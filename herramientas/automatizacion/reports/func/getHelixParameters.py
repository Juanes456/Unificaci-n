import os
import json
import sqlite3
import pandas as pd

def get_helix_parameters(parameters_path=None, report_type='Incidentes abiertos'):
    """
    Obtiene los DataFrames de GrupoHelix y AsociadosTCS.
    Si parameters_path es válido, lee las hojas del Excel.
    Si parameters_path es None o no existe, lee los datos de la base de datos de Django db.sqlite3 
    o de la caché local 'usuarios_tcs_cache.json'.
    """
    # Intentar leer desde el Excel si se suministra un path válido
    if parameters_path and os.path.exists(parameters_path):
        try:
            from reports.func.readDocuments import getData as gtDc
            data = gtDc(parameters_path, report_type)
            if data and 'GrupoHelix' in data and 'AsociadosTCS' in data:
                return data['GrupoHelix'], data['AsociadosTCS']
        except Exception as excel_err:
            print(f"Advertencia: No se pudo leer el archivo Excel de parámetros. Usando base de datos/caché: {excel_err}")

    # Fallback a Base de datos / Caché local
    df_groups = pd.DataFrame(columns=['NOMBRE DEL GRUPO BMC HELIX', 'Torre'])
    df_associates = pd.DataFrame(columns=['Column1', 'Torre'])

    # Encontrar db.sqlite3 en las rutas de desarrollo del usuario
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # script_dir is herramientas/automatizacion/reports/func
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_dir))))
    candidate_db_paths = [
        os.path.abspath(os.path.join(project_root, "db.sqlite3")),
        os.path.abspath(os.path.join(project_root, "..", "..", "..", "Front-backend", "reporte-de-consumos-backend", "db.sqlite3")),
        r"C:\Users\3171131\Desktop\Front-backend\reporte-de-consumos-backend\db.sqlite3",
        os.path.join(project_root, "automatizacion_portable", "db.sqlite3")
    ]

    db_path = None
    for path in candidate_db_paths:
        if os.path.exists(path):
            db_path = path
            break

    # 1. Cargar grupos de Helix
    loaded_groups = False
    if db_path:
        try:
            conn = sqlite3.connect(db_path)
            # La tabla de Django para Grupos de soporte es 'Grupo'
            query_groups = "SELECT nombreGrupoHelix, torre FROM Grupo"
            groups_data = pd.read_sql_query(query_groups, conn)
            groups_data.rename(columns={'nombreGrupoHelix': 'NOMBRE DEL GRUPO BMC HELIX', 'torre': 'Torre'}, inplace=True)
            if not groups_data.empty:
                df_groups = groups_data
                loaded_groups = True
            conn.close()
        except Exception as db_err:
            print(f"Error al leer grupos de la base de datos: {db_err}")

    if not loaded_groups:
        # Fallback a un set mínimo en código o dejar vacío
        print("Advertencia: No se pudieron cargar los grupos desde la base de datos.")

    # 2. Cargar asociados de TCS
    loaded_associates = False
    if db_path:
        try:
            conn = sqlite3.connect(db_path)
            # La tabla de Django es 'UsuariosTCS'
            query_users = "SELECT nombre, usuario, torre FROM UsuariosTCS WHERE activo = 1"
            users_data = pd.read_sql_query(query_users, conn)
            conn.close()
            
            if not users_data.empty:
                # El algoritmo de getTorre original hace merge con Column1. 
                # Column1 típicamente tiene el Nombre Completo. 
                # Para asegurar la máxima compatibilidad y que funcione si buscan por nombre completo o por usuario (Remedy Login ID):
                assoc_list = []
                for _, row in users_data.iterrows():
                    nombre = row['nombre']
                    usuario = row['usuario']
                    torre = row['torre']
                    if nombre:
                        assoc_list.append({'Column1': str(nombre).strip().upper(), 'Torre': torre})
                    if usuario:
                        assoc_list.append({'Column1': str(usuario).strip().upper(), 'Torre': torre})
                        assoc_list.append({'Column1': str(usuario).strip().lower(), 'Torre': torre})
                df_associates = pd.DataFrame(assoc_list).drop_duplicates(subset=['Column1'])
                loaded_associates = True
        except Exception as db_err:
            print(f"Error al leer usuarios de la base de datos: {db_err}")

    # Si la base de datos no está disponible, cargar desde el archivo json de caché
    if not loaded_associates:
        cache_path = os.path.join(project_root, "usuarios_tcs_cache.json")
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    users_list = json.load(f)
                assoc_list = []
                for user in users_list:
                    if user.get('activo', True):
                        nombre = user.get('nombre')
                        usuario = user.get('usuario')
                        torre = user.get('torre')
                        if nombre:
                            assoc_list.append({'Column1': str(nombre).strip().upper(), 'Torre': torre})
                        if usuario:
                            assoc_list.append({'Column1': str(usuario).strip().upper(), 'Torre': torre})
                            assoc_list.append({'Column1': str(usuario).strip().lower(), 'Torre': torre})
                df_associates = pd.DataFrame(assoc_list).drop_duplicates(subset=['Column1'])
                loaded_associates = True
                print("Usuarios cargados exitosamente desde la caché json local.")
            except Exception as cache_err:
                print(f"Error al leer usuarios de la caché json: {cache_err}")

    return df_groups, df_associates
