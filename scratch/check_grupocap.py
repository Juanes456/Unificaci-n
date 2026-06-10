import pandas as pd

file_path = r"c:\Users\3171131\Downloads\Copy of WO y TASK Plataformas Centrales v3 1.xlsx"
df = pd.read_excel(file_path)

df_oferta = df[df["Oferta"].astype(str).str.strip().str.lower() == "gestión de usuarios bases de datos"]
print("GrupoCapacidadAsignado value counts for Oferta='Gestión de usuarios bases de datos':")
print(df_oferta["GrupoCapacidadAsignado"].value_counts(dropna=False))
