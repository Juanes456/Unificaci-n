from __future__ import annotations

import json
import logging
import os
import re
import unicodedata
from typing import Any, Dict, Set

import requests

from .exceptions import ApiError
from .http_utils import build_retry_session
from .utils import extract_path, normalize_set

logger = logging.getLogger(__name__)


_CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "concatenacion_portable", "config.json"
)
if not os.path.exists(_CONFIG_FILE):
    _CONFIG_FILE = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "concatenacion", "config.json"
    )

_CONFIG_DEFAULTS = {
    "base_url": "http://10.8.150.90/",
    "endpoint": "api/reporte-consumos/reporte-consumos-pseries/",
    "user_field": "user",
    "torre": "Base de datos",
    "results_path": None,
    "headers": {},
    "params": {},
}


def _load_config() -> dict:
    if os.path.exists(_CONFIG_FILE):
        try:
            with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
                return {**_CONFIG_DEFAULTS, **json.load(f)}
        except Exception:
            pass
    return _CONFIG_DEFAULTS.copy()


_cfg = _load_config()


def _normalizar(valor: str) -> str:
    s = str(valor).strip().lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"\s+", " ", s)
    return s


class ResiClient:
    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        if config is None:
            config = _cfg

        self.config = config
        timeout = int(config.get("timeout", 30))
        retries = int(config.get("retries", 3))
        self.session = build_retry_session(timeout=timeout, total_retries=retries)
        self.base_url = str(config.get("base_url", "")).rstrip("/")

    def fetch_pseries_users(self) -> Set[str]:
        use_django_api = self.config.get("use_django_api", True)
        if use_django_api:
            try:
                import django_db_helper
                api_url = self.config.get("django_api_url", "http://127.0.0.1:8000/")
                ui_torre = os.environ.get("UNIFICADA_CRQ_UI_TORRE", "").strip()
                if not ui_torre:
                    ui_torre = self.config.get("torre", "pSeries")
                logger.info("Cargando usuarios de la torre '%s' desde la API de Django...", ui_torre)
                return django_db_helper.get_users_from_api(
                    api_url=api_url,
                    torre=ui_torre
                )
            except Exception as exc:
                logger.error("Error al consultar usuarios desde el helper de Django API: %s", exc)
                raise ApiError(
                    f"No se pudo obtener la lista de usuarios de la API para la torre seleccionada.\nDetalle: {exc}"
                )

        # Si está configurado para usar la base de datos Django dinámicamente
        use_django_db = self.config.get("use_django_db", False)
        if use_django_db:
            try:
                import django_db_helper
                ui_torre = os.environ.get("UNIFICADA_CRQ_UI_TORRE", "").strip()
                if not ui_torre:
                    ui_torre = self.config.get("torre", "pSeries")
                logger.info("Cargando usuarios de la torre '%s' desde la base de datos de Django...", ui_torre)
                return django_db_helper.get_users_from_db(
                    db_config=self.config.get("db", {}),
                    torre=ui_torre
                )
            except Exception as exc:
                logger.error("Error al consultar usuarios desde el helper de Django DB: %s", exc)
                raise ApiError(
                    f"No se pudo obtener la lista de usuarios de la base de datos para la torre seleccionada.\nDetalle: {exc}"
                )

        if "db" in self.config:
            db_cfg = self.config["db"]
            host = db_cfg.get("host", "10.8.150.90")
            port = int(db_cfg.get("port", 3306))
            name = db_cfg.get("name", "reporte_de_consumos")
            
            raw_user = db_cfg.get("user", "")
            raw_password = db_cfg.get("password", "")
            
            def _resolve_env(val: Any) -> str:
                if not isinstance(val, str):
                    return str(val)
                m = re.search(r"\{\{\s*env\['([^']+)'\](?:\s+or\s+'([^']*)')?\s*\}\}", val)
                if m:
                    env_var = m.group(1)
                    default_val = m.group(2) or ""
                    return os.environ.get(env_var, default_val)
                return val

            user = _resolve_env(raw_user)
            password = _resolve_env(raw_password)
            
            query_template = db_cfg.get("query", "SELECT username FROM users_user WHERE torre = '{torre}'")
            ui_torre = os.environ.get("UNIFICADA_CRQ_UI_TORRE", "").strip()

            if not ui_torre or ui_torre.lower() == "todos":
                query = "SELECT username FROM users_user WHERE torre IN ('Base de datos', 'pSeries', 'Malla de operaciones', 'Wintel')"
            else:
                if "{torre}" in query_template:
                    query = query_template.format(torre=ui_torre)
                elif "torre = 'Pseries'" in query_template:
                    query = query_template.replace("torre = 'Pseries'", f"torre = '{ui_torre}'")
                elif "torre = 'pseries'" in query_template:
                    query = query_template.replace("torre = 'pseries'", f"torre = '{ui_torre}'")
                else:
                    query = query_template

            logger.info("Conectando directamente a la base de datos MySQL de RESI en %s:%s...", host, port)
            try:
                import pymysql
            except ImportError:
                import subprocess
                import sys
                logger.info("Librería pymysql no encontrada. Intentando instalar pymysql...")
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "pymysql"])
                    import pymysql
                except Exception as e:
                    raise ApiError(
                        f"No se pudo instalar la librería pymysql automáticamente: {e}. "
                        "Por favor, instala la librería manualmente ejecutando: pip install pymysql"
                    )

            try:
                conn = pymysql.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    database=name,
                    charset="utf8mb4",
                    connect_timeout=10
                )
                try:
                    with conn.cursor() as cursor:
                        cursor.execute(query)
                        rows = cursor.fetchall()
                        users = [str(row[0]).strip() for row in rows if row[0] is not None]
                finally:
                    conn.close()
            except Exception as exc:
                raise ApiError(
                    f"Error de conexión directa a la base de datos MySQL: {exc}"
                )

            normalized_users = normalize_set(users)
            logger.info("Usuarios pSeries obtenidos de la Base de Datos: %s", len(normalized_users))
            return normalized_users

        users_cfg = self.config.get("users", self.config)

        endpoint = users_cfg.get("endpoint")
        if not endpoint:
            raise ApiError("Configuración de RESI inválida (falta endpoint y db config)")
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        headers = users_cfg.get("headers", {})
        params = users_cfg.get("params", {})
        results_path = users_cfg.get("results_path")
        user_field = users_cfg.get("user_field")

        try:
            resp = self.session.get(url, headers=headers, params=params, verify=False)
        except requests.RequestException as exc:
            raise ApiError(
                f"No se pudo conectar con RESI en {url}. Verifica red o SSL."
            ) from exc

        if resp.status_code >= 400:
            raise ApiError(
                f"Error consultando usuarios pSeries en RESI. HTTP {resp.status_code}: {resp.text[:300]}"
            )

        try:
            body = resp.json()
        except ValueError as exc:
            raise ApiError("La respuesta de RESI no es JSON válido.") from exc

        payload = extract_path(body, results_path) if results_path else body

        if not isinstance(payload, list):
            raise ApiError("La respuesta de RESI no es una lista de usuarios.")

        if user_field:
            users = [
                item.get(user_field)
                for item in payload
                if isinstance(item, dict) and item.get(user_field)
            ]
        else:
            users = payload

        normalized_users = normalize_set(users)
        logger.info("Usuarios pSeries obtenidos de RESI: %s", len(normalized_users))
        return normalized_users
