import requests
import json

API_URL = "http://localhost:8000"

print("=== TEST DEBUG: Generación de Ruta ===\n")

# 1. Crear incidencias
print("1. Creando 6 incidencias...")
ids = []
tipos = ["animal_muerto", "zona_critica", "zona_critica", "animal_muerto", "zona_critica", "zona_critica"]
for i, tipo in enumerate(tipos, 1):
    data = {
        "tipo": tipo,
        "descripcion": f"Test {i}",
        "lat": -0.92,
        "lon": -78.61,
        "usuario_id": 1
    }
    resp = requests.post(f"{API_URL}/api/incidencias", json=data)
    if resp.status_code == 200:
        inc = resp.json()
        ids.append(inc["id"])
        print(f"   ✓ Incidencia {inc['id']}: {tipo}, gravedad={inc['gravedad']}")
    else:
        print(f"   ✗ Error: {resp.text}")

print(f"\n2. Validando {len(ids)} incidencias...")
for i, inc_id in enumerate(ids, 1):
    resp = requests.post(f"{API_URL}/api/incidencias/{inc_id}/validate")
    if resp.status_code == 200:
        result = resp.json()
        if result.get("ruta_generada"):
            print(f"   🎉 RUTA GENERADA en incidencia #{inc_id}: Ruta ID={result['ruta_generada']['id']}")
            break
        else:
            print(f"   ✓ Incidencia {inc_id} validada (sin ruta)")
    else:
        print(f"   ✗ Error validando {inc_id}: {resp.status_code} - {resp.text[:200]}")

print("\n3. Verificando rutas generadas...")
resp = requests.get(f"{API_URL}/api/rutas")
if resp.status_code == 200:
    rutas = resp.json()
    print(f"   Total de rutas: {len(rutas)}")
    for ruta in rutas:
        print(f"   - Ruta {ruta['id']}: {ruta['zona']}, estado={ruta['estado']}, gravedad={ruta['suma_gravedad']}")
else:
    print(f"   ✗ Error: {resp.text}")

print("\nDone!")
