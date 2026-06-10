import pandas as pd
import os
import json
from concatenacion_portable.concatenacion import load_concatenacion_config, _normalizar
import django_db_helper

# Let's inspect the files in the output or input to see what's being processed
# Let's find any excel files in the workspace or outputs
print("Files in workspace:")
for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith(".xlsx") and not file.startswith("~$"):
            print("  ", os.path.join(root, file))

# Let's see what users are in the cache for "Malla de operaciones"
cache_path = "usuarios_tcs_cache.json"
if os.path.exists(cache_path):
    with open(cache_path, "r", encoding="utf-8") as f:
        users_list = json.load(f)
    print("\nTotal users in cache:", len(users_list))
    malla_users = [u for u in users_list if u.get("torre", "").lower() == "malla de operaciones"]
    print("Malla de operaciones users count:", len(malla_users))
    print("Malla users sample:", [u.get("nombre") for u in malla_users[:5]])
    bd_users = [u for u in users_list if u.get("torre", "").lower() == "base de datos"]
    print("Base de datos users count:", len(bd_users))
