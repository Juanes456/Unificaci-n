from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class TorreOption:
    value: str
    label: str


def get_torre_options() -> List[TorreOption]:
    # fcunion por ahora
    return [
        TorreOption(value="fcunion", label="fcunion"),
    ]
