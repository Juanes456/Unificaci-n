from __future__ import annotations

import os
import sqlite3
import logging
import unicodedata
import re
import requests
import json

# Deshabilitar advertencias de certificados no verificados
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

def _normalizar(valor: str) -> str:
    """
    Normaliza una cadena de texto para facilitar comparaciones consistentes.
    
    Proceso:
    1. Convierte el texto a minúsculas y elimina espacios en blanco al inicio y al final.
    2. Aplica normalización Unicode NFD para separar los caracteres base de sus diacríticos.
    3. Remueve tildes, diéresis y otros caracteres de la categoría 'Mn' (Nonspacing Mark).
    4. Usa expresiones regulares para sustituir múltiples espacios en blanco consecutivos por uno solo.
    
    Args:
        valor (str): Cadena de texto a normalizar.
        
    Returns:
        str: Cadena de texto normalizada limpia.
    """
    s = str(valor).strip().lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"\s+", " ", s)
    return s

def _process_api_users_list(users_list: list, torre: str, source_name: str = "la API de Django") -> set[str]:
    """
    Filtra y normaliza la lista de usuarios obtenida en formato JSON/diccionario.
    
    Valida el estado activo de cada usuario, verifica si pertenece a la torre objetivo
    (o a cualquiera de la lista de torres válidas si la torre objetivo es 'todos')
    y agrega tanto el nombre completo normalizado como el usuario normalizado al conjunto.
    
    Args:
        users_list (list): Lista de diccionarios de usuario retornados por el backend.
        torre (str): Torre objetivo a filtrar (ej. 'Base de datos', 'pSeries', 'todos').
        source_name (str): Nombre descriptivo de la fuente para logs o errores.
        
    Returns:
        set[str]: Conjunto de nombres y usuarios normalizados.
        
    Raises:
        ValueError: Si no se encuentran usuarios activos coincidentes.
    """
    users = set()
    torres_list = ["base de datos", "pseries", "malla de operaciones", "wintel", "storage"]
    is_multi_torre = not torre or torre.strip().lower() == "todos"
    torre_target_lower = torre.strip().lower() if torre else ""

    for user_data in users_list:
        # Filtrar solo usuarios activos
        if not user_data.get("activo", True):
            continue

        user_torre = user_data.get("torre")
        if not user_torre:
            continue
            
        user_torre_lower = user_torre.strip().lower()
        match = False
        if is_multi_torre:
            if user_torre_lower in torres_list:
                match = True
        else:
            if user_torre_lower == torre_target_lower:
                match = True

        if match:
            nombre = user_data.get("nombre")
            usuario = user_data.get("usuario")
            if nombre:
                users.add(_normalizar(nombre))
            if usuario:
                users.add(_normalizar(usuario))

    if not users:
        raise ValueError(
            f"No se encontraron usuarios activos para la torre '{torre}' a través de {source_name}.\n"
            f"Por favor, configure los usuarios en la tabla UsuariosTCS de Django."
        )
    return users

def get_users_from_api(api_url: str, torre: str, timeout: int = 30) -> set[str]:
    """
    Realiza una petición GET al endpoint HTTP de Django para obtener la lista de usuarios TCS.
    
    Implementa un mecanismo de tolerancia a fallos (fallback):
    1. Si la llamada HTTP tiene éxito, actualiza un archivo de caché local (usuarios_tcs_cache.json).
    2. Si la llamada falla (por timeout o caída del servidor), intenta cargar desde la caché local.
    3. Si la caché local no existe o está corrupta, intenta realizar consultas directas a la base de datos
       SQLite de desarrollo local en las rutas habituales.
       
    Args:
        api_url (str): Dirección base del backend Django.
        torre (str): Torre por la cual filtrar los analistas.
        timeout (int): Límite de espera de la petición HTTP en segundos.
        
    Returns:
        set[str]: Conjunto de nombres de usuario y usuarios normalizados.
        
    Raises:
        ValueError: Si la API y todos los mecanismos de fallback fallan.
    """
    if not api_url:
        api_url = "http://127.0.0.1:8000/"

    # Construir endpoint completo para la tabla UsuariosTCS
    url = f"{api_url.rstrip('/')}/api/reporte-consumos/reportes-sla-de-gobierno/usuarios-tcs/"
    logger.info(f"Consultando usuarios TCS vía API en: {url}")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    cache_path = os.path.join(project_root, "usuarios_tcs_cache.json")

    try:
        # GET request, verify=False para omitir errores de certificados autofirmados corporativos
        resp = requests.get(url, timeout=timeout, verify=False)
        if resp.status_code != 200:
            raise ValueError(f"El servidor respondió con código {resp.status_code}: {resp.text[:200]}")
        
        body = resp.json()
        if isinstance(body, dict) and "value" in body:
            users_list = body["value"]
        elif isinstance(body, list):
            users_list = body
        else:
            users_list = []
            
        # Guardar en caché local para offline/fallbacks futuros
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(users_list, f, ensure_ascii=False, indent=2)
            logger.info("Caché local de usuarios actualizada correctamente.")
        except Exception as cache_err:
            logger.warning(f"No se pudo guardar la caché local de usuarios: {cache_err}")
            
        return _process_api_users_list(users_list, torre, "la API de Django")

    except Exception as e:
        logger.warning(
            f"La consulta a la API de Django en {url} falló o dio timeout (timeout={timeout}s).\n"
            f"Detalle: {e}\n"
            f"Intentando cargar usuarios desde la caché local..."
        )
        
        # 1. Intentar cargar desde el archivo de caché local del proyecto
        if os.path.exists(cache_path):
            logger.info(f"Cargando usuarios desde la caché local: {cache_path}")
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    cached_users_list = json.load(f)
                users = _process_api_users_list(cached_users_list, torre, "la caché local de respaldo")
                logger.info(f"Se recuperaron exitosamente {len(users)} nombres/usuarios desde la caché local de respaldo.")
                return users
            except Exception as cache_load_err:
                logger.error(f"El fallback a la caché local falló. Detalle: {cache_load_err}")
        else:
            logger.warning(f"No se encontró el archivo de caché local en: {cache_path}")
        
        # 2. Intentar usar la base de datos SQLite de desarrollo (alternativa adicional para el dev)
        project_root = os.path.dirname(script_dir)
        candidate_paths = [
            os.path.abspath(os.path.join(project_root, "..", "..", "Front-backend", "reporte-de-consumos-backend", "db.sqlite3")),
            os.path.abspath(os.path.join(project_root, "db.sqlite3")),
            r"C:\Users\3171131\Desktop\Front-backend\reporte-de-consumos-backend\db.sqlite3"
        ]
        
        sqlite_file = None
        for path in candidate_paths:
            if os.path.exists(path):
                sqlite_file = path
                break
                
        if sqlite_file:
            logger.info(f"Base de datos SQLite de desarrollo encontrada en: {sqlite_file}. Consultando...")
            try:
                sqlite_config = {
                    "engine": "sqlite3",
                    "name": sqlite_file
                }
                return get_users_from_db(sqlite_config, torre)
            except Exception as db_err:
                logger.error(f"El fallback a la base de datos SQLite de desarrollo falló. Detalle: {db_err}")
                
        raise ValueError(
            f"No se pudo conectar a la API del backend Django en {url} y no fue posible usar respaldos.\n"
            f"Asegúrate de que el servidor web de Django esté iniciado y sea accesible.\n"
            f"Detalle: {e}"
        )

def get_users_from_db(db_config: dict, torre: str) -> set[str]:
    """
    Se conecta directamente a la base de datos relacional de Django (SQLite o MySQL) y obtiene analistas TCS.
    
    Ejecuta consultas SQL sobre la tabla `UsuariosTCS` filtrando analistas de la torre asignada
    que estén marcados como activos (activo = 1).
    
    Args:
        db_config (dict): Parámetros de conexión a la base de datos (engine, host, port, user, password, name).
        torre (str): Nombre de la torre de analistas (ej: 'Base de datos', 'Wintel').
        
    Returns:
        set[str]: Conjunto de nombres de analistas y usuarios normalizados.
        
    Raises:
        ValueError: Si la conexión o consulta fallan y no es posible recuperar analistas.
    """
    if not db_config:
        raise ValueError("La configuración de base de datos 'db' está vacía o es inválida.")

    engine = db_config.get("engine", "sqlite3").lower()
    users = set()
    rows = []

    # Construir la condición de filtrado por torre
    torres_list = ["Base de datos", "pSeries", "Malla de operaciones", "Wintel", "Storage"]
    is_multi_torre = not torre or torre.strip().lower() == "todos"

    # Conectar a la base de datos según el motor configurado
    if "sqlite" in engine:
        db_path = db_config.get("name", "db.sqlite3")
        if not os.path.exists(db_path):
            raise ValueError(f"Archivo de base de datos SQLite no encontrado en: {db_path}")

        logger.info(f"Conectando a base de datos SQLite: {db_path}")
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            if is_multi_torre:
                placeholders = ",".join(["?"] * len(torres_list))
                query = f"SELECT nombre, usuario FROM UsuariosTCS WHERE LOWER(torre) IN ({placeholders}) AND activo = 1"
                cursor.execute(query, [t.lower() for t in torres_list])
            else:
                query = "SELECT nombre, usuario FROM UsuariosTCS WHERE LOWER(torre) = ? AND activo = 1"
                cursor.execute(query, (torre.strip().lower(),))
            rows = cursor.fetchall()
            conn.close()
        except Exception as e:
            raise ValueError(f"Error al consultar la tabla UsuariosTCS en SQLite: {e}")

    elif "mysql" in engine:
        try:
            import pymysql
        except ImportError:
            raise ImportError(
                "El paquete 'pymysql' es requerido para conectar a MySQL pero no está instalado."
            )

        host = db_config.get("host", "localhost")
        port = int(db_config.get("port", 3306))
        user = db_config.get("user", "").strip("'\"")
        password = db_config.get("password", "").strip("'\"")
        db_name = db_config.get("name", "").strip("'\"")

        logger.info(f"Conectando a base de datos MySQL en {host}:{port} ({db_name})")
        try:
            conn = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=db_name,
                charset="utf8mb4",
                connect_timeout=10
            )
            try:
                with conn.cursor() as cursor:
                    if is_multi_torre:
                        placeholders = ",".join(["%s"] * len(torres_list))
                        query = f"SELECT nombre, usuario FROM UsuariosTCS WHERE LOWER(torre) IN ({placeholders}) AND activo = 1"
                        cursor.execute(query, [t.lower() for t in torres_list])
                    else:
                        query = "SELECT nombre, usuario FROM UsuariosTCS WHERE LOWER(torre) = %s AND activo = 1"
                        cursor.execute(query, (torre.strip().lower(),))
                    rows = cursor.fetchall()
            finally:
                conn.close()
        except Exception as e:
            logger.warning(
                f"La conexión o consulta a la base de datos MySQL en {host}:{port} falló.\n"
                f"Detalle: {e}\n"
                f"Intentando usar base de datos SQLite local de respaldo..."
            )
            
            script_dir = os.path.dirname(os.path.abspath(__file__))
            candidate_paths = [
                os.path.abspath(os.path.join(script_dir, "..", "..", "..", "Front-backend", "reporte-de-consumos-backend", "db.sqlite3")),
                os.path.abspath(os.path.join(script_dir, "db.sqlite3")),
                r"C:\Users\3171131\Desktop\Front-backend\reporte-de-consumos-backend\db.sqlite3"
            ]
            
            sqlite_file = None
            for path in candidate_paths:
                if os.path.exists(path):
                    sqlite_file = path
                    break
                    
            if sqlite_file:
                logger.info(f"Base de datos SQLite local de respaldo encontrada en: {sqlite_file}. Consultando...")
                try:
                    conn = sqlite3.connect(sqlite_file)
                    cursor = conn.cursor()
                    if is_multi_torre:
                        placeholders = ",".join(["?"] * len(torres_list))
                        query = f"SELECT nombre, usuario FROM UsuariosTCS WHERE LOWER(torre) IN ({placeholders}) AND activo = 1"
                        cursor.execute(query, [t.lower() for t in torres_list])
                    else:
                        query = "SELECT nombre, usuario FROM UsuariosTCS WHERE LOWER(torre) = ? AND activo = 1"
                        cursor.execute(query, (torre.strip().lower(),))
                    rows = cursor.fetchall()
                    conn.close()
                except Exception as sqlite_err:
                    logger.error(f"El fallback a la base de datos SQLite local también falló. Detalle: {sqlite_err}")
                    raise ValueError(f"Error al consultar la tabla UsuariosTCS en MySQL: {e}")
            else:
                raise ValueError(f"Error al consultar la tabla UsuariosTCS en MySQL: {e}")
    else:
        raise ValueError(f"Motor de base de datos no soportado en la aplicación unificada: {engine}")

    # Procesar filas y normalizar nombres y usuarios
    for row in rows:
        nombre = row[0]
        usuario = row[1]
        if nombre:
            users.add(_normalizar(nombre))
        if usuario:
            users.add(_normalizar(usuario))

    if not users:
        raise ValueError(
            f"No se encontraron usuarios activos para la torre '{torre}' en la base de datos de Django.\n"
            f"Por favor, configure los usuarios en la tabla UsuariosTCS."
        )

    logger.info(f"Se recuperaron exitosamente {len(users)} nombres/usuarios desde la base de datos de Django.")
    return users
