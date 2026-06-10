import pandas as pd
import os
import glob
import json
from concatenacion_portable.concatenacion import _normalizar

cache_path = "usuarios_tcs_cache.json"
with open(cache_path, "r", encoding="utf-8") as f:
    users_list = json.load(f)

malla_users = {_normalizar(u["nombre"]) for u in users_list if u.get("torre", "").lower() == "malla de operaciones"}
malla_users_usr = {_normalizar(u["usuario"]) for u in users_list if u.get("torre", "").lower() == "malla de operaciones" and u.get("usuario")}
all_malla_users = malla_users.union(malla_users_usr)

excel_files = glob.glob("c:/Users/3171131/Downloads/**/*.xlsx", recursive=True)
for f in excel_files:
    try:
        df = pd.read_excel(f)
        if "Oferta" in df.columns and "Analistadecapacidadasignado" in df.columns:
            df_filtered = df[df["Oferta"].astype(str).str.strip().str.lower() == "gestión de usuarios bases de datos"]
            if len(df_filtered) > 0:
                col_analista = "Analistadecapacidadasignado"
                df_tcs = df_filtered[df_filtered[col_analista].astype(str).apply(_normalizar).isin(all_malla_users)]
                if len(df_tcs) > 0:
                    print(f"FOUND MATCHES IN FILE: {f}")
                    print(f"  Rows in Oferta: {len(df_filtered)} | Rows matching Malla: {len(df_tcs)}")
    except Exception as e:
        pass
