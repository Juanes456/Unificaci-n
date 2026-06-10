import pandas as pd
import os
import glob
import json
from concatenacion_portable.concatenacion import _normalizar

cache_path = "usuarios_tcs_cache.json"
with open(cache_path, "r", encoding="utf-8") as f:
    users_list = json.load(f)

user_to_torre = {}
for u in users_list:
    n = _normalizar(u.get("nombre", ""))
    usr = _normalizar(u.get("usuario", ""))
    if n:
        user_to_torre[n] = u.get("torre")
    if usr:
        user_to_torre[usr] = u.get("torre")

excel_files = glob.glob("c:/Users/3171131/Downloads/**/*.xlsx", recursive=True)
for f in excel_files:
    if "Resultado" in f or "combinado" in f or "concatenacion" in f:
        continue
    try:
        df = pd.read_excel(f)
        col_analista = "Analistadecapacidadasignado"
        if col_analista in df.columns:
            malla_count = 0
            bd_count = 0
            for val in df[col_analista].dropna().unique():
                norm = _normalizar(val)
                torre = user_to_torre.get(norm)
                if torre == "Malla de operaciones":
                    malla_count += 1
                elif torre == "Base de datos":
                    bd_count += 1
            if malla_count > 0 or bd_count > 0:
                print(f"File: {f} | Rows: {len(df)}")
                print(f"  Malla analysts: {malla_count} | BD analysts: {bd_count}")
    except Exception as e:
        pass
