from __future__ import annotations

import logging
from typing import Any, Dict

import pandas as pd

from .exceptions import DataValidationError
from .utils import normalize_set, normalize_text

logger = logging.getLogger(__name__)


def _required_columns(columns_cfg: Dict[str, str | None]) -> Dict[str, str | None]:
    required = {
        "categoria": columns_cfg.get("categoria"),
        "tarea": columns_cfg.get("tarea"),
        "motivo_estado": columns_cfg.get("motivo_estado"),
        "asignado": columns_cfg.get("asignado"),
    }
    for key in required:
        if not required[key]:
            raise DataValidationError(f"Falta mapear la columna obligatoria: {key}")
    return required


def _normalize_category_set(value: Any) -> set[str]:
    if isinstance(value, list):
        return {normalize_text(v) for v in value}
    if isinstance(value, str):
        return {normalize_text(value)}
    return set()


def _resolve_tipo_cambio(
    normalized_category: str,
    cats_aprovisionamiento: set[str],
    cats_consejo: set[str],
) -> str | None:
    if normalized_category in cats_aprovisionamiento:
        return "Aprovisionamiento"
    if normalized_category in cats_consejo:
        return "Consejo"
    return None


def process_crq(
    df: pd.DataFrame,
    columns_cfg: Dict[str, str | None],
    business_cfg: Dict[str, Any],
    pseries_users: set[str],
    *,
    torre: str | None = None,
) -> pd.DataFrame:
    if df.empty:
        raise DataValidationError("La consulta no devolvio registros.")

    cols = _required_columns(columns_cfg)
    missing_in_df = [c for c in cols.values() if c not in df.columns]
    if missing_in_df:
        raise DataValidationError(f"Faltan columnas en el DataFrame: {missing_in_df}")

    cats_aprovisionamiento = _normalize_category_set(
        business_cfg.get(
            "category_aprovisionamiento",
            [
                "Cambio en Produccion.Manual.Estandar.Aprovisionamiento_pSeries.Riesgo =1",
                "Cambio en Produccion.Banistmo.Estandar.Regional.Plataformas Distribuidas.Aprovisionamiento.Wintel Linux/Virtual",
                "Cambio en Produccion.Manual.Estandar.Aprovisionamiento_Sterling.Riesgo =1",
                "Paso a ambientes no productivos - Plataformas centrales - Aprovisionamiento Administrativa X86",
                "Paso a ambientes no productivos - Plataformas centrales - Aprovisionamiento X86",
                "Cambio en Produccion.Manual.Estandar.Aprovisionamiento_X86.Riesgo =1",
                "Cambio en Produccion.Manual.Estandar.Aprovisionamiento_Orquestacion - X86.Riesgo1",
                "Cambio en Produccion.Manual.Estandar.Aprovisionamiento_Portales.Riesgo =1",
                "Paso a ambientes no productivos - Plataformas centrales - Aprovisionamiento Orquestacion x86",
                "Cambio en Produccion.Manual.Estandar.Aprovisionamiento_P2V.Riesgo =1",
                "Gestion de Plataforma Banistmo - Aprovisionamiento Ambientes No Productivos Niquia",
            ],
        )
    )

    cats_consejo = _normalize_category_set(
        business_cfg.get(
            "category_consejo",
            "Cambio en Produccion.Manual.Programado.General.Riesgo >=3",
        )
    )

    # Agregar soporte para categorías de la UI unificada para que no se filtren
    ui_supported_aprovisionamiento = [
        "Cambio en Produccion.Manual.Estandar.Aprovisionamiento_pSeries.Riesgo =1",
        "Cambio en Produccion.Manual.Estandar.Aprovisionamiento_Eliminacion - Bases de Datos.Riesgo =1",
    ]
    ui_supported_consejo = [
        "Cambio en Produccion.Manual.Programado.General.Riesgo >=3",
        "Cambio en Produccion.Manual.Emergencia.General.Riesgo >=3",
        "Cambio en Produccion.Manual.Agil.General.Riesgo <=2",
        "Cambio en Produccion.Manual.Estandar.Procesos Malla_Mantenimiento.Riesgo =1",
    ]
    for c in ui_supported_aprovisionamiento:
        cats_aprovisionamiento.add(normalize_text(c))
    for c in ui_supported_consejo:
        cats_consejo.add(normalize_text(c))

    allowed_tasks = normalize_set(
        business_cfg.get(
            "allowed_tasks",
            [
                "Ejecutar Cambio pSeries",
                "Ejecutar Cambio",
                "Ejecutar Cambio TI",
                "Implementación Cambio",
                "Ejecutar cambio en produccion",
            ],
        )
    )

    filial_requerida = normalize_text(
        business_cfg.get("filial_requerida", "Bancolombia")
    )
    filial_col = columns_cfg.get("filial")

    status_translations = business_cfg.get("status_translations", {})
    success_reasons = normalize_set(
        business_cfg.get("success_reasons", ["Satisfactorio"])
    )

    categoria_col = cols["categoria"]
    tarea_col = cols["tarea"]
    motivo_col = cols["motivo_estado"]
    asignado_col = cols["asignado"]

    logger.info("Registros iniciales: %s", len(df))

    crq_status_translations = business_cfg.get("crq_status_translations", {})
    estado_col = None
    # Si la config mapea estado, aplicamos traduccion (opcional)
    for k in ("estado", "estado_crq"):
        if k in columns_cfg and columns_cfg[k]:
            estado_col = columns_cfg[k]
            break

    if crq_status_translations and estado_col and estado_col in df.columns:
        df = df.copy()
        df[estado_col] = df[estado_col].map(
            lambda v: crq_status_translations.get(str(v), v) if pd.notna(v) else v
        )

    if status_translations:
        df = df.copy()
        df[motivo_col] = df[motivo_col].map(
            lambda v: status_translations.get(str(v), v) if pd.notna(v) else v
        )

    df["_cat_norm"] = df[categoria_col].map(normalize_text)
    df["tipoDeCambio"] = df["_cat_norm"].map(
        lambda c: _resolve_tipo_cambio(c, cats_aprovisionamiento, cats_consejo)
    )
    before = len(df)
    df = df[df["tipoDeCambio"].notna()].copy()
    logger.info("Filtro categoria exacta: %s -> %s", before, len(df))

    # === Filtro adicional desde UI ===
    # Si `UNIFICADA_CRQ_UI_CATEGORIA` está definido, filtramos por las categorías
    # seleccionadas (separadas por punto y coma `;`).
    import os

    ui_categoria = os.environ.get("UNIFICADA_CRQ_UI_CATEGORIA", "").strip()
    if ui_categoria and ui_categoria.lower() != "todos":
        cats_to_filter = [normalize_text(c.strip()) for c in ui_categoria.split(";") if c.strip()]
        if cats_to_filter:
            before_ui = len(df)
            df = df[df["_cat_norm"].isin(cats_to_filter)].copy()
            logger.info(
                "Filtro categoria UI: %s -> %s (categorias=%s)",
                before_ui,
                len(df),
                ui_categoria,
            )

    df["_tarea_norm"] = df[tarea_col].map(normalize_text)

    # Definir listas de tareas por categoría
    cat_elim_db = normalize_text("Cambio en Produccion.Manual.Estandar.Aprovisionamiento_Eliminacion - Bases de Datos.Riesgo =1")
    cat_malla = normalize_text("Cambio en Produccion.Manual.Estandar.Procesos Malla_Mantenimiento.Riesgo =1")

    # Lista común base
    allowed_tasks_base = set(allowed_tasks)

    # Tarea de implementación para agregar a todas excepto eliminación
    task_implementacion = normalize_text("Implementación del Cambio")
    task_tarea1 = normalize_text("Tarea 1: Implementación del Cambio")
    task_tarea2 = normalize_text("Tarea 2: Implementación del Cambio")

    # Tareas específicas para malla
    tasks_malla = {
        normalize_text("Ejecutar Cambio Procesos Malla"),
        normalize_text("Validar Cambio Procesos Malla")
    }

    # Tareas específicas para eliminación
    tasks_elim = {
        normalize_text("Eliminar Motor BD")
    }

    def _is_task_allowed_for_row(row):
        cat_norm = row["_cat_norm"]
        task_norm = row["_tarea_norm"]

        # Tareas permitidas para esta fila
        allowed_for_row = allowed_tasks_base.copy()

        if cat_norm == cat_elim_db:
            allowed_for_row.update(tasks_elim)
        else:
            allowed_for_row.add(task_implementacion)
            allowed_for_row.add(task_tarea1)
            allowed_for_row.add(task_tarea2)

        if cat_norm == cat_malla:
            allowed_for_row.update(tasks_malla)

        return task_norm in allowed_for_row

    before = len(df)
    df = df[df.apply(_is_task_allowed_for_row, axis=1)].copy()
    logger.info("Filtro tarea dinámico por categoría: %s -> %s", before, len(df))

    df["_motivo_norm"] = df[motivo_col].map(normalize_text)
    before = len(df)
    df = df[df["_motivo_norm"].isin(success_reasons)].copy()
    logger.info("Filtro motivo estado: %s -> %s", before, len(df))

    if filial_col and filial_col in df.columns:
        before = len(df)
        df = df[df[filial_col].map(normalize_text) == filial_requerida].copy()
        logger.info("Filtro filial (%s): %s -> %s", filial_requerida, before, len(df))

    # Modo degradado: si no hay lista de usuarios, no abortamos.
    if not pseries_users:
        logger.warning(
            "Catálogo de usuarios vacío: omitiendo filtro por columna asignado."
        )
    else:
        df["_asignado_norm"] = df[asignado_col].map(normalize_text)

        import os
        ui_torre = os.environ.get("UNIFICADA_CRQ_UI_TORRE", "").strip()
        ui_torre_norm = normalize_text(ui_torre) if ui_torre else ""

        before = len(df)
        df = df[df["_asignado_norm"].isin(pseries_users)].copy()
        logger.info(
            "Filtro asignado estricto por torre %s (usuarios válidos): %s -> %s",
            ui_torre or "Todos",
            before,
            len(df),
        )

    df = df.drop(columns=[c for c in df.columns if c.startswith("_")])
    return df
