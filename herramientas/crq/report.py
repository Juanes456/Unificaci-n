from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List

import pandas as pd

logger = logging.getLogger(__name__)


def build_summary(df: pd.DataFrame, asignado_col: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    if asignado_col not in df.columns:
        # fallback: contar filas
        return pd.DataFrame({"asignado": ["(sin asignado)"], "conteo": [len(df)]})

    tipo_col = "tipoDeCambio" if "tipoDeCambio" in df.columns else None

    if tipo_col:
        grp = df.groupby([asignado_col, tipo_col]).size().reset_index(name="conteo")
        grp = grp.rename(columns={asignado_col: "asignado", tipo_col: "Tipo de cambio"})
        return grp

    grp = df.groupby([asignado_col]).size().reset_index(name="conteo")
    grp = grp.rename(columns={asignado_col: "asignado"})
    return grp


def export_excel(
    df_filtered: pd.DataFrame,
    summary_df: pd.DataFrame,
    output_dir: Path,
    excluded_columns: List[str] | None = None,
    column_order: List[str] | None = None,
    file_prefix: str = "CRQ_Report",
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    excluded_columns = excluded_columns or []
    column_order = column_order or []

    df_out = df_filtered.copy()
    for c in excluded_columns:
        if c in df_out.columns:
            df_out = df_out.drop(columns=[c])

    if column_order:
        cols_present = [c for c in column_order if c in df_out.columns]
        remaining = [c for c in df_out.columns if c not in cols_present]
        df_out = df_out[cols_present + remaining]

    from datetime import datetime

    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_path = output_dir / f"{file_prefix}_{ts}.xlsx"

    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        df_out.to_excel(writer, sheet_name="detalle_filtrado", index=False)
        summary_df.to_excel(writer, sheet_name="resumen", index=False)

    logger.info("Excel exportado: %s", out_path)
    return out_path
