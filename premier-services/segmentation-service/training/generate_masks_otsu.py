"""
generate_masks_otsu.py
-----------------------
Génère des masques de segmentation depuis les paires image/masque CBIS-DDSM.

Approche : masque rectangulaire centré sur la zone ROI croppée.
Le masque blanc = zone tumorale approximative (ROI rectangle).
"""

from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np
from tqdm import tqdm

DATA_DIR = Path("data/segmentation")
IMG_SIZE = 224


def generate_roi_mask(image_path: Path, mask_path: Path) -> None:
    """
    Stratégie :
    1. Charge l'image croppée (ROI)
    2. Détecte la zone non-noire (tissu mammaire)
    3. Crée un masque blanc sur cette zone
    """
    image   = Image.open(image_path).convert("L")
    img_np  = np.array(image)

    # Détecte la zone non-noire (seuil bas = 15)
    non_black = (img_np > 15).astype(np.uint8)

    # Si pas assez de contenu → masque centré 50%
    if non_black.sum() < IMG_SIZE * IMG_SIZE * 0.1:
        mask_np = np.zeros((IMG_SIZE, IMG_SIZE), dtype=np.uint8)
        # Rectangle central 50%
        m = IMG_SIZE // 4
        mask_np[m:IMG_SIZE-m, m:IMG_SIZE-m] = 255
    else:
        # Bounding box de la zone non-noire
        rows    = np.any(non_black, axis=1)
        cols    = np.any(non_black, axis=0)
        rmin, rmax = np.where(rows)[0][[0, -1]]
        cmin, cmax = np.where(cols)[0][[0, -1]]

        # Masque blanc sur la bounding box
        mask_np = np.zeros((IMG_SIZE, IMG_SIZE), dtype=np.uint8)
        mask_np[rmin:rmax, cmin:cmax] = 255

    Image.fromarray(mask_np, mode="L").save(mask_path)


def main():
    total = 0
    for split in ["train", "val"]:
        img_dir  = DATA_DIR / split / "images"
        mask_dir = DATA_DIR / split / "masks"
        images   = sorted(img_dir.glob("*.jpg"))

        print(f"\n[mask] {split} : {len(images)} images")

        for img_path in tqdm(images, desc=split):
            mask_path = mask_dir / img_path.with_suffix(".png").name
            try:
                generate_roi_mask(img_path, mask_path)
                total += 1
            except Exception as e:
                print(f"  ⚠️ {img_path.name} : {e}")

    print(f"\n✅ {total} masques générés")

    # Vérification
    masks = list((DATA_DIR / "train" / "masks").glob("*.png"))[:10]
    pcts  = [(np.array(Image.open(m)) > 127).mean() * 100 for m in masks]
    print(f"\n[verify] Moyenne pixels blancs : {np.mean(pcts):.1f}%")
    print(f"[verify] Min: {np.min(pcts):.1f}%  Max: {np.max(pcts):.1f}%")

    if np.mean(pcts) < 60:
        print("[verify] ✅ Masques générés !")
    else:
        print("[verify] ⚠️ Vérifie visuellement")


if __name__ == "__main__":
    main()