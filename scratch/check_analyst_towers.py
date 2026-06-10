import json
from concatenacion_portable.concatenacion import _normalizar

with open("usuarios_tcs_cache.json", "r", encoding="utf-8") as f:
    users_list = json.load(f)

analysts = [
    "JAVIER ALEXANDER LOPERA CARMONA",
    "JOSE IGNACIO PINZON BALLESTEROS",
    "AURA CRISTINA FLOREZ CHICA",
    "HECTOR FABIO CABRERA NUNEZ",
    "KEVIN ANDREE VIVEROS",
    "JOSE REINALDO PATINO CALDERON",
    "JULIAN DAVID ORTIZ IDROBO",
    "JAIRO MANUEL RAMIREZ MONROY",
    "WILDER ALBERTO BERRIO",
    "CARLOS ALBERTO REBAGE ALDANA",
    "WILLIAM ALEXANDER USECHE BELTRAN",
    "CARLOS ARTURO PACHECO CARDENAS",
]

for a in analysts:
    norm_a = _normalizar(a)
    found = False
    for u in users_list:
        if _normalizar(u.get("nombre", "")) == norm_a or _normalizar(u.get("usuario", "")) == norm_a:
            print(f"Analyst: '{a}' | Torre: {u.get('torre')} | Activo: {u.get('activo')}")
            found = True
            break
    if not found:
        print(f"Analyst: '{a}' | NOT FOUND IN CACHE")
