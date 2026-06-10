import pandas as pd
import re
import os
import json
from concatenacion_portable.concatenacion import _normalizar

file_path = r"c:\Users\3171131\Downloads\Copy of WO y TASK Plataformas Centrales v3 1.xlsx"
if not os.path.exists(file_path):
    print("File not found:", file_path)
    exit(1)

df = pd.read_excel(file_path)
print(f"Loaded file {file_path} with {len(df)} rows.")

# 1. Check ResumenWO distribution
print("\n1. ResumenWO value counts:")
print(df["ResumenWO"].value_counts(dropna=False).head(10))

# 2. Filter ResumenWO by "Gestión de usuarios bases de datos"
resumen_filtro = "Gestión de usuarios bases de datos"
df_filtered_resumen = df[
    df["ResumenWO"].astype(str).str.lower().str.startswith(resumen_filtro.lower())
    | (df["ResumenWO"].astype(str) == resumen_filtro)
]
print(f"\n2. Rows after ResumenWO filter ('{resumen_filtro}'): {len(df_filtered_resumen)}")

# 3. Filter TipoSolicitud
df_filtered_tipo = df_filtered_resumen[
    df_filtered_resumen["TipoSolicitud"].str.contains("Creación", na=False)
]
print(f"\n3. Rows after TipoSolicitud filter ('Creación'): {len(df_filtered_tipo)}")
if len(df_filtered_tipo) > 0:
    print("TipoSolicitud values:")
    print(df_filtered_tipo["TipoSolicitud"].value_counts())

# 4. Filter Descripción
df_filtered_desc = df_filtered_tipo[
    df_filtered_tipo["Descripción"]
    .astype(str)
    .str.lower()
    .str.contains(r"tipo solicitud.*cre", regex=True, na=False)
]
print(f"\n4. Rows after Descripción regex filter ('tipo solicitud.*cre'): {len(df_filtered_desc)}")
if len(df_filtered_desc) > 0:
    print("Sample descriptions:")
    for d in df_filtered_desc["Descripción"].head(3):
        print("  -", repr(d))

# 5. Filter Analysts
cache_path = "usuarios_tcs_cache.json"
with open(cache_path, "r", encoding="utf-8") as f:
    users_list = json.load(f)

# Find Malla users
malla_users = {_normalizar(u["nombre"]) for u in users_list if u.get("torre", "").lower() == "malla de operaciones"}
malla_users_usr = {_normalizar(u["usuario"]) for u in users_list if u.get("torre", "").lower() == "malla de operaciones" and u.get("usuario")}
all_malla_users = malla_users.union(malla_users_usr)

print(f"\nMalla users count: {len(all_malla_users)}")

if len(df_filtered_desc) > 0:
    col_analista = "Analistadecapacidadasignado"
    print("\nAnalysts in data before filtering:")
    print(df_filtered_desc[col_analista].value_counts(dropna=False))
    
    df_tcs = df_filtered_desc[
        df_filtered_desc[col_analista].astype(str).apply(_normalizar).isin(all_malla_users)
    ]
    print(f"\n5. Rows after Malla analysts filter: {len(df_tcs)}")
