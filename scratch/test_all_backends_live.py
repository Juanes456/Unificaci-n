import os
import sys
from datetime import datetime, timedelta
import pandas as pd

# Set stdout/stderr encoding to UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Define paths
WORKSPACE = r"c:\Users\3171131\Desktop\Proyectos (3)\Proyectos\unificada"
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

# Change directory to WORKSPACE for correct path imports
os.chdir(WORKSPACE)

# Add subdirectories to sys.path
sys.path.insert(0, os.path.join(WORKSPACE, "core"))
sys.path.insert(0, os.path.join(WORKSPACE, "herramientas"))
sys.path.insert(0, os.path.join(WORKSPACE, "herramientas", "automatizacion"))
sys.path.insert(0, os.path.join(WORKSPACE, "herramientas", "crq"))
sys.path.insert(0, os.path.join(WORKSPACE, "herramientas", "concatenacion"))

print("=== STARTING ONE-BY-ONE COMPONENT VERIFICATION ===")

# --- Helper function for results ---
def report_status(component, success, details=""):
    status = "SUCCESS" if success else "FAILED"
    print(f"[{component}] {status} - {details}")

# ==========================================
# 1. TEST AUTOMATIZACION (Incidentes Abiertos & Cerrados)
# ==========================================
print("\n--- 1. Testing Automatizacion Reports (API + Mapping) ---")
try:
    from reports.func.getDataApi import getActiveIncident, getFinalizedIncident
    from reports.func.getHelixParameters import get_helix_parameters
    
    # Let's run a query for the last 5 days
    end_date_dt = datetime.now()
    start_date_dt = end_date_dt - timedelta(days=5)
    
    start_str = start_date_dt.strftime('%Y-%m-%d')
    end_str = end_date_dt.strftime('%Y-%m-%d')
    
    print(f"Querying active incidents from {start_str} to {end_str}...")
    df_active = getActiveIncident(start_str, end_str)
    print(f"Retrieved {len(df_active) if df_active is not None else 0} active incidents.")
    
    print(f"Querying finalized incidents from {start_str} to {end_str}...")
    df_finalized = getFinalizedIncident(start_str, end_str)
    print(f"Retrieved {len(df_finalized) if df_finalized is not None else 0} finalized incidents.")
    
    # Try report mapping
    from reports.reportOpenInc import getReportOpenInc
    from reports.reportFinishInc import getReportFinishInc
    
    print("Testing getReportOpenInc...")
    res_open = getReportOpenInc(start_date_dt, end_date_dt, None)
    if res_open is not None:
        print(f"Report Open Incident parsed successfully. Report sheets: {list(res_open.keys())}")
        report_status("Incidentes Abiertos", True, f"Retrieved and mapped {len(res_open['Reporte'])} records.")
    else:
        report_status("Incidentes Abiertos", False, "No data or mapping failure.")
        
    print("Testing getReportFinishInc...")
    res_finish = getReportFinishInc(start_date_dt, end_date_dt, None)
    if res_finish is not None:
        print(f"Report Finish Incident parsed successfully. Keys: {list(res_finish.keys())}")
        report_status("Incidentes Cerrados", True, f"Retrieved and mapped {len(res_finish['Data'])} records.")
    else:
        report_status("Incidentes Cerrados", False, "No data or mapping failure.")
except Exception as e:
    import traceback
    report_status("Automatizacion", False, f"Exception occurred: {e}\n{traceback.format_exc()}")

# ==========================================
# 2. TEST CRQ PORTABLE (Helix API + Process)
# ==========================================
print("\n--- 2. Testing CRQ Portable ---")
try:
    import yaml
    from herramientas.crq.helix_client import HelixClient
    from herramientas.crq.processor import process_crq
    
    with open("herramientas/crq/config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        
    # Override date range to something small/recent (last 10 days)
    yesterday = datetime.now() - timedelta(days=10)
    config["date_range"]["date_from"] = yesterday.strftime('%Y-%m-%d')
    config["date_range"]["date_to"] = datetime.now().strftime('%Y-%m-%d')
    
    print(f"Querying CRQ/Tasks between {config['date_range']['date_from']} and {config['date_range']['date_to']}...")
    
    client = HelixClient(config["helix"])
    # 1. Test Authenticate
    client.authenticate()
    print("HelixClient Authentication: Success.")
    
    # 2. Test Fetching Tasks directly using HelixClient query
    tms_cfg = config["helix"]["tasks"]
    query = f"'{tms_cfg['task_date_field']}' >= \"{config['date_range']['date_from']}T00:00:00\" and '{tms_cfg['task_date_field']}' <= \"{config['date_range']['date_to']}T23:59:59\""
    
    # Custom get records query to check API pull
    from herramientas.crq.utils import extract_path
    
    url = f"{client.base_url}/{tms_cfg['endpoint'].lstrip('/')}?q={query}&fields={tms_cfg['fields']}&limit=10"
    resp = client.session.get(url)
    resp.raise_for_status()
    entries = resp.json().get(tms_cfg["results_path"], [])
    print(f"Retrieved {len(entries)} raw task entries from Helix API.")
    
    report_status("CRQ API Connection", True, f"Successfully authenticated and queried Tasks.")
except Exception as e:
    import traceback
    report_status("CRQ API Connection", False, f"Exception occurred: {e}\n{traceback.format_exc()}")

# ==========================================
# 3. TEST CONCATENACION PORTABLE
# ==========================================
print("\n--- 3. Testing Concatenacion Portable ---")
try:
    from herramientas.concatenacion.concatenacion import load_concatenacion_config, HelixClient as ConcatHelixClient
    import django_db_helper
    
    cfg = load_concatenacion_config("herramientas/concatenacion/config.json")
    print(f"Testing Helix login for Concatenacion (User: {cfg.helix_user})...")
    
    client = ConcatHelixClient(cfg)
    token = client._helix_login()
    print("Concatenacion Helix login: Success.")
    
    # Try fetching users via django_db_helper (which is the actual production path)
    print(f"Fetching users using django_db_helper for tower: '{cfg.torre}'...")
    users = django_db_helper.get_users_from_api(
        api_url=cfg.django_api_url,
        torre=cfg.torre
    )
    print(f"Successfully fetched {len(users)} users using django_db_helper.")
    
    report_status("Concatenacion API Connection", True, f"Successfully authenticated and fetched {len(users)} users via django_db_helper.")
except Exception as e:
    import traceback
    report_status("Concatenacion API Connection", False, f"Exception occurred: {e}\n{traceback.format_exc()}")

print("\n=== VERIFICATION COMPLETE ===")
