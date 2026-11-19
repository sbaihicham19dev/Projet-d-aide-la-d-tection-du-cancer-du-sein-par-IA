import pandas as pd 
import os 
from glob import glob 
df = pd.read_csv(r'C:\Users\hicha\Downloads\cbis-ddsm\csv\mass_case_description_train_set.csv') 
val = str(df.iloc[0]['image file path']) 
print('CSV path:', val) 
uid = val.replace('\\\\','/' ).rstrip('/').split('/')[-1] 
print('UID extrait:', uid) 
folders = os.listdir(r'C:\Users\hicha\Downloads\cbis-ddsm\jpeg') 
print('Exemple dossier disque:', folders[0]) 
print('Match?', uid in folders) 
