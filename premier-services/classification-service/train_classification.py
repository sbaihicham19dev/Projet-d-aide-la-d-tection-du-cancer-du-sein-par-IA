"""
train_classification.py
------------------------
Fine-tune EfficientNet-B4 sur CBIS-DDSM — Benign vs Malignant.
Optimisé CPU. Objectif : AUC > 0.82

Sorties
-------
    ../models/efficientnet_b4.pt
    ../models/class_names.json
    ../models/training_history_classification.json
"""

import argparse
import json
import time
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, WeightedRandomSampler
from torchvision import datasets, models, transforms

try:
    from sklearn.metrics import roc_auc_score, classification_report
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("[train] pip install scikit-learn")

# ── Chemins ───────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
DATA_DIR   = BASE_DIR / "data" / "cbis_ddsm_classification"
MODELS_DIR = BASE_DIR.parent / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

DEFAULTS = dict(
    epochs          = 60,      # était 25 → le modèle n'avait pas convergé
    batch_size      = 16,
    lr              = 1e-4,    # était 5e-4 → trop élevé pour EfficientNet pré-entraîné
    weight_decay    = 1e-4,    # était 1e-3 → trop fort, empêche la convergence
    img_size        = 380,
    patience        = 10,      # était 7 → plus de tolérance
    num_workers     = 0,
    seed            = 42,
    unfreeze_epoch  = 5,
    label_smoothing = 0.05,    # était 0.1 → trop fort pour dataset petit
)


# ── Transforms ────────────────────────────────────────────────────────────────
def build_transforms(img_size: int):
    mean = [0.485, 0.456, 0.406]
    std  = [0.229, 0.224, 0.225]

    train_tf = transforms.Compose([
        transforms.Resize((img_size + 32, img_size + 32)),
        transforms.RandomCrop(img_size),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.3),
        transforms.RandomRotation(15),
        transforms.RandomAffine(degrees=0, translate=(0.1, 0.1), scale=(0.9, 1.1)),
        transforms.ColorJitter(brightness=0.3, contrast=0.4),
        transforms.RandomAutocontrast(p=0.3),
        transforms.Grayscale(num_output_channels=3),
        transforms.ToTensor(),
        transforms.Normalize(mean, std),
        transforms.RandomErasing(p=0.2, scale=(0.02, 0.1)),
    ])

    val_tf = transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.Grayscale(num_output_channels=3),
        transforms.ToTensor(),
        transforms.Normalize(mean, std),
    ])

    tta_tf = transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.RandomHorizontalFlip(p=1.0),
        transforms.Grayscale(num_output_channels=3),
        transforms.ToTensor(),
        transforms.Normalize(mean, std),
    ])

    return train_tf, val_tf, tta_tf


# ── Modèle EfficientNet-B4 ────────────────────────────────────────────────────
def build_model(num_classes: int) -> nn.Module:
    print("[train] Chargement EfficientNet-B4 (ImageNet) …")
    model       = models.efficientnet_b4(weights=models.EfficientNet_B4_Weights.DEFAULT)
    in_features = model.classifier[1].in_features  # 1792

    for param in model.parameters():
        param.requires_grad = False

    model.classifier = nn.Sequential(
        nn.Dropout(p=0.4),
        nn.Linear(in_features, 256),
        nn.ReLU(inplace=True),
        nn.Dropout(p=0.2),
        nn.Linear(256, num_classes),
    )
    return model.to(DEVICE)


def unfreeze_top_blocks(model, optimizer, base_lr):
    """Dégèle les derniers blocs de EfficientNet."""
    for block in list(model.features.children())[-3:]:
        for param in block.parameters():
            param.requires_grad = True
    params = [p for p in model.features.parameters() if p.requires_grad]
    optimizer.add_param_group({"params": params, "lr": base_lr * 0.05})
    print("[train] ✅ Derniers blocs dégelés — lr = base_lr × 0.05")


# ── Weighted sampler pour gérer le déséquilibre ───────────────────────────────
def build_weighted_sampler(dataset) -> WeightedRandomSampler:
    """Rééquilibre les classes en sur-échantillonnant la classe minoritaire."""
    class_counts = [0] * len(dataset.classes)
    for _, label in dataset.samples:
        class_counts[label] += 1

    print(f"[train] Distribution des classes : ", end="")
    for i, (name, count) in enumerate(zip(dataset.classes, class_counts)):
        print(f"{name}={count}", end="  ")
    print()

    # Poids inversement proportionnels aux effectifs
    class_weights = [1.0 / max(c, 1) for c in class_counts]
    sample_weights = [class_weights[label] for _, label in dataset.samples]

    return WeightedRandomSampler(
        weights=sample_weights,
        num_samples=len(sample_weights),
        replacement=True,
    )


# ── Train epoch ───────────────────────────────────────────────────────────────
def train_epoch(model, loader, criterion, optimizer):
    model.train()
    total_loss = correct = total = 0

    for batch_idx, (imgs, labels) in enumerate(loader):
        imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)
        optimizer.zero_grad()
        out  = model(imgs)
        loss = criterion(out, labels)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

        total_loss += loss.item() * imgs.size(0)
        correct    += (out.argmax(1) == labels).sum().item()
        total      += imgs.size(0)

        if (batch_idx + 1) % 20 == 0:
            print(
                f"    batch {batch_idx+1}/{len(loader)}  "
                f"loss={total_loss/total:.4f}  acc={correct/total:.3f}",
                end="\r",
            )

    print()
    return total_loss / total, correct / total


# ── Val epoch avec TTA ────────────────────────────────────────────────────────
@torch.no_grad()
def val_epoch(model, val_root, val_tf, tta_tf, batch_size, pos_idx):
    model.eval()
    correct = total = 0
    all_probs, all_labels = [], []

    val_ds  = datasets.ImageFolder(val_root, transform=val_tf)
    tta_ds  = datasets.ImageFolder(val_root, transform=tta_tf)
    loader  = DataLoader(val_ds,  batch_size=batch_size, shuffle=False, num_workers=0)
    tta_ldr = DataLoader(tta_ds,  batch_size=batch_size, shuffle=False, num_workers=0)

    for (imgs, labels), (imgs_tta, _) in zip(loader, tta_ldr):
        imgs, imgs_tta, labels = imgs.to(DEVICE), imgs_tta.to(DEVICE), labels.to(DEVICE)

        probs     = torch.softmax(model(imgs),     dim=1)
        probs_tta = torch.softmax(model(imgs_tta), dim=1)
        probs_avg = (probs + probs_tta) / 2.0

        correct += (probs_avg.argmax(1) == labels).sum().item()
        total   += imgs.size(0)
        all_probs.extend(probs_avg[:, pos_idx].tolist())
        all_labels.extend(labels.tolist())

    acc = correct / total
    if HAS_SKLEARN:
        auc = roc_auc_score(all_labels, all_probs)
        if auc < 0.5:
            auc = 1.0 - auc
    else:
        auc = float("nan")

    return acc, auc, all_labels, all_probs


# ── Sauvegarde ────────────────────────────────────────────────────────────────
def save_checkpoint(model, class_names, models_dir):
    torch.save(model.state_dict(), models_dir / "efficientnet_b4.pt")
    with open(models_dir / "class_names.json", "w") as f:
        json.dump(class_names, f, indent=2)
    print(f"  ✅ Sauvegardé → efficientnet_b4.pt")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    for k, v in DEFAULTS.items():
        parser.add_argument(f"--{k.replace('_','-')}", type=type(v), default=v)
    parser.add_argument("--data-dir",   type=Path, default=DATA_DIR)
    parser.add_argument("--models-dir", type=Path, default=MODELS_DIR)
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    print(f"[train] Device  : {DEVICE}")
    print(f"[train] Torch   : {torch.__version__}")

    for split in ("train", "val"):
        for label in ("Benign", "Malignant"):
            d = args.data_dir / split / label
            if not d.exists():
                raise SystemExit(
                    f"❌ Dossier manquant : {d}\n"
                    f"   Lance d'abord : python prepare_data_classification.py"
                )

    train_tf, val_tf, tta_tf = build_transforms(args.img_size)
    train_ds = datasets.ImageFolder(args.data_dir / "train", transform=train_tf)
    val_root = str(args.data_dir / "val")

    class_names = train_ds.classes
    pos_idx     = class_names.index("Malignant") if "Malignant" in class_names else 1

    print(f"[train] class_to_idx : {train_ds.class_to_idx}")
    print(f"[train] pos_idx      : {pos_idx} → '{class_names[pos_idx]}'")
    print(f"[train] Train        : {len(train_ds)} images")
    print(f"[train] Epochs max   : {args.epochs}\n")

    # ── WeightedRandomSampler pour rééquilibrer les classes ──────────────────
    sampler = build_weighted_sampler(train_ds)
    train_loader = DataLoader(
        train_ds,
        batch_size=args.batch_size,
        sampler=sampler,          # remplace shuffle=True
        num_workers=args.num_workers,
        pin_memory=False,
    )

    model     = build_model(len(class_names))
    criterion = nn.CrossEntropyLoss(label_smoothing=args.label_smoothing)
    optimizer = optim.AdamW(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=args.lr,
        weight_decay=args.weight_decay,
    )

    # CosineAnnealingLR — meilleure convergence que ReduceLROnPlateau
    scheduler = optim.lr_scheduler.CosineAnnealingLR(
        optimizer,
        T_max=args.epochs,
        eta_min=1e-6,
    )

    best_auc      = 0.0
    patience_left = args.patience
    history       = []
    unfrozen      = False

    print("═" * 65)
    for epoch in range(1, args.epochs + 1):
        t0 = time.time()

        if not unfrozen and epoch >= args.unfreeze_epoch:
            unfreeze_top_blocks(model, optimizer, args.lr)
            unfrozen = True

        print(f"\nEpoch {epoch}/{args.epochs}")
        tr_loss, tr_acc = train_epoch(model, train_loader, criterion, optimizer)
        vl_acc, vl_auc, all_labels, all_probs = val_epoch(
            model, val_root, val_tf, tta_tf, args.batch_size, pos_idx
        )
        scheduler.step()

        elapsed = time.time() - t0
        flag    = " ◀ BEST" if vl_auc > best_auc else ""
        print(
            f"  train  loss={tr_loss:.4f}  acc={tr_acc:.3f}\n"
            f"  val    acc={vl_acc:.3f}  auc={vl_auc:.3f}  "
            f"[{elapsed/60:.1f} min]{flag}"
        )

        if HAS_SKLEARN and epoch % 5 == 0:
            preds = [1 if p > 0.5 else 0 for p in all_probs]
            print("\n" + classification_report(all_labels, preds, target_names=class_names))

        history.append(dict(
            epoch=epoch,
            train_loss=round(tr_loss, 4), train_acc=round(tr_acc, 4),
            val_acc=round(vl_acc, 4),     val_auc=round(vl_auc, 4),
            elapsed_min=round(elapsed / 60, 2),
        ))

        # Sauvegarde du meilleur modèle
        if vl_auc > best_auc:
            best_auc      = vl_auc
            patience_left = args.patience
            save_checkpoint(model, list(class_names), args.models_dir)
        else:
            patience_left -= 1
            print(f"  Patience restante : {patience_left}/{args.patience}")
            if patience_left == 0:
                print(f"\n[train] Early stopping à l'epoch {epoch}.")
                break

        # Sauvegarde intermédiaire toutes les 10 epochs
        if epoch % 10 == 0:
            hist_path = args.models_dir / "training_history_classification.json"
            with open(hist_path, "w") as f:
                json.dump(history, f, indent=2)
            print(f"  💾 Historique sauvegardé à l'epoch {epoch}")

    hist_path = args.models_dir / "training_history_classification.json"
    with open(hist_path, "w") as f:
        json.dump(history, f, indent=2)

    print("\n" + "═" * 65)
    print(f"[train] Meilleur AUC : {best_auc:.4f}")
    print("[train] ✅ Entraînement terminé")

    if best_auc >= 0.82:
        print("\n🏆 Excellent ! AUC ≥ 0.82 — prêt pour la production.")
    elif best_auc >= 0.72:
        print("\n✅ Bon modèle. AUC ≥ 0.72 — résultats fiables.")
    else:
        print("\n⚠️  AUC < 0.72 — essaie plus d'epochs ou vérifie les données.")


if __name__ == "__main__":
    main()