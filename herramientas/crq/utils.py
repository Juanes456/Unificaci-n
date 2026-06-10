from __future__ import annotations

import re
from typing import Any, Iterable


def normalize_text(v: Any) -> str:
    """Normaliza texto para comparaciones robustas."""
    if v is None:
        return ""
    s = str(v).strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def normalize_set(values: Any) -> set[str]:
    if values is None:
        return set()
    if isinstance(values, (set, list, tuple)):
        return {normalize_text(v) for v in values if v is not None}
    if isinstance(values, str):
        # separadores posibles
        parts = [p for p in re.split(r"[,;|]", values) if p.strip()]
        if len(parts) <= 1:
            return {normalize_text(values)}
        return {normalize_text(p) for p in parts}
    return set()


def extract_path(obj: Any, path: str | None) -> Any:
    """Extrae obj[path] si path tiene formato 'a.b.c'. Si path es None, devuelve obj."""
    if path is None:
        return obj
    if not isinstance(path, str) or not path.strip():
        return obj

    cur = obj
    for part in path.split("."):
        if cur is None:
            return None
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur


def safe_to_int(v: Any, default: int | None = None) -> int | None:
    try:
        if v is None:
            return default
        return int(str(v).strip())
    except Exception:
        return default
