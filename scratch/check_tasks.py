import pandas as pd
import json
import os
from concatenacion_portable.concatenacion import _normalizar

file_path = r"c:\Users\3171131\Downloads\Copy of WO y TASK Plataformas Centrales v3 1.xlsx"
df = pd.read_excel(file_path)

df_oferta = df[df["Oferta"].astype(str).str.strip().str.lower() == "gestión de usuarios bases de datos"]
print(f"Total rows: {len(df_oferta)}")

# Load users cache
cache_path = "usuarios_tcs_cache.json"
with open(cache_path, "r", encoding="utf-8") as f:
    users_list = json.load(f)

user_to_torre = {
    _normalizar(u.get("nombre", "")): u.get("torre") for u in users_list
}
user_to_torre.update({
    _normalizar(u.get("usuario", "")): u.get("torre") for u in users_list if u.get("usuario")
})

col_usuario_asignado = "UsuarioAsignado"
col_grupo_tarea = "Grupoasignadotarea"

print("\nValue counts for UsuarioAsignado in these rows:")
for u, count in df_oferta[col_usuario_asignado].value_counts(dropna=False).items():
    norm = _normalizar(u)
    torre = user_to_torre.get(norm, "NOT FOUND")
    print(f"  User: '{u}' | Count: {count} | Torre: {torre}")

print("\nValue counts for Grupoasignadotarea in these rows:")
print(df_oferta[col_grupo_tarea].value_counts(dropna=False))
