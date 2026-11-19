import pandas as pd
import shutil
import os
from pathlib import Path

# ─── CHEMINS ──────────────────────────────────────────
CSV_DIR    = r"C:\Users\DELL\Downloads\cbis-ddsm\csv"
JPEG_DIR   = r"C:\Users\DELL\Downloads\cbis-ddsm\jpeg"
OUTPUT_DIR = r"C:\Users\DELL\Documents\CHU\breast-cancer-pipeline\services-python\detection-service\training\data\cbis_ddsm"

# ─── LIMITE PAR CLASSE ────────────────────────────────
MAX_PER_CLASS = 300

# ─── CRÉER LES DOSSIERS ───────────────────────────────
os.makedirs(f"{OUTPUT_DIR}/Cancer", exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/Non-Cancer", exist_ok=True)

# ─── CHARGER LES CSV ──────────────────────────────────
dfs = []
for csv_file in [
    "mass_case_description_train_set.csv",
    "mass_case_description_test_set.csv",
    "calc_case_description_train_set.csv",
    "calc_case_description_test_set.csv"
]:
    df = pd.read_csv(os.path.join(CSV_DIR, csv_file))
    dfs.append(df)

df_all = pd.concat(dfs, ignore_index=True)

print(f"[INFO] Total cases: {len(df_all)}")

# ─── IDENTIFIER LA COLONNE PATHOLOGIE ─────────────────
path_col = None
for col in df_all.columns:
    if "pathology" in col.lower():
        path_col = col
        break

print(f"[INFO] Colonne pathologie: {path_col}")
print(df_all[path_col].value_counts())
# ─── COPIER LES IMAGES ────────────────────────────────
copied = 0
not_found = 0
done = False

for root, dirs, files in os.walk(JPEG_DIR):
    if done:
        break
    for file in files:
        if not (file.endswith(".jpg") or file.endswith(".jpeg")):
            continue

        folder_name = Path(root).name

        match = df_all[df_all.apply(
            lambda row: str(row.get('image file path', '')).find(folder_name) != -1 or
                        str(row.get('cropped image file path', '')).find(folder_name) != -1,
            axis=1
        )]

        src = os.path.join(root, file)

        if len(match) > 0:
            pathology = match.iloc[0][path_col]
            folder = "Cancer" if "MALIGNANT" in str(pathology).upper() else "Non-Cancer"

            count = len(os.listdir(f"{OUTPUT_DIR}/{folder}"))
            if count >= MAX_PER_CLASS:
                continue

            dst = os.path.join(OUTPUT_DIR, folder, f"{folder_name}_{file}")
            shutil.copy2(src, dst)
            copied += 1
            print(f"[{folder}] {copied} copié")
        else:
            not_found += 1

        # Arrêter si les deux classes sont pleines
        c = len(os.listdir(f"{OUTPUT_DIR}/Cancer"))
        nc = len(os.listdir(f"{OUTPUT_DIR}/Non-Cancer"))
        if c >= MAX_PER_CLASS and nc >= MAX_PER_CLASS:
            done = True
            break

print(f"\n✅ Images copiées : {copied}")
print(f"📁 Cancer : {len(os.listdir(OUTPUT_DIR+'/Cancer'))} images")
print(f"📁 Non-Cancer : {len(os.listdir(OUTPUT_DIR+'/Non-Cancer'))} images")