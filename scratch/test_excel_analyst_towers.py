import pandas as pd
import os
import json
import glob
from concatenacion_portable.concatenacion import _normalizar

# Find all Excel files in the folder "c:/Users/3171131/Desktop/Proyectos (3)/Proyectos"
excel_files = glob.glob("c:/Users/3171131/Desktop/Proyectos (3)/Proyectos/**/*.xlsx", recursive=True)
print("Excel files found:")
for f in excel_files:
    print("  ", f)

# Read the cache of users to map them
cache_path = "usuarios_tcs_cache.json"
if os.path.exists(cache_path):
    with open(cache_path, "r", encoding="utf-8") as f:
        users_list = json.load(f)
    user_to_torre = {}
    for u in users_list:
        n = _normalizar(u.get("nombre", ""))
        usr = _normalizar(u.get("usuario", ""))
        torre = u.get("torre", "")
        if n:
            user_to_torre[n] = torre
        if usr:
            user_to_torre[usr] = torre
else:
    print("No cache found")
    user_to_torre = {}

# Check the analysts in the files
for f in excel_files:
    if "Resultado" in f or "output" in f:
        continue
    try:
        df = pd.read_excel(f)
        col_analista = "Analistadecapacidadasignado"
        col_resumen = "ResumenWO"
        
        if col_analista in df.columns:
            print(f"\nAnalyzing file: {f}")
            print(f"Total rows: {len(df)}")
            
            # Show a sample of ResumenWO
            if col_resumen in df.columns:
                print("ResumenWO value counts:")
                print(df[col_resumen].value_counts().head(5))
                
            analysts = df[col_analista].dropna().unique()
            print(f"Unique analysts: {len(analysts)}")
            for a in analysts:
                norm_a = _normalizar(a)
                torre = user_to_torre.get(norm_a, "NOT FOUND IN CACHE")
                print(f"  Analyst: '{a}' | Torre: {torre}")
    except Exception as e:
         print(f"Error reading {f}: {e}")
