import pandas as pd
import json
import os
from concatenacion_portable.concatenacion import _normalizar

file_path = r"c:\Users\3171131\Downloads\Copy of WO y TASK Plataformas Centrales v3 1.xlsx"
df = pd.read_excel(file_path)

print("Oferta column unique values:")
print(df["Oferta"].value_counts(dropna=False).head(20))

# Let's filter by Oferta == "Gestión de usuarios bases de datos"
df_oferta = df[df["Oferta"].astype(str).str.strip().str.lower() == "gestión de usuarios bases de datos"]
print(f"\nTotal rows where Oferta is 'Gestión de usuarios bases de datos': {len(df_oferta)}")

if len(df_oferta) > 0:
    cache_path = "usuarios_tcs_cache.json"
    with open(cache_path, "r", encoding="utf-8") as f:
        users_list = json.load(f)

    user_to_torre = {
        _normalizar(u.get("nombre", "")): u.get("torre") for u in users_list
    }
    user_to_torre.update({
        _normalizar(u.get("usuario", "")): u.get("torre") for u in users_list if u.get("usuario")
    })

    col_analista = "Analistadecapacidadasignado"
    print("\nAnalysts assigned to Oferta='Gestión de usuarios bases de datos':")
    for a, count in df_oferta[col_analista].value_counts().items():
        norm = _normalizar(a)
        torre = user_to_torre.get(norm, "NOT FOUND")
        print(f"  Analyst: '{a}' | Count: {count} | Torre: {torre}")
