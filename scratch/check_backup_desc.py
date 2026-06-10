import pandas as pd

file_path = r"C:\Users\3171131\Desktop\excels\WO y TASK Plataformas Centrales v3 8.xlsx"
df = pd.read_excel(file_path)

df_oferta = df[df["Oferta"].astype(str).str.strip().str.lower() == "respaldos de información en servidores"]

print("Descriptions of the backup rows:")
for idx, d in enumerate(df_oferta["Descripción"].dropna().head(10)):
    print(f"\nRow {idx}:")
    print(repr(d[:200]))
