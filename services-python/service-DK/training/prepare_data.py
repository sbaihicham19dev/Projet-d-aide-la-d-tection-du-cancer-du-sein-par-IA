"""
prepare_data.py  —  CBIS-DDSM → Dataset ResNet50

Labels :
    MALIGNANT               -> Cancer
    BENIGN                  -> Non-Cancer
    BENIGN_WITHOUT_CALLBACK -> Non-Cancer

Cible :
    Cancer     : train=1700  val=300
    Non-Cancer : train=1700  val=300
"""

import os, cv2, random
import pandas as pd
from glob import glob
from tqdm import tqdm

# ── CONFIG ────────────────────────────────────────────────
DATASET_DIR = r"C:\Users\hicha\Downloads\cbis-ddsm"
OUTPUT_DIR  = "data"
IMAGE_SIZE  = 224
SEED        = 42

TARGET = {
    "Cancer":     {"train": 1700, "val": 300},
    "Non-Cancer": {"train": 1700, "val": 300},
}

CSV_FILES = [
    "mass_case_description_train_set.csv",
    "mass_case_description_test_set.csv",
    "calc_case_description_train_set.csv",
    "calc_case_description_test_set.csv",
]

# ── CREATE FOLDERS ────────────────────────────────────────
for split in ["train", "val"]:
    for cls in ["Cancer", "Non-Cancer"]:
        os.makedirs(os.path.join(OUTPUT_DIR, split, cls), exist_ok=True)

# ── HELPERS ───────────────────────────────────────────────
def get_label(pathology):
    p = str(pathology).strip().upper()
    if p == "MALIGNANT":
        return "Cancer"
    if p in ("BENIGN", "BENIGN_WITHOUT_CALLBACK"):
        return "Non-Cancer"
    return None

def clean_image(path):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None or img.shape[0] < 100 or img.shape[1] < 100:
        return None
    coords = cv2.findNonZero(img)
    if coords is not None:
        x, y, w, h = cv2.boundingRect(coords)
        img = img[y:y+h, x:x+w]
    img = cv2.resize(img, (IMAGE_SIZE, IMAGE_SIZE))
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    img = clahe.apply(img)
    return cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

def build_uid_index(jpeg_root):
    """
    Structure disque :  jpeg/<UID_dossier>/<fichier>.jpg
    Retourne dict       {UID_dossier: chemin_premier_jpg}
    """
    print("[INFO] Indexation des dossiers UID...")
    index = {}
    for jpg in glob(os.path.join(jpeg_root, "**", "*.jpg"), recursive=True):
        uid = os.path.basename(os.path.dirname(jpg))
        if uid not in index:
            index[uid] = jpg
    print(f"[INFO] {len(index)} UIDs indexes")
    return index

def resolve(row, uid_index):
    """
    Chemin CSV :  Prefix/UID_serie/UID_instance/000000.dcm
    UID_instance (avant-dernier) = dossier present dans jpeg/
    """
    for col in ["image file path", "cropped image file path", "ROI mask file path"]:
        raw = str(row.get(col, "")).strip()
        if not raw or raw == "nan":
            continue
        # normaliser separateurs
        parts = [p for p in raw.replace("\\", "/").split("/") if p]
        # tester positions -2 puis -3 puis -1
        for i in [-2, -3, -1]:
            if len(parts) >= abs(i):
                uid = parts[i]
                if uid in uid_index:
                    return uid_index[uid]
    return None

# ── STEP 1 : LOAD CSV ─────────────────────────────────────
print("\n[1/5] Chargement CSV...")
dfs = []
for f in CSV_FILES:
    p = os.path.join(DATASET_DIR, "csv", f)
    if os.path.exists(p):
        df = pd.read_csv(p)
        df["_src"] = f
        dfs.append(df)
        print(f"  OK  {f}  ({len(df)} lignes)")
    else:
        print(f"  MANQUANT : {p}")
df_all = pd.concat(dfs, ignore_index=True)
print(f"  Total : {len(df_all)} lignes")

# ── STEP 2 : LABELS ───────────────────────────────────────
print("\n[2/5] Labélisation...")
pcol = next((c for c in df_all.columns if "pathology" in c.lower()), None)
df_all["label"] = df_all[pcol].apply(lambda x: get_label(x) if pd.notna(x) else None)
df_all = df_all[df_all["label"].notna()].copy()
print(f"  {df_all['label'].value_counts().to_dict()}")

# ── STEP 3 : RESOLVE PATHS ───────────────────────────────
print("\n[3/5] Résolution des chemins...")
uid_index = build_uid_index(os.path.join(DATASET_DIR, "jpeg"))

tqdm.pandas(desc="  Résolution")
df_all["image_path"] = df_all.progress_apply(lambda r: resolve(r, uid_index), axis=1)

df_valid = df_all[df_all["image_path"].notna()].copy()
print(f"  Resolues : {len(df_valid)} / {len(df_all)}")
print(f"  {df_valid['label'].value_counts().to_dict()}")

if len(df_valid) == 0:
    # Debug : afficher un exemple pour diagnostic
    row0 = df_all.iloc[0]
    raw  = str(row0.get("image file path", ""))
    parts = [p for p in raw.replace("\\", "/").split("/") if p]
    print("\n[DEBUG] Exemple chemin CSV :", raw)
    print("[DEBUG] Segments            :", parts)
    print("[DEBUG] Exemple UID disque  :", list(uid_index.keys())[0])
    raise RuntimeError("0 images resolues. Voir debug ci-dessus.")

# ── STEP 4 : SAMPLE + SPLIT ──────────────────────────────
print("\n[4/5] Sampling et split...")
random.seed(SEED)
splits = {"train": [], "val": []}

for label, counts in TARGET.items():
    pool = df_valid[df_valid["label"] == label]["image_path"].tolist()
    need = counts["train"] + counts["val"]
    if len(pool) == 0:
        raise RuntimeError(f"Aucune image pour '{label}'")
    if len(pool) < need:
        print(f"  WARN {label} : {len(pool)} dispo < {need} → sur-echantillonnage")
        pool = random.choices(pool, k=need)
    else:
        pool = random.sample(pool, need)
    splits["train"] += [(p, label) for p in pool[:counts["train"]]]
    splits["val"]   += [(p, label) for p in pool[counts["train"]:]]
    print(f"  {label} -> train:{counts['train']}  val:{counts['val']}")

# ── STEP 5 : SAVE ────────────────────────────────────────
print("\n[5/5] Sauvegarde...")

def save_split(name, samples):
    cnt = {"Cancer": 0, "Non-Cancer": 0}
    skip = 0
    for path, label in tqdm(samples, desc=f"  {name}"):
        img = clean_image(path)
        if img is None:
            skip += 1
            continue
        fname = f"{label.replace('-','_')}_{cnt[label]:04d}.png"
        cv2.imwrite(os.path.join(OUTPUT_DIR, name, label, fname), img)
        cnt[label] += 1
    print(f"  Sauvegardes={cnt}  Ignores={skip}")

save_split("train", splits["train"])
save_split("val",   splits["val"])

# ── RAPPORT ──────────────────────────────────────────────
print("\n" + "="*44)
print("           DATASET PRET")
print("="*44)
for split in ["train", "val"]:
    for cls in ["Cancer", "Non-Cancer"]:
        n   = len(os.listdir(os.path.join(OUTPUT_DIR, split, cls)))
        exp = TARGET[cls][split]
        ok  = "OK" if n == exp else f"WARN attendu {exp}"
        print(f"  {split:5s} / {cls:12s} : {n:4d}  {ok}")
print("="*44)