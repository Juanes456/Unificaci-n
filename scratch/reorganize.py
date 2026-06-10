import os
import sys
import shutil

WORKSPACE = r"c:\Users\3171131\Desktop\Proyectos (3)\Proyectos\unificada"
os.chdir(WORKSPACE)

print("Starting reorganization script...")

# 1. Create target directories
os.makedirs("core/shims", exist_ok=True)
os.makedirs("herramientas", exist_ok=True)

# 2. Move portable programs
def move_dir(src, dst):
    if os.path.exists(src):
        print(f"Moving directory {src} to {dst}")
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.move(src, dst)
    else:
        print(f"Source directory {src} does not exist")

move_dir("automatizacion_portable", "herramientas/automatizacion")
move_dir("crq_portable", "herramientas/crq")
move_dir("concatenacion_portable", "herramientas/concatenacion")

# 3. Move and rename shims/helpers
def move_file(src, dst):
    if os.path.exists(src):
        print(f"Moving file {src} to {dst}")
        if os.path.exists(dst):
            os.remove(dst)
        shutil.move(src, dst)
    else:
        print(f"Source file {src} does not exist")

move_file("django_db_helper.py", "core/django_db_helper.py")
move_file("automatizacion_main_shim.py", "core/shims/automatizacion_shim.py")
move_file("crq_shim.py", "core/shims/crq_shim.py")
move_file("concatenaci_n_shim.py", "core/shims/concatenacion_shim.py")

print("Files and directories moved successfully. Updating code files...")

# --- UPDATE main.py ---
main_path = "main.py"
if os.path.exists(main_path):
    with open(main_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Update sys.path configuration
    old_sys_path = """# Asegurar que el directorio actual (`unificada/`) esté en sys.path
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if THIS_DIR not in sys.path:
    sys.path.insert(0, THIS_DIR)"""

    new_sys_path = """# Asegurar que el directorio actual (`unificada/`) y módulos estén en sys.path
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if THIS_DIR not in sys.path:
    sys.path.insert(0, THIS_DIR)
sys.path.insert(0, os.path.join(THIS_DIR, "core"))
sys.path.insert(0, os.path.join(THIS_DIR, "core", "shims"))
sys.path.insert(0, os.path.join(THIS_DIR, "herramientas"))"""

    content = content.replace(old_sys_path, new_sys_path)

    # Update imports
    old_imports = """from design_tokens import *
from automatizacion_main_shim import build_automatizacion_page
from crq_shim import build_crq_page
from concatenaci_n_shim import build_concatenacion_page"""

    new_imports = """from design_tokens import *
from core.shims.automatizacion_shim import build_automatizacion_page
from core.shims.crq_shim import build_crq_page
from core.shims.concatenacion_shim import build_concatenacion_page"""

    content = content.replace(old_imports, new_imports)

    with open(main_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("main.py updated.")

# --- UPDATE core/shims/automatizacion_shim.py ---
aut_shim_path = "core/shims/automatizacion_shim.py"
if os.path.exists(aut_shim_path):
    with open(aut_shim_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Update paths
    old_paths = """THIS_DIR = os.path.dirname(os.path.abspath(__file__))
AUT_DIR = os.path.join(THIS_DIR, "automatizacion_portable")"""

    new_paths = """THIS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(THIS_DIR))
AUT_DIR = os.path.join(ROOT_DIR, "herramientas", "automatizacion")
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)"""

    content = content.replace(old_paths, new_paths)
    
    # Update interfaces loading to add AUT_DIR
    old_sys_path = """if AUT_DIR not in sys.path:
    sys.path.insert(0, AUT_DIR)"""
    
    new_sys_path = """if AUT_DIR not in sys.path:
    sys.path.insert(0, AUT_DIR)
if os.path.join(ROOT_DIR, "core") not in sys.path:
    sys.path.insert(0, os.path.join(ROOT_DIR, "core"))"""
    
    content = content.replace(old_sys_path, new_sys_path)

    with open(aut_shim_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("automatizacion_shim.py updated.")

# --- UPDATE core/shims/crq_shim.py ---
crq_shim_path = "core/shims/crq_shim.py"
if os.path.exists(crq_shim_path):
    with open(crq_shim_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Update path
    old_path = "REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))"
    new_path = """SHIM_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(SHIM_DIR))
sys.path.insert(0, os.path.join(REPO_ROOT, "herramientas", "crq"))"""

    content = content.replace(old_path, new_path)

    # Update import
    content = content.replace("from crq_portable.cli import run_crq", "from herramientas.crq.cli import run_crq")

    with open(crq_shim_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("crq_shim.py updated.")

# --- UPDATE core/shims/concatenacion_shim.py ---
concat_shim_path = "core/shims/concatenacion_shim.py"
if os.path.exists(concat_shim_path):
    with open(concat_shim_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Update path
    old_path = "REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))"
    new_path = """SHIM_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(SHIM_DIR))
sys.path.insert(0, os.path.join(REPO_ROOT, "herramientas", "concatenacion"))"""

    content = content.replace(old_path, new_path)

    # Update import
    content = content.replace("from concatenacion_portable.concatenacion import", "from herramientas.concatenacion.concatenacion import")

    with open(concat_shim_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("concatenacion_shim.py updated.")

# --- UPDATE core/django_db_helper.py ---
db_helper_path = "core/django_db_helper.py"
if os.path.exists(db_helper_path):
    with open(db_helper_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Update project root paths and cache paths
    old_cache = """    script_dir = os.path.dirname(os.path.abspath(__file__))
    cache_path = os.path.join(script_dir, "usuarios_tcs_cache.json")"""

    new_cache = """    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    cache_path = os.path.join(project_root, "usuarios_tcs_cache.json")"""

    content = content.replace(old_cache, new_cache)

    old_db = """        # 2. Intentar usar la base de datos SQLite de desarrollo (alternativa adicional para el dev)
        candidate_paths = [
            os.path.abspath(os.path.join(script_dir, "..", "..", "..", "Front-backend", "reporte-de-consumos-backend", "db.sqlite3")),
            os.path.abspath(os.path.join(script_dir, "db.sqlite3")),
            r"C:\\Users\\3171131\\Desktop\\Front-backend\\reporte-de-consumos-backend\\db.sqlite3"
        ]"""

    new_db = """        # 2. Intentar usar la base de datos SQLite de desarrollo (alternativa adicional para el dev)
        project_root = os.path.dirname(script_dir)
        candidate_paths = [
            os.path.abspath(os.path.join(project_root, "..", "..", "Front-backend", "reporte-de-consumos-backend", "db.sqlite3")),
            os.path.abspath(os.path.join(project_root, "db.sqlite3")),
            r"C:\\Users\\3171131\\Desktop\\Front-backend\\reporte-de-consumos-backend\\db.sqlite3"
        ]"""

    content = content.replace(old_db, new_db)

    with open(db_helper_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("django_db_helper.py updated.")

# --- UPDATE herramientas/crq/resi_client.py ---
resi_client_path = "herramientas/crq/resi_client.py"
if os.path.exists(resi_client_path):
    with open(resi_client_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Update config path in resi_client
    old_config_path = """_CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "config.json"
)"""

    new_config_path = """_CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "concatenacion_portable", "config.json"
)
if not os.path.exists(_CONFIG_FILE):
    _CONFIG_FILE = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "concatenacion", "config.json"
    )"""

    content = content.replace(old_config_path, new_config_path)
    
    with open(resi_client_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("resi_client.py updated.")

# --- UPDATE herramientas/automatizacion/reports/func/getHelixParameters.py ---
get_helix_params_path = "herramientas/automatizacion/reports/func/getHelixParameters.py"
if os.path.exists(get_helix_params_path):
    with open(get_helix_params_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Update project root calculations since it's now 1 level deeper
    old_root = """    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))"""

    new_root = """    script_dir = os.path.dirname(os.path.abspath(__file__))
    # script_dir is herramientas/automatizacion/reports/func
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_dir))))"""

    content = content.replace(old_root, new_root)

    with open(get_helix_params_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("getHelixParameters.py updated.")

print("REORGANIZATION COMPLETE!")
