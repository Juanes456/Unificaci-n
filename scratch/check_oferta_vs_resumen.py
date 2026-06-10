import pandas as pd

file_path = r"c:\Users\3171131\Downloads\Copy of WO y TASK Plataformas Centrales v3 1.xlsx"
df = pd.read_excel(file_path)

df_oferta = df[df["Oferta"].astype(str).str.strip().str.lower() == "gestión de usuarios bases de datos"]
print("For rows where Oferta is 'Gestión de usuarios bases de datos':")
print("ResumenWO value counts:")
print(df_oferta["ResumenWO"].value_counts(dropna=False))
