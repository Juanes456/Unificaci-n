from __future__ import annotations

import logging
from typing import Any, Dict, List

from requests.auth import HTTPBasicAuth

from .exceptions import ApiError, AuthenticationError
from .http_utils import build_retry_session
from .utils import extract_path

logger = logging.getLogger(__name__)


class HelixClient:
    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        timeout = int(config.get("timeout", 30))
        retries = int(config.get("retries", 3))
        self.session = build_retry_session(timeout=timeout, total_retries=retries)
        self.base_url = str(config["base_url"]).rstrip("/")
        self.token: str | None = None
        self.basic_auth = False

        auth_cfg = self.config["auth"]
        if auth_cfg.get("basic_auth", False):
            self.session.auth = HTTPBasicAuth(
                auth_cfg["username"], auth_cfg["password"]
            )
            self.basic_auth = True

    @staticmethod
    def _normalize_record(item: Any) -> Dict[str, Any]:
        if not isinstance(item, dict):
            return {"value": item}

        values = item.get("values")
        if isinstance(values, dict):
            normalized: Dict[str, Any] = dict(values)
            entry_id = item.get("entryId")
            if entry_id is not None and "entryId" not in normalized:
                normalized["entryId"] = entry_id
            return normalized

        return item

    def authenticate(self) -> str:
        auth_cfg = self.config["auth"]
        endpoint = auth_cfg["endpoint"]
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        username_field = auth_cfg.get("username_field", "username")
        password_field = auth_cfg.get("password_field", "password")
        payload = {
            username_field: auth_cfg["username"],
            password_field: auth_cfg["password"],
        }

        send_as = auth_cfg.get("send_as", "json").lower()
        headers = auth_cfg.get("headers", {})

        if send_as == "form":
            resp = self.session.post(url, data=payload, headers=headers)
        else:
            resp = self.session.post(url, json=payload, headers=headers)

        if resp.status_code >= 400:
            raise AuthenticationError(
                f"Fallo autenticacion Helix. HTTP {resp.status_code}: {resp.text[:300]}"
            )

        token_path = auth_cfg.get("token_path", "token")
        token_prefix = auth_cfg.get("token_prefix", "Bearer")

        token = None
        try:
            body = resp.json()
            token = extract_path(body, token_path)
        except ValueError:
            token = resp.text.strip()

        if not token:
            raise AuthenticationError(
                "Autenticacion Helix exitosa, pero no se pudo extraer JWT."
            )

        self.token = str(token)
        self.session.headers.update({"Authorization": f"{token_prefix} {self.token}"})
        logger.info("Autenticacion Helix OK.")
        return self.token

    def fetch_crq_by_ids(
        self, root_ids: List[str], batch_size: int = 10
    ) -> List[Dict[str, Any]]:
        if not self.basic_auth and not self.token:
            self.authenticate()
        if not root_ids:
            return []

        crq_cfg = self.config["crq"]
        endpoint = crq_cfg["endpoint"]
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        fields = crq_cfg.get("fields", "")

        id_field = "Infrastructure Change ID"
        all_records: List[Dict[str, Any]] = []

        for i in range(0, len(root_ids), batch_size):
            chunk = root_ids[i : i + batch_size]
            # Para evitar "Request Header Fields Too Large" (431) en Helix/Arsys,
            # reducimos el tamaño del q enviando menos IDs por request.
            # Además evitamos q muy largo saturando headers/cookies.
            # Qualification line: valores deben ir con comillas dobles escapadas.
            # Usamos el formato simple Arsys: 'Campo' = "valor".
            q = " OR ".join([f"'{id_field}' = \"{rid}\"" for rid in chunk])
            params: Dict[str, Any] = {"q": q, "limit": min(len(chunk) * 2, 2000)}
            if fields:
                params["fields"] = fields

            resp = self.session.get(url, params=params)
            if resp.status_code >= 400:
                raise ApiError(
                    f"Error consultando {endpoint}. HTTP {resp.status_code}: {resp.text[:300]}"
                )

            try:
                body = resp.json()
            except ValueError as exc:
                raise ApiError(f"Respuesta no JSON de {endpoint}.") from exc

            results_path = crq_cfg.get("results_path")
            chunk_raw = extract_path(body, results_path) if results_path else body
            if isinstance(chunk_raw, list):
                all_records.extend([self._normalize_record(item) for item in chunk_raw])

            logger.debug(
                "%s batch %d-%d: %d registros",
                endpoint,
                i,
                i + len(chunk),
                len(chunk_raw or []),
            )

        logger.info("Total CRQ recuperados por ID: %s", len(all_records))
        return all_records

    def fetch_task_records(self, date_from: str, date_to: str) -> List[Dict[str, Any]]:
        if not self.basic_auth and not self.token:
            self.authenticate()

        tasks_cfg = self.config["tasks"]
        date_field = tasks_cfg.get("task_date_field", "End Time")
        # Arsys/Helix tiende a rechazar qualification lines si el formato no coincide.
        # Para mejorar compatibilidad usamos formato ISO 8601 completo (00:00:00).
        # Si tu backend espera solo YYYY-MM-DD, puedes revertir a la version anterior.
        # Usar formato YYYY-MM-DD únicamente (Arsys suele validar el tipo de dato exacto).
        # Si el backend requiere hora, se ajusta luego, pero primero dejamos el formato simple.
        date_from_iso = f"{date_from}"
        date_to_iso = f"{date_to}"

        q_filter = (
            f"'{{date_field}}' >= \"{date_from_iso}\" "
            f"AND '{{date_field}}' <= \"{date_to_iso}\" "
            f"AND 'Status' = \"Closed\""
        ).format(date_field=date_field)

        records = self._fetch_paged(tasks_cfg, extra_params={"q": q_filter})
        logger.info("Total tareas recuperadas de TMS:Task: %s", len(records))
        return records

    def fetch_single_entry(self, endpoint: str, entry_id: str) -> Dict[str, Any]:
        if not self.basic_auth and not self.token:
            self.authenticate()

        url = f"{self.base_url}/{endpoint.lstrip('/')}/{entry_id}"
        resp = self.session.get(url)
        if resp.status_code >= 400:
            raise ApiError(
                f"Error consultando {url}. HTTP {resp.status_code}: {resp.text[:200]}"
            )

        try:
            item = resp.json()
        except ValueError as exc:
            raise ApiError(f"Respuesta no JSON de {url}.") from exc

        return self._normalize_record(item)

    def fetch_people(self) -> List[Dict[str, Any]]:
        if not self.basic_auth and not self.token:
            self.authenticate()
        records = self._fetch_paged(self.config["people"])
        logger.info("Total registros CTM:People recuperados: %s", len(records))
        return records

    def _fetch_paged(
        self,
        cfg: Dict[str, Any],
        extra_params: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:
        endpoint = cfg["endpoint"]
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        page_size = int(cfg.get("page_size", 100))
        max_pages = cfg.get("max_pages")
        max_records = cfg.get("max_records")
        results_path = cfg.get("results_path")

        params_base: Dict[str, Any] = dict(cfg.get("params", {}))
        if extra_params:
            params_base.update(extra_params)
        if cfg.get("fields"):
            params_base["fields"] = cfg["fields"]

        all_records: List[Dict[str, Any]] = []
        offset = 0
        pages_fetched = 0

        while True:
            params = dict(params_base)
            params["offset"] = offset
            params["limit"] = page_size

            resp = self.session.get(url, params=params)
            if resp.status_code >= 400:
                raise ApiError(
                    f"Error consultando {endpoint}. HTTP {resp.status_code}: {resp.text[:300]}"
                )

            try:
                body = resp.json()
            except ValueError as exc:
                raise ApiError(
                    f"La respuesta de {endpoint} no es JSON valido."
                ) from exc

            if results_path:
                chunk_raw = extract_path(body, results_path)
            else:
                chunk_raw = body

            if chunk_raw is None:
                chunk = []
            elif isinstance(chunk_raw, list):
                chunk = chunk_raw
            else:
                raise ApiError(
                    f"El bloque de resultados de {endpoint} no es una lista."
                )

            all_records.extend([self._normalize_record(item) for item in chunk])
            pages_fetched += 1
            logger.info("%s offset=%s: %s registros", endpoint, offset, len(chunk))

            if len(chunk) < page_size:
                break

            if (
                isinstance(max_records, int)
                and max_records > 0
                and len(all_records) >= max_records
            ):
                logger.warning(
                    "Se alcanzo max_records=%s en %s.", max_records, endpoint
                )
                all_records = all_records[:max_records]
                break

            if (
                isinstance(max_pages, int)
                and max_pages > 0
                and pages_fetched >= max_pages
            ):
                logger.warning("Se alcanzo max_pages=%s en %s.", max_pages, endpoint)
                break

            offset += page_size

        return all_records
