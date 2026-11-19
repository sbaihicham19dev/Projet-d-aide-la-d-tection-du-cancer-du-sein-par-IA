import pandas as pd 
df = pd.read_csv(r'C:\Users\hicha\Downloads\cbis-ddsm\csv\mass_case_description_train_set.csv') 
print(df.columns.tolist()) 
print(df.iloc[0]) 
