"""
train.py — ResNet50 Fine-tuning pour CBIS-DDSM
Breast Cancer Detection : Cancer vs Non-Cancer

Architecture ResNet50 :
    Conv1 (7x7, 64, stride=2)
    MaxPool (3x3, stride=2)
    Layer1 : 3 x Bottleneck (64 -> 256)
    Layer2 : 4 x Bottleneck (128 -> 512)
    Layer3 : 6 x Bottleneck (256 -> 1024)
    Layer4 : 3 x Bottleneck (512 -> 2048)
    AdaptiveAvgPool
    FC (2048 -> 2)  ← remplace la couche originale (1000 classes)

Strategie fine-tuning en 3 phases :
    Phase 1 : entraîner seulement FC            (5 epochs)
    Phase 2 : dégeler layer4 + FC               (10 epochs)
    Phase 3 : dégeler tout le réseau            (15 epochs)
"""

import os
import time
import copy
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.models as models
import torchvision.transforms as transforms
from torch.utils.data import DataLoader
from torchvision.datasets import ImageFolder
from torch.optim.lr_scheduler import CosineAnnealingLR
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ══════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════

DATA_DIR    = "data"
OUTPUT_DIR  = "output"
BATCH_SIZE  = 32
NUM_WORKERS = 0
DEVICE      = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Phases d'entraînement
PHASES = [
    {"name": "phase1_fc_only",   "epochs": 5,  "lr": 1e-3, "unfreeze": "fc"},
    {"name": "phase2_layer4_fc", "epochs": 10, "lr": 5e-4, "unfreeze": "layer4"},
    {"name": "phase3_full",      "epochs": 15, "lr": 1e-4, "unfreeze": "all"},
]

os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"Device : {DEVICE}")
if torch.cuda.is_available():
    print(f"GPU    : {torch.cuda.get_device_name(0)}")

# ══════════════════════════════════════════════════════════
# TRANSFORMS
# ══════════════════════════════════════════════════════════

train_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomVerticalFlip(p=0.3),
    transforms.RandomRotation(degrees=15),
    transforms.ColorJitter(brightness=0.2, contrast=0.2),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    ),
])

val_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    ),
])


if __name__ == "__main__":
    # ══════════════════════════════════════════════════════
    # DATASETS & DATALOADERS
    # ══════════════════════════════════════════════════════

    # ══════════════════════════════════════════════════════════

    train_dataset = ImageFolder(
        root=os.path.join(DATA_DIR, "train"),
        transform=train_transform
    )
    val_dataset = ImageFolder(
        root=os.path.join(DATA_DIR, "val"),
        transform=val_transform
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=0,
        pin_memory=False
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=0,
        pin_memory=False
    )

    print(f"\nClasses       : {train_dataset.classes}")
    print(f"Train samples : {len(train_dataset)}")
    print(f"Val   samples : {len(val_dataset)}")

    # ══════════════════════════════════════════════════════════
    # MODELE RESNET50
    # ══════════════════════════════════════════════════════════

    def build_model():
        """
        Charge ResNet50 pré-entraîné ImageNet et remplace la couche FC.

        Architecture ResNet50 complète :
        ┌─────────────────────────────────────────┐
        │  Input : (B, 3, 224, 224)               │
        │  conv1  : 7x7, 64 filtres, stride=2     │
        │  bn1 + relu + maxpool                   │
        ├─────────────────────────────────────────┤
        │  layer1 : 3 x Bottleneck  →  (B,  256, 56, 56)  │
        │  layer2 : 4 x Bottleneck  →  (B,  512, 28, 28)  │
        │  layer3 : 6 x Bottleneck  →  (B, 1024, 14, 14)  │
        │  layer4 : 3 x Bottleneck  →  (B, 2048,  7,  7)  │
        ├─────────────────────────────────────────┤
        │  AdaptiveAvgPool2d(1,1)   →  (B, 2048,  1,  1)  │
        │  Flatten                  →  (B, 2048)           │
        │  FC : 2048 → 2  (Cancer / Non-Cancer)            │
        └─────────────────────────────────────────┘
        """
        model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)

        # Remplacer la dernière couche FC
        # Original : Linear(2048, 1000)  → ImageNet 1000 classes
        # Nouveau  : Linear(2048, 2)     → Cancer / Non-Cancer
        in_features = model.fc.in_features   # 2048
        model.fc = nn.Sequential(
            nn.Dropout(p=0.4),
            nn.Linear(in_features, 2)
        )

        return model


    def freeze_all(model):
        for param in model.parameters():
            param.requires_grad = False


    def unfreeze_layer(model, layer_name):
        """Dégèle une couche spécifique ou tout le réseau."""
        if layer_name == "fc":
            for param in model.fc.parameters():
                param.requires_grad = True

        elif layer_name == "layer4":
            for param in model.layer4.parameters():
                param.requires_grad = True
            for param in model.fc.parameters():
                param.requires_grad = True

        elif layer_name == "all":
            for param in model.parameters():
                param.requires_grad = True


    def count_trainable(model):
        return sum(p.numel() for p in model.parameters() if p.requires_grad)


    model = build_model()
    model = model.to(DEVICE)

    print(f"\nModele ResNet50 charge")
    print(f"  Parametres totaux     : {sum(p.numel() for p in model.parameters()):,}")

    # ══════════════════════════════════════════════════════════
    # CLASS WEIGHTS  (compenser le sur-echantillonnage Cancer)
    # ══════════════════════════════════════════════════════════

    # Cancer = 1457 images reelles / Non-Cancer = 2111
    # On pondère inversement pour ne pas biaiser
    class_counts = torch.tensor([1700.0, 1700.0])   # equilibré dans notre dataset
    class_weights = 1.0 / class_counts
    class_weights = class_weights / class_weights.sum()
    class_weights = class_weights.to(DEVICE)

    criterion = nn.CrossEntropyLoss(weight=class_weights)

    # ══════════════════════════════════════════════════════════
    # FONCTIONS TRAIN / EVAL
    # ══════════════════════════════════════════════════════════

    def train_one_epoch(model, loader, optimizer, criterion):
        model.train()
        total_loss = 0.0
        correct    = 0
        total      = 0

        for images, labels in loader:
            images = images.to(DEVICE, non_blocking=True)
            labels = labels.to(DEVICE, non_blocking=True)

            optimizer.zero_grad()
            outputs = model(images)
            loss    = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * images.size(0)
            preds       = outputs.argmax(dim=1)
            correct    += (preds == labels).sum().item()
            total      += images.size(0)

        return total_loss / total, correct / total


    def evaluate(model, loader, criterion):
        model.eval()
        total_loss = 0.0
        correct    = 0
        total      = 0

        # Pour les métriques par classe
        tp = {0: 0, 1: 0}
        fp = {0: 0, 1: 0}
        fn = {0: 0, 1: 0}

        with torch.no_grad():
            for images, labels in loader:
                images = images.to(DEVICE, non_blocking=True)
                labels = labels.to(DEVICE, non_blocking=True)

                outputs = model(images)
                loss    = criterion(outputs, labels)
                preds   = outputs.argmax(dim=1)

                total_loss += loss.item() * images.size(0)
                correct    += (preds == labels).sum().item()
                total      += images.size(0)

                for c in [0, 1]:
                    tp[c] += ((preds == c) & (labels == c)).sum().item()
                    fp[c] += ((preds == c) & (labels != c)).sum().item()
                    fn[c] += ((preds != c) & (labels == c)).sum().item()

        # Precision / Recall / F1 par classe
        metrics = {}
        for c in [0, 1]:
            prec   = tp[c] / (tp[c] + fp[c] + 1e-8)
            recall = tp[c] / (tp[c] + fn[c] + 1e-8)
            f1     = 2 * prec * recall / (prec + recall + 1e-8)
            metrics[c] = {"precision": prec, "recall": recall, "f1": f1}

        return total_loss / total, correct / total, metrics


    # ══════════════════════════════════════════════════════════
    # BOUCLE D'ENTRAINEMENT  (3 phases)
    # ══════════════════════════════════════════════════════════

    history = {
        "train_loss": [], "train_acc": [],
        "val_loss":   [], "val_acc":   [],
    }

    best_val_acc  = 0.0
    best_model_wt = copy.deepcopy(model.state_dict())
    global_epoch  = 0

    print("\n" + "="*60)
    print("  DEBUT ENTRAINEMENT ResNet50 — Fine-tuning 3 phases")
    print("="*60)

    for phase in PHASES:
        print(f"\n{'─'*60}")
        print(f"  {phase['name'].upper()}")
        print(f"  Unfreeze : {phase['unfreeze']}  |  LR : {phase['lr']}  |  Epochs : {phase['epochs']}")
        print(f"{'─'*60}")

        # Geler tout, puis dégeler la partie voulue
        freeze_all(model)
        unfreeze_layer(model, phase["unfreeze"])

        print(f"  Parametres entrainables : {count_trainable(model):,}")

        # Optimizer sur les seuls paramètres dégelés
        optimizer = optim.AdamW(
            filter(lambda p: p.requires_grad, model.parameters()),
            lr=phase["lr"],
            weight_decay=1e-4
        )
        scheduler = CosineAnnealingLR(optimizer, T_max=phase["epochs"])

        for epoch in range(1, phase["epochs"] + 1):
            global_epoch += 1
            t0 = time.time()

            train_loss, train_acc = train_one_epoch(model, train_loader, optimizer, criterion)
            val_loss,   val_acc, metrics = evaluate(model, val_loader, criterion)
            scheduler.step()

            elapsed = time.time() - t0

            history["train_loss"].append(train_loss)
            history["train_acc"].append(train_acc)
            history["val_loss"].append(val_loss)
            history["val_acc"].append(val_acc)

            # Sauvegarder le meilleur modèle
            if val_acc > best_val_acc:
                best_val_acc  = val_acc
                best_model_wt = copy.deepcopy(model.state_dict())
                torch.save(best_model_wt, os.path.join(OUTPUT_DIR, "best_model.pth"))
                saved = " ← BEST"
            else:
                saved = ""

            # Classes : 0=Cancer, 1=Non-Cancer (ordre alphabétique ImageFolder)
            cls_names = train_dataset.classes
            print(
                f"  Ep {global_epoch:02d}/{sum(p['epochs'] for p in PHASES)} "
                f"[{elapsed:.0f}s] "
                f"| Train  loss={train_loss:.4f}  acc={train_acc*100:.1f}% "
                f"| Val  loss={val_loss:.4f}  acc={val_acc*100:.1f}% "
                f"| F1 {cls_names[0]}={metrics[0]['f1']:.3f}  {cls_names[1]}={metrics[1]['f1']:.3f}"
                f"{saved}"
            )

    # ══════════════════════════════════════════════════════════
    # CHARGER MEILLEUR MODELE + EVALUATION FINALE
    # ══════════════════════════════════════════════════════════

    model.load_state_dict(best_model_wt)
    _, final_acc, final_metrics = evaluate(model, val_loader, criterion)

    cls_names = train_dataset.classes

    print("\n" + "="*60)
    print("  RESULTATS FINAUX")
    print("="*60)
    print(f"  Meilleure Val Accuracy : {best_val_acc*100:.2f}%")
    print(f"  Val Accuracy finale    : {final_acc*100:.2f}%")
    print()
    for c, name in enumerate(cls_names):
        m = final_metrics[c]
        print(f"  [{name}]")
        print(f"    Precision : {m['precision']*100:.1f}%")
        print(f"    Recall    : {m['recall']*100:.1f}%")
        print(f"    F1-Score  : {m['f1']*100:.1f}%")
    print("="*60)

    # Sauvegarder modèle final
    torch.save(model.state_dict(), os.path.join(OUTPUT_DIR, "final_model.pth"))
    print(f"\nModeles sauvegardes dans : {os.path.abspath(OUTPUT_DIR)}/")
    print(f"  best_model.pth   (meilleure val accuracy)")
    print(f"  final_model.pth  (dernier epoch)")

    # ══════════════════════════════════════════════════════════
    # COURBES D'APPRENTISSAGE
    # ══════════════════════════════════════════════════════════

    epochs_range = range(1, global_epoch + 1)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.plot(epochs_range, [l for l in history["train_loss"]], label="Train Loss", color="steelblue")
    ax1.plot(epochs_range, [l for l in history["val_loss"]],   label="Val Loss",   color="tomato")
    ax1.set_title("Loss")
    ax1.set_xlabel("Epoch")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2.plot(epochs_range, [a*100 for a in history["train_acc"]], label="Train Acc", color="steelblue")
    ax2.plot(epochs_range, [a*100 for a in history["val_acc"]],   label="Val Acc",   color="tomato")
    ax2.axhline(y=best_val_acc*100, color="green", linestyle="--", label=f"Best={best_val_acc*100:.1f}%")
    ax2.set_title("Accuracy (%)")
    ax2.set_xlabel("Epoch")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.suptitle("ResNet50 — CBIS-DDSM Breast Cancer", fontsize=13)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "training_curves.png"), dpi=150)
    print(f"  training_curves.png")