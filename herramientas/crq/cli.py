from __future__ import annotations

import html
import logging
from html.parser import HTMLParser
from pathlib import Path

import pandas as pd

from .config import load_config
from .exceptions import ApiError, AuthenticationError, ConfigError, DataValidationError
from .helix_client import HelixClient
from .processor import process_crq
from .report import build_summary, export_excel
from .resi_client import ResiClient


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def get_text(self) -> str:
        return " ".join(p.strip() for p in self._parts if p.strip())


def _strip_html(value: str) -> str:
    try:
        parser = _TextExtractor()
        parser.feed(value)
        text = parser.get_text()
        return text if text else html.unescape(value).strip()
    except Exception:
        return html.unescape(value).strip()


_ALT_SUMMARY_FIELDS = [
    "Notes",
    "Description",
    "Detailed Description",
    "Work Info Summary",
    "WorkLog7",
    "z1D_ActivityDate_tab",
]


def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def run_crq(
    config_path: str | Path,
    date_from: str,
    date_to: str,
    output_dir: str | Path,
    log_level: str = "INFO",
) -> int:
    _configure_logging(log_level)
    logger = logging.getLogger("crq_portable")

    try:
        cfg = load_config(config_path)

        # Validar formato fechas
        from datetime import datetime

        fecha_inicio = datetime.strptime(date_from, "%Y-%m-%d")
        fecha_fin = datetime.strptime(date_to, "%Y-%m-%d")
        if fecha_inicio > fecha_fin:
            raise ConfigError("La fecha de inicio no puede ser mayor que la de fin.")

        helix_client = HelixClient(cfg.helix)

        # Paso 1: autenticar
        logger.info("Autenticando en Helix…")
        helix_client.authenticate()

        # Paso 2a: tareas
        logger.info("Consultando tareas TMS:Task (%s -> %s)…", date_from, date_to)
        tasks = helix_client.fetch_task_records(date_from, date_to)
        if not tasks:
            raise DataValidationError(
                f"Helix no devolvio tareas para el periodo {date_from} -> {date_to}."
            )
        df_tasks = pd.DataFrame(tasks)

        # Paso 2a.1: backfill summary placeholders
        _SUMMARY_PLACEHOLDERS = {
            "ver descripcion",
            "see description",
            "view description",
        }

        def _is_ph(v: object) -> bool:
            from .utils import normalize_text as _nt

            return isinstance(v, str) and _nt(v) in _SUMMARY_PLACEHOLDERS

        summary_col = "Summary"
        tasks_endpoint = cfg.helix.get("tasks", {}).get("endpoint", "")

        if summary_col in df_tasks.columns and "entryId" in df_tasks.columns:
            mask = df_tasks[summary_col].apply(_is_ph)
            for idx in df_tasks[mask].index:
                entry_id = df_tasks.at[idx, "entryId"]
                if not entry_id:
                    continue
                try:
                    full = helix_client.fetch_single_entry(
                        tasks_endpoint, str(entry_id)
                    )
                    real = str(full.get(summary_col, "")).strip()
                    if real and _is_ph(real):
                        real = ""
                    if not real:
                        for alt in _ALT_SUMMARY_FIELDS:
                            candidate = str(full.get(alt, "")).strip()
                            if candidate and not _is_ph(candidate):
                                real = _strip_html(candidate)
                                if real:
                                    break
                    if real:
                        real = _strip_html(real)
                    df_tasks.at[idx, summary_col] = (
                        real if (real and not _is_ph(real)) else ""
                    )
                except Exception:
                    df_tasks.at[idx, summary_col] = ""

        # Paso 2b: CRQ por IDs
        task_crq_id_col_raw = cfg.columns.get("task_crq_id", "RootRequestID")
        root_ids = list(
            {t.get(task_crq_id_col_raw) for t in tasks if t.get(task_crq_id_col_raw)}
        )

        # batch_size para evitar HTTP 431 (Request Header Fields Too Large)
        # Incrementamos a 20 para acelerar en escenarios donde no se sature el header.
        crq_records = helix_client.fetch_crq_by_ids(root_ids, batch_size=20)
        if not crq_records:
            raise DataValidationError("Helix devolvio respuesta vacia para CHG.")
        df_crq = pd.DataFrame(crq_records)

        # Paso 2c: usuarios pSeries desde RESI
        resi_cfg = cfg.raw.get("resi")
        if not resi_cfg:
            raise ConfigError("Falta la configuracion de RESI en config.yaml")

        resi_client = ResiClient(resi_cfg)
        try:
            pseries_users = resi_client.fetch_pseries_users()
        except Exception as exc:
            logger.error("Error al consultar usuarios en la base de datos de RESI: %s", exc)
            raise ApiError(
                f"No se pudo obtener la lista de usuarios de la base de datos para la torre seleccionada. "
                f"Por favor verifica tus credenciales de base de datos en config.yaml o las variables de entorno USR_SS y PASS_SS.\nDetalle: {exc}"
            )

        # Paso 3b: join
        crq_id_col = cfg.columns.get("crq_id", "Infrastructure Change ID")
        task_crq_id_col = cfg.columns.get("task_crq_id", "RootRequestID")
        categoria_col = cfg.columns.get("categoria", "z1D_Template_Name")

        CHG_EXTRA = {
            "Change Request Status": "estado_crq",
            "Submit Date": "fechaCreacionCrq_crq",
            "Actual End Date": "fechaCierreCrq_crq",
            "Scheduled Start Date": "fechaInicioProgramada_crq",
            "Scheduled End Date": "fechaFinProgramada_crq",
            "Company3": "filial_crq",
        }

        if (
            crq_id_col in df_crq.columns
            and task_crq_id_col in df_tasks.columns
            and categoria_col in df_crq.columns
        ):
            extra_available = [c for c in CHG_EXTRA if c in df_crq.columns]
            crq_cols = [crq_id_col, categoria_col] + extra_available
            crq_slim = (
                df_crq[crq_cols]
                .drop_duplicates(subset=[crq_id_col])
                .rename(columns={c: CHG_EXTRA[c] for c in extra_available})
            )
            df_merged = df_tasks.merge(
                crq_slim,
                left_on=task_crq_id_col,
                right_on=crq_id_col,
                how="left",
                suffixes=("", "_dup"),
            )
        else:
            df_merged = df_tasks

        # Paso 4: filtros
        # torre (por ahora fcunion): por compatibilidad lo pasamos pero aún no cambia filtros
        df_filtered = process_crq(
            df=df_merged,
            columns_cfg=cfg.columns,
            business_cfg=cfg.business,
            pseries_users=pseries_users,
            torre=cfg.business.get("torre"),
        )

        # Paso 5: renombrar + export
        rename_map: dict = cfg.output.get("rename_columns", {})
        if rename_map:
            df_filtered = df_filtered.rename(
                columns={
                    k: v for k, v in rename_map.items() if k in df_filtered.columns
                }
            )

        # Ordenar cronológicamente por la fecha de cierre de la tarea (cerroTareaSistema)
        if "cerroTareaSistema" in df_filtered.columns:
            try:
                temp_dates = pd.to_datetime(df_filtered["cerroTareaSistema"], errors="coerce")
                df_filtered = df_filtered.iloc[temp_dates.argsort()].copy()
            except Exception as e:
                logger.warning("No se pudo ordenar cronológicamente por cerroTareaSistema: %s", e)

        # Formatear columnas de fecha a formato humano (DD/MM/YYYY HH:MM:SS)
        date_columns = [
            "fechaCreacionCrq",
            "fechaCierreCrq",
            "fechaInicioProgramada",
            "fechaFinProgramada",
            "inicioTareaSistema",
            "cerroTareaSistema",
        ]
        for col in date_columns:
            if col in df_filtered.columns:
                try:
                    # Convertir a datetime de forma flexible
                    parsed_dates = pd.to_datetime(df_filtered[col], errors="coerce")
                    # Formatear como DD/MM/YYYY HH:MM:SS. Para los valores NaT/NaN se conserva None
                    df_filtered[col] = parsed_dates.dt.strftime("%d/%m/%Y %H:%M:%S").where(parsed_dates.notna(), None)
                except Exception as e:
                    logger.warning("No se pudo formatear la columna de fecha %s: %s", col, e)

        asignado_out = rename_map.get(
            cfg.columns.get("asignado", "Assignee"),
            cfg.columns.get("asignado", "Assignee"),
        )
        summary = build_summary(df_filtered, asignado_col=asignado_out)

        excluded_columns = cfg.output.get("exclude_columns", [])
        column_order = cfg.output.get("column_order", [])
        prefix = cfg.output.get("file_prefix", "CRQ_Report")

        output_path = export_excel(
            df_filtered=df_filtered,
            summary_df=summary,
            output_dir=Path(output_dir),
            excluded_columns=excluded_columns,
            column_order=column_order,
            file_prefix=prefix,
        )

        logger.info("Reporte generado: %s", output_path)

        return 0, str(output_path)

    except (ConfigError, AuthenticationError, ApiError, DataValidationError) as exc:
        logger.error("[ERROR] %s", exc)
        return 2, str(exc)
    except Exception as exc:
        logger.exception("[ERROR INESPERADO] %s", exc)
        return 3, str(exc)
