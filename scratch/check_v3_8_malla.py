import pandas as pd
import json
import sqlite3
import os
from concatenacion_portable.concatenacion import _normalizar

file_path = r"C:\Users\3171131\Desktop\excels\WO y TASK Plataformas Centrales v3 8.xlsx"
if not os.path.exists(file_path):
    print("File not found:", file_path)
    exit(1)

df = pd.read_excel(file_path)
print(f"Loaded {file_path} with {len(df)} rows.")

# 1. Filter by Oferta
col_oferta = "Oferta"
if col_oferta not in df.columns:
    print(f"Column '{col_oferta}' not found in columns: {list(df.columns)}")
    exit(1)

df_filtered = df[df[col_oferta].astype(str).str.strip().str.lower() == "gestión de usuarios bases de datos"]
print(f"Rows matching Oferta='Gestión de usuarios bases de datos': {len(df_filtered)}")

# 2. Get analysts for these rows
col_analista = "Analistadecapacidadasignado"
if len(df_filtered) > 0:
    analysts = df_filtered[col_analista].dropna().unique()
    print(f"Unique analysts in filtered rows ({len(analysts)}):")
    
    # Check them in DB
    db_path = r"C:\Users\3171131\Desktop\Front-backend\reporte-de-consumos-backend\db.sqlite3"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    for a in analysts:
        norm = _normalizar(a)
        # Search by name
        cursor.execute("SELECT nombre, usuario, torre, activo FROM UsuariosTCS WHERE nombre LIKE ?", (a,))
        db_rows = cursor.fetchall()
        if db_rows:
            for r in db_rows:
                print(f"  Analyst in Excel: '{a}' | DB Match: {r}")
        else:
            # Try searching with wildcard
            wildcard = f"%{a.split()[0]}%" if len(a.split()) > 0 else a
            cursor.execute("SELECT nombre, usuario, torre, activo FROM UsuariosTCS WHERE nombre LIKE ?", (wildcard,))
            db_wildcard = cursor.fetchall()
            print(f"  Analyst in Excel: '{a}' | NOT EXACT MATCH. Wildcard search for '{wildcard}':")
            for w in db_wildcard:
                print(f"    -> {w}")
                
    conn.close()
else:
    print("No rows found for Oferta='Gestión de usuarios bases de datos'")
