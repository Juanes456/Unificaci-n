import pandas as pd
import json
import os
from concatenacion_portable.concatenacion import _normalizar

file_path = r"c:\Users\3171131\Downloads\Copy of WO y TASK Plataformas Centrales v3 1.xlsx"
df = pd.read_excel(file_path)

cache_path = "usuarios_tcs_cache.json"
with open(cache_path, "r", encoding="utf-8") as f:
    users_list = json.load(f)

malla_users = {_normalizar(u["nombre"]) for u in users_list if u.get("torre", "").lower() == "malla de operaciones"}
malla_users_usr = {_normalizar(u["usuario"]) for u in users_list if u.get("torre", "").lower() == "malla de operaciones" and u.get("usuario")}
all_malla_users = malla_users.union(malla_users_usr)

col_analista = "Analistadecapacidadasignado"
df_malla = df[df[col_analista].astype(str).apply(_normalizar).isin(all_malla_users)]
print(f"Total rows with Malla analysts: {len(df_malla)}")

if len(df_malla) > 0:
    print("\nResumenWO value counts for Malla analysts:")
    print(df_malla["ResumenWO"].value_counts(dropna=False).head(20))
