"""
prepare_data_segmentation.py
-----------------------------
Prépare les paires image/masque depuis CBIS-DDSM pour entraîner U-Net.

Structure de sortie :
    training/data/segmentation/
        train/
            images/  image_00000.jpg ...
            masks/   image_00000.png ...
        val/
            images/
            masks/
"""

import csv
import random
import shutil
from pathlib import Path
from PIL import Image
import numpy as np
from tqdm import tqdm

# ── Config ────────────────────────────────────────────────────────────────────
MAX_PAIRS  = 2000
VAL_SPLIT  = 0.15
SEED       = 42
IMG_SIZE   = 224

RAW_DIR    = Path(r"C:\Users\hicha\Downloads\cbis-ddsm")
BASE_DIR   = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "data" / "segmentation"

CSV_FILES = [
    "mass_case_description_train_set.csv",
    "mass_case_description_test_set.csv",
]


# ── Résoudre chemin JPEG ──────────────────────────────────────────────────────
def resolve_folder(file_path: str, jpeg_root: Path):
    parts = file_path.strip().replace("\\", "/").split("/")
    if len(parts) < 2:
        return None
    uid    = parts[-2]
    folder = jpeg_root / uid
    return folder if folder.exists() else None


def get_image_and_mask(folder: Path):
    """
    Dans chaque dossier ROI :
    - Le fichier le plus GRAND  = image originale
    - Le fichier le plus PETIT  = masque ROI (zone tumorale en blanc)

    ✅ FIX : le masque est le petit fichier mais ses pixels blancs
    représentent la tumeur → on inverse pour avoir fond noir / tumeur blanche.
    """
    files     = sorted(folder.iterdir(), key=lambda f: f.stat().st_size)
    jpg_files = [f for f in files if f.suffix.lower() in {".jpg", ".jpeg", ".png"}]

    if len(jpg_files) < 2:
        return None, None

    # ✅ FIX: grand = image, petit = masque
    image_file = jpg_files[-1]  # plus grand = image mammographie
    mask_file  = jpg_files[0]   # plus petit = masque ROI

    return image_file, mask_file


# ── Collecte ──────────────────────────────────────────────────────────────────
def collect(raw_dir: Path) -> list:
    jpeg_root = raw_dir / "jpeg"
    csv_dir   = raw_dir / "csv"
    pairs     = []
    seen      = set()

    for csv_name in CSV_FILES:
        csv_path = csv_dir / csv_name
        if not csv_path.exists():
            print(f"[prepare] CSV absent : {csv_name}")
            continue

        print(f"[prepare] Lecture : {csv_name}")
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                roi_path = row.get("ROI mask file path", "").strip()
                if not roi_path:
                    continue

                folder = resolve_folder(roi_path, jpeg_root)
                if folder is None:
                    continue

                folder_key = str(folder)
                if folder_key in seen:
                    continue
                seen.add(folder_key)

                image_file, mask_file = get_image_and_mask(folder)
                if image_file is None or mask_file is None:
                    continue

                pairs.append({
                    "image": image_file,
                    "mask":  mask_file,
                })

    print(f"\n[prepare] Paires image/masque trouvées : {len(pairs)}")
    return pairs


# ── Traitement image/masque ───────────────────────────────────────────────────
def process_pair(image_path: Path, mask_path: Path, img_size: int):
    """
    - Image  : RGB resizée
    - Masque : binaire L (blanc = tumeur, noir = fond)
    """
    image = Image.open(image_path).convert("RGB").resize(
        (img_size, img_size), Image.BILINEAR
    )

    mask    = Image.open(mask_path).convert("L").resize(
        (img_size, img_size), Image.NEAREST
    )
    mask_np = np.array(mask)

    # CBIS-DDSM masques toujours inversés → on inverse toujours
    mask_np = (mask_np < 127).astype(np.uint8) * 255

    mask = Image.fromarray(mask_np, mode="L")
    return image, mask


# ── Copie split ───────────────────────────────────────────────────────────────
def copy_pairs(pairs, output_dir, val_split, rng):
    rng.shuffle(pairs)
    n_val   = max(1, int(len(pairs) * val_split))
    val_p   = pairs[:n_val]
    train_p = pairs[n_val:]

    for split_name, split_pairs in [("train", train_p), ("val", val_p)]:
        img_dir  = output_dir / split_name / "images"
        mask_dir = output_dir / split_name / "masks"
        img_dir.mkdir(parents=True, exist_ok=True)
        mask_dir.mkdir(parents=True, exist_ok=True)

        ok = 0
        for i, pair in enumerate(tqdm(split_pairs, desc=f"{split_name}")):
            try:
                image, mask = process_pair(pair["image"], pair["mask"], IMG_SIZE)

                img_name  = f"image_{i:05d}.jpg"
                mask_name = f"image_{i:05d}.png"

                image.save(img_dir  / img_name,  quality=95)
                mask.save(mask_dir  / mask_name)
                ok += 1
            except Exception as e:
                print(f"  ⚠️ Erreur {pair['image'].name} : {e}")

        print(f"  {split_name} : {ok} paires sauvegardées")

    return len(train_p), len(val_p)


# ── Vérification masques ──────────────────────────────────────────────────────
def verify_masks(output_dir, n=20):
    mask_dir = output_dir / "train" / "masks"
    masks    = list(mask_dir.glob("*.png"))[:n]
    pcts     = []

    for m in masks:
        arr = np.array(Image.open(m).convert("L"))
        pct = (arr > 127).sum() / arr.size * 100
        pcts.append(pct)

    avg = np.mean(pcts)
    print(f"\n[verify] Pixels tumeur moyen : {avg:.1f}%")
    print(f"[verify] Min : {np.min(pcts):.1f}%  Max : {np.max(pcts):.1f}%")

    if avg < 30:
        print("[verify] ✅ Masques corrects — tumeur bien délimitée")
    else:
        print("[verify] ⚠️ Masques peut-être incorrects — vérifie visuellement")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    if not RAW_DIR.exists():
        raise SystemExit(f"❌ Dataset introuvable : {RAW_DIR}")

    rng = random.Random(SEED)

    print("=" * 60)
    print(f"[prepare] Source : {RAW_DIR}")
    print(f"[prepare] Output : {OUTPUT_DIR}")
    print(f"[prepare] Max paires : {MAX_PAIRS}")
    print("=" * 60)

    # Nettoie l'ancien dossier
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
        print("[prepare] Ancien dossier supprimé")

    pairs = collect(RAW_DIR)

    if not pairs:
        raise SystemExit("❌ Aucune paire trouvée")

    if len(pairs) > MAX_PAIRS:
        pairs = rng.sample(pairs, MAX_PAIRS)
        print(f"[prepare] Échantillon : {MAX_PAIRS} paires")

    train_n, val_n = copy_pairs(pairs, OUTPUT_DIR, VAL_SPLIT, rng)

    print(f"\n✅ Terminé — Train: {train_n} | Val: {val_n}")

    # Vérification automatique
    verify_masks(OUTPUT_DIR)

    print("\nLance ensuite : python train_segmentation.py")


if __name__ == "__main__":
    main()