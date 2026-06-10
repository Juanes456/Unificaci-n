from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .exceptions import ConfigError


@dataclass
class AppConfig:
    raw: Dict[str, Any]

    @property
    def helix(self) -> Dict[str, Any]:
        return self.raw.get("helix", {})

    @property
    def date_range(self) -> Dict[str, Any]:
        return self.raw.get("date_range", {})

    @property
    def columns(self) -> Dict[str, Optional[str]]:
        return self.raw.get("columns", {})

    @property
    def business(self) -> Dict[str, Any]:
        return self.raw.get("business", {})

    @property
    def output(self) -> Dict[str, Any]:
        return self.raw.get("output", {})


def _validate_config(data: Dict[str, Any]) -> None:
    required_top = ["helix", "columns", "business", "output"]
    missing_top = [k for k in required_top if k not in data]
    if missing_top:
        raise ConfigError(f"Faltan secciones obligatorias en config: {missing_top}")

    helix_required = ["base_url", "auth", "crq", "tasks", "people"]
    missing_helix = [k for k in helix_required if k not in data["helix"]]
    if missing_helix:
        raise ConfigError(f"Faltan claves en helix: {missing_helix}")

    auth_required = ["endpoint", "username", "password"]
    missing_auth = [k for k in auth_required if k not in data["helix"]["auth"]]
    if missing_auth:
        raise ConfigError(f"Faltan claves en helix.auth: {missing_auth}")

    crq_required = ["endpoint"]
    missing_crq = [k for k in crq_required if k not in data["helix"]["crq"]]
    if missing_crq:
        raise ConfigError(f"Faltan claves en helix.crq: {missing_crq}")


def load_config(path: str | Path = "config.yaml") -> AppConfig:
    """Carga la configuracion desde YAML.

    Nota: busca rutas relativas en el directorio de trabajo actual (cwd).
    """

    config_path = Path(path)
    if not config_path.is_absolute():
        config_path = Path.cwd() / config_path

    if not config_path.exists():
        raise ConfigError(f"No existe el archivo de configuracion: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if not isinstance(data, dict):
        raise ConfigError("El archivo de configuracion debe ser un objeto YAML.")

    defaults = {
        "helix": {},
        "resi": {},
        "columns": {},
        "business": {},
        "output": {},
        "date_range": {},
    }
    for k, v in defaults.items():
        if k not in data:
            data[k] = v

    try:
        _validate_config(data)
    except ConfigError as e:
        # Permitir avanzar si solo se usan partes
        print(f"[ADVERTENCIA] Configuracion incompleta: {e}")

    return AppConfig(raw=data)
