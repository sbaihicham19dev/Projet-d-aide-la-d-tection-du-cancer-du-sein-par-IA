"""
prepare_data.py
---------------

Organise le dataset CBIS-DDSM local vers :

    training/data/cbis_ddsm/
        train/  Cancer/  Non-Cancer/
        val/    Cancer/  Non-Cancer/
"""

import argparse
import csv
import json
import random
import shutil
from pathlib import Path

from tqdm import tqdm

# ── Config ────────────────────────────────────────────────────────────────────
IMAGES_PER_CLASS = 2000
VAL_SPLIT        = 0.15
SEED             = 42
VALID_EXT        = {".jpg", ".jpeg", ".png"}

# ✅ FIXED PATH (TON PC)
RAW_DIR = Path(r"C:\Users\hicha\Downloads\cbis-ddsm")
BASE_DIR   = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "data" / "cbis_ddsm"

CSV_FILES = [
    "mass_case_description_train_set.csv",
    "mass_case_description_test_set.csv",
    "calc_case_description_train_set.csv",
    "calc_case_description_test_set.csv",
]

# ── Resolve image path ────────────────────────────────────────────────────────
def resolve_jpeg(image_file_path: str, jpeg_root: Path) -> Path | None:
    parts = image_file_path.strip().replace("\\", "/").split("/")

    if len(parts) < 3:
        return None

    uid_image = parts[-2]
    folder = jpeg_root / uid_image

    if not folder.exists():
        return None

    for f in folder.iterdir():
        if f.suffix.lower() in VALID_EXT:
            return f

    return None


# ── Collect ───────────────────────────────────────────────────────────────────
def collect(raw_dir: Path) -> dict:
    jpeg_root = raw_dir / "jpeg"
    csv_dir   = raw_dir / "csv"

    result = {"Cancer": [], "Non-Cancer": []}
    seen = set()

    for csv_name in CSV_FILES:
        csv_path = csv_dir / csv_name
        if not csv_path.exists():
            print(f"[prepare] CSV absent : {csv_name}")
            continue

        print(f"[prepare] Lecture : {csv_name}")

        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                pathology = row.get("pathology", "").strip().upper()
                img_path  = row.get("image file path", "").strip()

                if not pathology or not img_path:
                    continue

                label = "Cancer" if pathology == "MALIGNANT" else "Non-Cancer"

                img = resolve_jpeg(img_path, jpeg_root)
                if img is None:
                    continue

                if str(img) in seen:
                    continue
                seen.add(str(img))

                result[label].append(img)

    print("\n[prepare] Images trouvées :")
    print("  Cancer     :", len(result["Cancer"]))
    print("  Non-Cancer :", len(result["Non-Cancer"]))

    return result


# ── Sampling ──────────────────────────────────────────────────────────────────
def balanced_sample(paths, n, rng):
    if len(paths) >= n:
        return rng.sample(paths, n)

    pool = paths.copy()
    while len(pool) < n:
        pool += paths

    return rng.sample(pool, n)


# ── Copy split ────────────────────────────────────────────────────────────────
def copy_split(paths, label, output_dir, val_split, rng):
    rng.shuffle(paths)

    n_val = max(1, int(len(paths) * val_split))
    val_p = paths[:n_val]
    train_p = paths[n_val:]

    for split_name, split_paths in [("train", train_p), ("val", val_p)]:
        dest_dir = output_dir / split_name / label
        dest_dir.mkdir(parents=True, exist_ok=True)

        safe = label.replace("-", "_")

        for i, src in enumerate(tqdm(split_paths, desc=f"{split_name}/{label}", leave=False)):
            dest = dest_dir / f"{safe}_{split_name}_{i:05d}{src.suffix}"
            shutil.copy2(src, dest)

    return len(train_p), len(val_p)


# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--val-split", type=float, default=VAL_SPLIT)
    args = parser.parse_args()

    if not args.raw_dir.exists():
        raise SystemExit(f"❌ Dataset introuvable : {args.raw_dir}")

    if not (args.raw_dir / "csv").exists():
        raise SystemExit("❌ dossier csv manquant")

    if not (args.raw_dir / "jpeg").exists():
        raise SystemExit("❌ dossier jpeg manquant")

    rng = random.Random(SEED)

    print("=" * 60)
    print("[prepare] Source :", args.raw_dir)
    print("[prepare] Output :", args.output_dir)
    print("=" * 60)

    images = collect(args.raw_dir)

    if not images["Cancer"] and not images["Non-Cancer"]:
        raise SystemExit("❌ Aucune image trouvée")

    for label in ["Cancer", "Non-Cancer"]:
        print(f"\n[prepare] {label}")

        selected = balanced_sample(images[label], IMAGES_PER_CLASS, rng)
        train_n, val_n = copy_split(
            selected, label, args.output_dir, args.val_split, rng
        )

        print(f"  Train: {train_n} | Val: {val_n}")

    print("\n✅ Terminé. Lance ensuite : python train.py")


if __name__ == "__main__":
    main()