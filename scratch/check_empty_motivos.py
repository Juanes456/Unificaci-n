import pandas as pd
import os

file_path = r"C:\Users\3171131\Desktop\excels\WO y TASK Plataformas Centrales v3 8.xlsx"
df = pd.read_excel(file_path)

col_motivo = "MotivoEstadodeWO"
if col_motivo in df.columns:
    print(f"Total values in '{col_motivo}' in raw file:")
    print(df[col_motivo].value_counts(dropna=False).head(10))
else:
    print(f"Column '{col_motivo}' not found.")
