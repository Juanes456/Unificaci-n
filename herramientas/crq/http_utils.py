import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3

# Deshabilitar advertencias de certificados no verificados en HTTPS
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def build_retry_session(timeout: int = 30, total_retries: int = 3) -> requests.Session:
    session = requests.Session()
    session.verify = False  # Desactivar verificación de SSL para compatibilidad con VPN/proxies corporativos

    retry = Retry(
        total=total_retries,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
        raise_on_status=False,
    )

    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    session.request_timeout = timeout
    return session
