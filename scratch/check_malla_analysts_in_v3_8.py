import pandas as pd
import json
import sqlite3
import os
from concatenacion_portable.concatenacion import _normalizar

file_path = r"C:\Users\3171131\Desktop\excels\WO y TASK Plataformas Centrales v3 8.xlsx"
df = pd.read_excel(file_path)

db_path = r"C:\Users\3171131\Desktop\Front-backend\reporte-de-consumos-backend\db.sqlite3"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all Malla users from DB
cursor.execute("SELECT nombre, usuario FROM UsuariosTCS WHERE LOWER(torre) = 'malla de operaciones'")
malla_users = cursor.fetchall()
malla_names = {_normalizar(r[0]) for r in malla_users if r[0]}
malla_users_short = {_normalizar(r[1]) for r in malla_users if r[1]}
all_malla = malla_names.union(malla_users_short)

print(f"Total Malla users in DB: {len(all_malla)}")

col_analista = "Analistadecapacidadasignado"
df_malla_rows = df[df[col_analista].astype(str).apply(_normalizar).isin(all_malla)]

print(f"Total rows in Excel assigned to Malla users from DB: {len(df_malla_rows)}")
if len(df_malla_rows) > 0:
    print("\nValue counts of Oferta for these Malla rows:")
    print(df_malla_rows["Oferta"].value_counts(dropna=False))
    print("\nValue counts of Analistadecapacidadasignado for these Malla rows:")
    print(df_malla_rows[col_analista].value_counts(dropna=False))
else:
    # Print a sample of all analysts in the Excel file
    print("\nSample of all unique analysts in Excel file:")
    print(df[col_analista].value_counts().head(20))

conn.close()
