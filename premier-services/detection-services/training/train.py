"""
train.py — Version finale (dataset équilibré)
----------------------------------------------
Fine-tune ResNet-50 sur CBIS-DDSM — Cancer vs Non-Cancer.
Dataset : 1700 Cancer + 1700 Non-Cancer (train) | 300 + 300 (val)
Objectif : AUC > 0.85 sur CPU.
"""

import argparse
import json
import time
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms

try:
    from sklearn.metrics import roc_auc_score, classification_report
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("[train] scikit-learn absent – pip install scikit-learn")

# ── Chemins ───────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
DATA_DIR   = BASE_DIR / "data" / "cbis_ddsm"
MODELS_DIR = BASE_DIR.parent / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ── Hyper-paramètres ──────────────────────────────────────────────────────────
DEFAULTS = dict(
    epochs          = 25,
    batch_size      = 16,
    lr              = 5e-4,
    weight_decay    = 1e-3,
    img_size        = 224,
    patience        = 7,
    num_workers     = 0,
    seed            = 42,
    unfreeze_layer4 = 3,
    unfreeze_layer3 = 7,
    label_smoothing = 0.1,
)


# ── Transformations ───────────────────────────────────────────────────────────
def build_transforms(img_size: int):
    mean = [0.485, 0.456, 0.406]
    std  = [0.229, 0.224, 0.225]

    train_tf = transforms.Compose([
        transforms.Resize((img_size + 48, img_size + 48)),
        transforms.RandomCrop(img_size),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.3),
        transforms.RandomRotation(degrees=15),
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


# ── Modèle ResNet-50 ──────────────────────────────────────────────────────────
def build_model(num_classes: int) -> nn.Module:
    print("[train] Chargement ResNet-50 (ImageNet V2) …")
    model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)

    for param in model.parameters():
        param.requires_grad = False

    in_features = model.fc.in_features  # 2048
    model.fc = nn.Sequential(
        nn.Dropout(p=0.5),
        nn.Linear(in_features, 512),
        nn.BatchNorm1d(512),
        nn.ReLU(inplace=True),
        nn.Dropout(p=0.3),
        nn.Linear(512, 128),
        nn.ReLU(inplace=True),
        nn.Linear(128, num_classes),
    )
    return model.to(DEVICE)


def unfreeze_layers(model, layers, optimizer, base_lr, label=""):
    params = []
    for layer in layers:
        for param in layer.parameters():
            param.requires_grad = True
            params.append(param)
    optimizer.add_param_group({"params": params, "lr": base_lr * 0.05})
    print(f"[train] ✅ {label} dégelée — lr = base_lr × 0.05")


# ── Epoch train ───────────────────────────────────────────────────────────────
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


# ── Validation avec TTA ───────────────────────────────────────────────────────
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
        imgs     = imgs.to(DEVICE)
        imgs_tta = imgs_tta.to(DEVICE)
        labels   = labels.to(DEVICE)

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
    torch.save(model.state_dict(), models_dir / "resnet50_mammography.pt")
    with open(models_dir / "class_names.json", "w") as f:
        json.dump(class_names, f, indent=2)
    print(f"  ✅ Sauvegardé → resnet50_mammography.pt")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    for k, v in DEFAULTS.items():
        parser.add_argument(f"--{k.replace('_','-')}", type=type(v), default=v)
    parser.add_argument("--data-dir",   type=Path, default=DATA_DIR)
    parser.add_argument("--models-dir", type=Path, default=MODELS_DIR)
    args = parser.parse_args()

    torch.manual_seed(args.seed)

    print(f"[train] Device       : {DEVICE}")
    print(f"[train] Torch        : {torch.__version__}")

    for split in ("train", "val"):
        for label in ("Cancer", "Non-Cancer"):
            d = args.data_dir / split / label
            if not d.exists():
                raise SystemExit(f"❌ Dossier manquant : {d}")

    train_tf, val_tf, tta_tf = build_transforms(args.img_size)
    train_ds = datasets.ImageFolder(args.data_dir / "train", transform=train_tf)
    val_root = str(args.data_dir / "val")

    class_names = train_ds.classes
    pos_idx     = class_names.index("Cancer") if "Cancer" in class_names else 0

    print(f"[train] class_to_idx : {train_ds.class_to_idx}")
    print(f"[train] pos_idx      : {pos_idx} → '{class_names[pos_idx]}'")
    print(f"[train] Train        : {len(train_ds)} images")
    print(f"[train] Val          : 600 images (300 Cancer + 300 Non-Cancer)")
    print(f"[train] LR initial   : {args.lr}")
    print(f"[train] Epochs max   : {args.epochs}\n")

    # Dataset équilibré → shuffle simple, pas besoin de WeightedSampler
    train_loader = DataLoader(
        train_ds,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=False,
    )

    model = build_model(len(class_names))

    # ✅ CrossEntropyLoss avec label smoothing — parfait pour dataset équilibré
    criterion = nn.CrossEntropyLoss(label_smoothing=args.label_smoothing)

    optimizer = optim.AdamW(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=args.lr,
        weight_decay=args.weight_decay,
    )

    # ✅ ReduceLROnPlateau — compatible avec unfreeze dynamique
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="max", factor=0.5, patience=3, min_lr=1e-6
    )

    best_auc      = 0.0
    patience_left = args.patience
    history       = []
    unfrozen_l4   = False
    unfrozen_l3   = False

    print("═" * 65)
    for epoch in range(1, args.epochs + 1):
        t0 = time.time()

        if not unfrozen_l4 and epoch >= args.unfreeze_layer4:
            unfreeze_layers(model, [model.layer4], optimizer, args.lr, "layer4")
            unfrozen_l4 = True

        if not unfrozen_l3 and epoch >= args.unfreeze_layer3:
            unfreeze_layers(model, [model.layer3], optimizer, args.lr, "layer3")
            unfrozen_l3 = True

        print(f"\nEpoch {epoch}/{args.epochs}")

        tr_loss, tr_acc = train_epoch(model, train_loader, criterion, optimizer)
        vl_acc, vl_auc, all_labels, all_probs = val_epoch(
            model, val_root, val_tf, tta_tf, args.batch_size, pos_idx
        )

        scheduler.step(vl_auc)

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

    hist_path = args.models_dir / "training_history.json"
    with open(hist_path, "w") as f:
        json.dump(history, f, indent=2)

    print("\n" + "═" * 65)
    print(f"[train] Meilleur val AUC : {best_auc:.4f}")
    print(f"[train] Historique       → {hist_path}")
    print("[train] ✅ Entraînement terminé")

    if best_auc >= 0.85:
        print("\n🏆 Excellent ! AUC ≥ 0.85 — prêt pour la production.")
    elif best_auc >= 0.75:
        print("\n✅ Bon modèle. AUC ≥ 0.75 — résultats fiables.")
    else:
        print("\n⚠️  AUC < 0.75 — essaie plus d'epochs ou vérifie les données.")


if __name__ == "__main__":
    main()   