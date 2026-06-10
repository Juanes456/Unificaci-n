from __future__ import annotations

import json
import os
import re
import threading
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
import requests


def _normalizar(valor: str) -> str:
    """Minúsculas, sin tildes/diacríticos y sin espacios extra."""
    s = str(valor).strip().lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"\s+", " ", s)
    return s


@dataclass(frozen=True)
class ConcatenacionConfig:
    api_url: str
    helix_user: str
    helix_password: str
    torre: str
    use_django_api: bool = True
    django_api_url: str = ""
    use_django_db: bool = False
    db: Dict[str, Any] = None


def load_concatenacion_config(config_path: str | Path) -> ConcatenacionConfig:
    config_path = Path(config_path)
    defaults = {
        "api_url": "https://bancolombia-restapi.onbmc.com",
        "helix_user": "",
        "helix_password": "",
        "torre": "Base de datos",
        "use_django_api": True,
        "django_api_url": "http://127.0.0.1:8000/",
        "use_django_db": False,
        "db": {},
    }

    data: Dict[str, Any] = {}
    if config_path.exists():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            # Si no se puede parsear, usamos defaults.
            data = {}

    merged = {**defaults, **data}
    return ConcatenacionConfig(
        api_url=str(merged["api_url"]),
        helix_user=str(merged.get("helix_user", "")),
        helix_password=str(merged.get("helix_password", "")),
        torre=str(merged.get("torre", "Base de datos")),
        use_django_api=bool(merged.get("use_django_api", True)),
        django_api_url=str(merged.get("django_api_url", "http://127.0.0.1:8000/")),
        use_django_db=bool(merged.get("use_django_db", False)),
        db=dict(merged.get("db", {})),
    )


class HelixClient:
    def __init__(self, cfg: ConcatenacionConfig):
        self.cfg = cfg
        self._jwt_token: str = ""
        self._lock = threading.Lock()

    def _helix_login(self) -> str:
        if not self.cfg.helix_user or not self.cfg.helix_password:
            raise ValueError(
                "Credenciales Helix no configuradas. "
                "Agregue 'helix_user' y 'helix_password' en config.json."
            )

        url = self.cfg.api_url.rstrip("/") + "/api/jwt/login"
        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
            'Accept': "*/*",
        }
        body = {
            "username": self.cfg.helix_user,
            "password": self.cfg.helix_password
        }
        resp = requests.post(
            url,
            headers=headers,
            data=body,
            timeout=15,
            verify=False,
        )
        resp.raise_for_status()
        try:
            token = resp.json().get("values", {}).get("Authentication-Token", "")
        except ValueError:
            token = ""
        if not token:
            token = resp.text.strip()
        if not token:
            raise ValueError("La API Helix no devolvió un token de autenticación.")
        self._jwt_token = token
        return token

    def get_tcs_users(self, torre: str = None) -> set[str]:
        # Cache thread-safe
        with self._lock:
            token = self._jwt_token or self._helix_login()

        def _fetch(tok: str):
            url = (
                self.cfg.api_url.rstrip("/")
                + "/api/arsys/v1/entry/CTM:People"
                + "?fields=values(Full+Name,Company)&limit=5000"
            )
            headers = {"Authorization": f"AR-JWT {tok}"}
            r = requests.get(url, headers=headers, timeout=30, verify=False)
            if r.status_code == 401:
                # Token expirado: renovar una vez
                new_tok = self._helix_login()
                headers["Authorization"] = f"AR-JWT {new_tok}"
                r = requests.get(url, headers=headers, timeout=30, verify=False)
            r.raise_for_status()
            return r.json()

        data = _fetch(token)
        entries = data if isinstance(data, list) else data.get("entries", [])

        target_torre = torre if torre is not None else self.cfg.torre
        torre_norm = _normalizar(target_torre)
        users: set[str] = set()

        for item in entries:
            vals = item.get("values", item) if isinstance(item, dict) else {}
            nombre = vals.get("Full Name") or vals.get("nombre", "")
            torre_val = vals.get("Company") or vals.get("torre", "")
            if nombre and _normalizar(torre_val) == torre_norm:
                users.add(_normalizar(nombre))

        if not users:
            raise ValueError(
                f"La API Helix no devolvió usuarios para la torre '{target_torre}'. "
                "Verifique credenciales y el filtro de torre en config.json."
            )

        return users


def _resumir_nombre(nombre: str, max_words: int = 3) -> str:
    palabras = re.split(r"[\s_\-]+", os.path.splitext(nombre)[0])
    palabras = [
        p for p in palabras if p and not p.lower().startswith("v") and not p.isdigit()
    ]
    return " ".join(palabras[:max_words])


def concat_filtra_export(
    file1: str | Path,
    file2: str | Path,
    *,
    config: ConcatenacionConfig,
    output_path: str | Path,
    resumen_filtro: str = "Gestión de usuarios bases de datos - Creación usuarios",  # default
    # Los filtros secundarios vienen del script original
    endpoint_tcs_col: str = "Analistadecapacidadasignado",
    col_resumen_wo: str = "ResumenWO",
    col_tipo_solicitud: str = "TipoSolicitud",
    col_descripcion: str = "Descripción",
    sheet_detail: str = "Registros Filtrados",
    sheet_summary: str = "Gestión BD - Creación Usuarios",
) -> Path:
    file1 = Path(file1)
    file2 = Path(file2)
    output_path = Path(output_path)

    df1 = pd.read_excel(file1)
    df2 = pd.read_excel(file2)

    # Concatenación (alinear columnas)
    all_cols = list(dict.fromkeys(list(df1.columns) + list(df2.columns)))
    df1 = df1.reindex(columns=all_cols)
    df2 = df2.reindex(columns=all_cols)
    df_concat = pd.concat([df1, df2], ignore_index=True)

    # Validación columnas requeridas (idéntico al script original)
    required_cols = {
        col_resumen_wo,
        col_tipo_solicitud,
        col_descripcion,
        endpoint_tcs_col,
    }
    missing = required_cols - set(df_concat.columns)
    if missing:
        raise ValueError(
            "Columnas requeridas no encontradas en los archivos: "
            + ", ".join(sorted(missing))
        )

    # Filtrado principal
    if resumen_filtro.lower() == "todos":
        df_filtered = df_concat.copy()
    else:
        df_filtered = df_concat[
            df_concat[col_resumen_wo].astype(str).str.lower().str.startswith(resumen_filtro.lower())
            | (df_concat[col_resumen_wo].astype(str) == resumen_filtro)
        ].copy()
    if "gesti" in resumen_filtro.lower() and "usuarios" in resumen_filtro.lower():
        df_filtered = df_filtered[
            df_filtered[col_tipo_solicitud].str.contains("Creación", na=False)
        ]
        df_filtered = df_filtered[
            df_filtered[col_descripcion]
            .astype(str)
            .str.lower()
            .str.contains(r"tipo solicitud.*cre", regex=True, na=False)
        ]

    # Limpieza columnas vacías excepto fechas (igual al script)
    fecha_columns = [
        "fechaCreacionPedido",
        "UltimaFechaModificacionPedido",
        "FechaCreacionWO",
        "FechaCierre",
        "FechaProgramadaInicio",
        "FechaProgramadaFin",
    ]
    columns_to_drop = [
        col
        for col in df_filtered.columns
        if df_filtered[col].isna().all() and col not in fecha_columns and col not in required_cols
    ]
    df_filtered = df_filtered.drop(columns=columns_to_drop)

    # Determinar la torre a consultar dinámicamente según el filtro seleccionado
    torre_target = config.torre  # default "Base de datos"
    if resumen_filtro:
        resumen_lower = resumen_filtro.lower()
        if resumen_lower == "todos":
            torre_target = "todos"
        elif "bases de datos" in resumen_lower or "base de datos" in resumen_lower:
            torre_target = "Base de datos"
        elif "respaldos" in resumen_lower or "servidores" in resumen_lower:
            torre_target = "Malla de operaciones"

    # Filtrado TCS BD vía API Django, Direct DB o Helix API
    if getattr(config, "use_django_api", True):
        import django_db_helper
        tcs_users = django_db_helper.get_users_from_api(
            api_url=getattr(config, "django_api_url", "http://127.0.0.1:8000/"),
            torre=torre_target
        )
    elif getattr(config, "use_django_db", False):
        import django_db_helper
        tcs_users = django_db_helper.get_users_from_db(
            db_config=getattr(config, "db", {}),
            torre=torre_target
        )
    else:
        helix = HelixClient(config)
        tcs_users = helix.get_tcs_users(torre=torre_target)

    df_tcs = df_filtered[
        df_filtered[endpoint_tcs_col].astype(str).apply(_normalizar).isin(tcs_users)
    ]

    # Resumen
    resumen = (
        df_tcs.groupby(endpoint_tcs_col)
        .size()
        .reset_index(name="Cantidad Creaciones")
        .sort_values("Cantidad Creaciones", ascending=False)
        .rename(columns={endpoint_tcs_col: "Analista"})
    )

    # Export
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df_tcs.to_excel(writer, sheet_name=sheet_detail, index=False)
        resumen.to_excel(writer, sheet_name=sheet_summary, index=False)

    return output_path


def default_output_name(file1: str | Path, file2: str | Path) -> str:
    r1 = _resumir_nombre(os.path.basename(str(file1)))
    r2 = _resumir_nombre(os.path.basename(str(file2)))
    return f"Resultado {r1} & {r2}.xlsx"
