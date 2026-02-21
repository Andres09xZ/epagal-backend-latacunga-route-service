"""Test de validaciones del endpoint POST /api/incidencias/"""
import urllib.request, json

BASE = "http://127.0.0.1:8000/api/incidencias/"
VALID_BASE = {
    "tipo": "animal_muerto",
    "descripcion": "Descripcion suficientemente larga para pasar validacion",
    "foto_url": "/fotos_incidencias/test.jpg",
    "lat": -0.9344,
    "lon": -78.6156,
    "usuario_id": 1,
}

CASOS = [
    ("descripcion < 10 chars",   {**VALID_BASE, "descripcion": "Corto"}),
    ("sin foto_url",              {k: v for k, v in VALID_BASE.items() if k != "foto_url"}),
    ("sin usuario_id",            {k: v for k, v in VALID_BASE.items() if k != "usuario_id"}),
    ("lat fuera de Latacunga",   {**VALID_BASE, "lat": 10.0}),
    ("lon fuera de Latacunga",   {**VALID_BASE, "lon": -70.0}),
    ("tipo invalido (bache)",     {**VALID_BASE, "tipo": "bache"}),
]

print("=== TEST 3: VALIDACIONES ===\n")
for label, body_dict in CASOS:
    body = json.dumps(body_dict).encode()
    req = urllib.request.Request(BASE, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req) as r:
            print(f"  [{label}] ❌ INESPERADO 2xx")
    except urllib.error.HTTPError as e:
        data = json.loads(e.read().decode())
        detail = data.get("detail", "")
        print(f"  [{label}] ✅ HTTP {e.code}")
        if isinstance(detail, list):
            for m in detail:
                loc = " -> ".join(str(x) for x in m.get("loc", []))
                print(f"       campo: {loc}")
                print(f"       msg:   {m.get('msg')}")
        else:
            print(f"       msg: {detail}")
        print()
