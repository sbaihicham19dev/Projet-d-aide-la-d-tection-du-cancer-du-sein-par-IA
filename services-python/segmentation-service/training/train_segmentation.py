"""
train_segmentation.py
----------------------
Entraîne U-Net sur CBIS-DDSM pour segmentation tumorale.
Entrée  : image mammographie 224×224
Sortie  : masque binaire 224×224

Sorties
-------
    ../models/unet_224.pt
    ../models/training_history_segmentation.json
"""

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image

# ── Chemins ───────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
DATA_DIR   = BASE_DIR / "data" / "segmentation"
MODELS_DIR = BASE_DIR.parent / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

DEFAULTS = dict(
    epochs      = 20,
    batch_size  = 8,
    lr          = 1e-3,
    img_size    = 224,
    patience    = 6,
    num_workers = 0,
    seed        = 42,
)


# ── Dataset ───────────────────────────────────────────────────────────────────
class SegmentationDataset(Dataset):
    def __init__(self, data_dir: Path, split: str, img_size: int):
        self.img_dir  = data_dir / split / "images"
        self.msk_dir  = data_dir / split / "masks"
        self.img_size = img_size
        self.files    = sorted(self.img_dir.glob("*.jpg"))

        self.img_tf = transforms.Compose([
            transforms.Resize((img_size, img_size)),
            transforms.Grayscale(num_output_channels=1),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5], std=[0.5]),
        ])
        self.msk_tf = transforms.Compose([
            transforms.Resize((img_size, img_size), interpolation=transforms.InterpolationMode.NEAREST),
            transforms.ToTensor(),
        ])

    def __len__(self):
        return len(self.files)

    def __getitem__(self, idx):
        img_path = self.files[idx]
        msk_path = self.msk_dir / img_path.with_suffix(".png").name

        image = Image.open(img_path).convert("RGB")
        mask  = Image.open(msk_path).convert("L") if msk_path.exists() \
                else Image.new("L", (self.img_size, self.img_size), 0)

        image = self.img_tf(image)
        mask  = self.msk_tf(mask)
        mask  = (mask > 0.5).float()

        return image, mask


# ── U-Net ─────────────────────────────────────────────────────────────────────
class DoubleConv(nn.Module):
    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.net(x)


class UNet(nn.Module):
    def __init__(self, in_channels=1, out_channels=1, features=[64, 128, 256, 512]):
        super().__init__()
        self.downs      = nn.ModuleList()
        self.ups        = nn.ModuleList()
        self.pool       = nn.MaxPool2d(2, 2)

        for f in features:
            self.downs.append(DoubleConv(in_channels, f))
            in_channels = f

        self.bottleneck = DoubleConv(features[-1], features[-1] * 2)

        for f in reversed(features):
            self.ups.append(nn.ConvTranspose2d(f * 2, f, 2, 2))
            self.ups.append(DoubleConv(f * 2, f))

        self.final = nn.Conv2d(features[0], out_channels, 1)

    def forward(self, x):
        skips = []
        for down in self.downs:
            x = down(x)
            skips.append(x)
            x = self.pool(x)

        x     = self.bottleneck(x)
        skips = skips[::-1]

        for i in range(0, len(self.ups), 2):
            x    = self.ups[i](x)
            skip = skips[i // 2]
            if x.shape != skip.shape:
                x = nn.functional.interpolate(x, size=skip.shape[2:])
            x = torch.cat([skip, x], dim=1)
            x = self.ups[i + 1](x)

        return self.final(x)


# ── Dice Loss ─────────────────────────────────────────────────────────────────
class DiceBCELoss(nn.Module):
    def __init__(self):
        super().__init__()
        self.bce = nn.BCEWithLogitsLoss()

    def forward(self, pred, target):
        bce_loss  = self.bce(pred, target)
        pred_sig  = torch.sigmoid(pred)
        smooth    = 1e-6
        inter     = (pred_sig * target).sum(dim=(2, 3))
        dice_loss = 1 - (2 * inter + smooth) / (
            pred_sig.sum(dim=(2, 3)) + target.sum(dim=(2, 3)) + smooth
        )
        return bce_loss + dice_loss.mean()


# ── Métriques ─────────────────────────────────────────────────────────────────
def dice_score(pred, target, threshold=0.5):
    pred   = (torch.sigmoid(pred) > threshold).float()
    smooth = 1e-6
    inter  = (pred * target).sum()
    return ((2 * inter + smooth) / (pred.sum() + target.sum() + smooth)).item()


# ── Train epoch ───────────────────────────────────────────────────────────────
def train_epoch(model, loader, criterion, optimizer):
    model.train()
    total_loss = total_dice = 0

    for batch_idx, (imgs, masks) in enumerate(loader):
        imgs, masks = imgs.to(DEVICE), masks.to(DEVICE)
        optimizer.zero_grad()
        preds = model(imgs)
        loss  = criterion(preds, masks)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

        total_loss += loss.item()
        total_dice += dice_score(preds, masks)

        if (batch_idx + 1) % 20 == 0:
            print(
                f"    batch {batch_idx+1}/{len(loader)}  "
                f"loss={total_loss/(batch_idx+1):.4f}  "
                f"dice={total_dice/(batch_idx+1):.3f}",
                end="\r",
            )

    print()
    n = len(loader)
    return total_loss / n, total_dice / n


# ── Val epoch ─────────────────────────────────────────────────────────────────
@torch.no_grad()
def val_epoch(model, loader, criterion):
    model.eval()
    total_loss = total_dice = 0

    for imgs, masks in loader:
        imgs, masks = imgs.to(DEVICE), masks.to(DEVICE)
        preds       = model(imgs)
        total_loss += criterion(preds, masks).item()
        total_dice += dice_score(preds, masks)

    n = len(loader)
    return total_loss / n, total_dice / n


# ── Sauvegarde ────────────────────────────────────────────────────────────────
def save_checkpoint(model, models_dir):
    torch.save(model.state_dict(), models_dir / "unet_224.pt")
    print(f"  ✅ Sauvegardé → unet_224.pt")


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
        for sub in ("images", "masks"):
            d = args.data_dir / split / sub
            if not d.exists():
                raise SystemExit(
                    f"❌ Dossier manquant : {d}\n"
                    f"   Lance d'abord : python prepare_data_segmentation.py"
                )

    train_ds = SegmentationDataset(args.data_dir, "train", args.img_size)
    val_ds   = SegmentationDataset(args.data_dir, "val",   args.img_size)

    print(f"[train] Train : {len(train_ds)} paires")
    print(f"[train] Val   : {len(val_ds)} paires")
    print(f"[train] Epochs: {args.epochs}\n")

    train_loader = DataLoader(
        train_ds, batch_size=args.batch_size,
        shuffle=True, num_workers=args.num_workers, pin_memory=False,
    )
    val_loader = DataLoader(
        val_ds, batch_size=args.batch_size,
        shuffle=False, num_workers=args.num_workers, pin_memory=False,
    )

    model     = UNet(in_channels=1, out_channels=1).to(DEVICE)
    criterion = DiceBCELoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="max", factor=0.5, patience=3, min_lr=1e-6
    )

    best_dice     = 0.0
    patience_left = args.patience
    history       = []

    print("═" * 60)
    for epoch in range(1, args.epochs + 1):
        t0 = time.time()

        print(f"\nEpoch {epoch}/{args.epochs}")
        tr_loss, tr_dice = train_epoch(model, train_loader, criterion, optimizer)
        vl_loss, vl_dice = val_epoch(model, val_loader, criterion)
        scheduler.step(vl_dice)

        elapsed = time.time() - t0
        flag    = " ◀ BEST" if vl_dice > best_dice else ""
        print(
            f"  train  loss={tr_loss:.4f}  dice={tr_dice:.3f}\n"
            f"  val    loss={vl_loss:.4f}  dice={vl_dice:.3f}  "
            f"[{elapsed/60:.1f} min]{flag}"
        )

        history.append(dict(
            epoch=epoch,
            train_loss=round(tr_loss, 4), train_dice=round(tr_dice, 4),
            val_loss=round(vl_loss, 4),   val_dice=round(vl_dice, 4),
            elapsed_min=round(elapsed / 60, 2),
        ))

        if vl_dice > best_dice:
            best_dice     = vl_dice
            patience_left = args.patience
            save_checkpoint(model, args.models_dir)
        else:
            patience_left -= 1
            print(f"  Patience restante : {patience_left}/{args.patience}")
            if patience_left == 0:
                print(f"\n[train] Early stopping à l'epoch {epoch}.")
                break

    hist_path = args.models_dir / "training_history_segmentation.json"
    with open(hist_path, "w") as f:
        json.dump(history, f, indent=2)

    print("\n" + "═" * 60)
    print(f"[train] Meilleur Dice : {best_dice:.4f}")
    print("[train] ✅ Entraînement terminé")

    if best_dice >= 0.70:
        print("\n🏆 Excellent ! Dice ≥ 0.70 — segmentation fiable.")
    elif best_dice >= 0.50:
        print("\n✅ Bon modèle. Dice ≥ 0.50 — segmentation acceptable.")
    else:
        print("\n⚠️  Dice < 0.50 — essaie plus d'epochs.")


if __name__ == "__main__":
    main()