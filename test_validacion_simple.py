"""
Test simple de validación con logs detallados
"""
import requests
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

def crear_incidencia(tipo, lat, lon, descripcion):
    """Crea una incidencia"""
    payload = {
        "tipo": tipo,
        "descripcion": descripcion,
        "lat": lat,
        "lon": lon,
        "foto_url": None,
        "usuario_id": 1
    }
    response = requests.post(f"{BASE_URL}/api/incidencias/", json=payload)
    if response.status_code == 201:
        data = response.json()
        print(f"✓ Incidencia {data['id']} creada: tipo={tipo}, gravedad={data['gravedad']}")
        return data['id']
    else:
        print(f"✗ Error creando incidencia: {response.status_code}")
        print(response.text)
        return None

def validar_incidencia(inc_id):
    """Valida una incidencia"""
    response = requests.post(f"{BASE_URL}/api/incidencias/{inc_id}/validate")
    if response.status_code == 200:
        print(f"✓ Incidencia {inc_id} validada")
        return True
    else:
        print(f"✗ Error validando incidencia {inc_id}: {response.status_code}")
        print(response.text)
        return False

def verificar_rutas():
    """Verifica si se generaron rutas"""
    # Intentar con zona específica
    response = requests.get(f"{BASE_URL}/api/rutas/zona/oriental")
    if response.status_code == 200:
        data = response.json()
        rutas = data.get('rutas', [])
        if rutas:
            print(f"\n✓ ÉXITO: Se generaron {len(rutas)} ruta(s)")
            for ruta in rutas:
                print(f"  - Ruta {ruta['id']}: zona={data['zona']}, "
                      f"gravedad={ruta['suma_gravedad']}, camiones={ruta['camiones_usados']}")
            return True
        else:
            print("\n✗ FALLO: No se generaron rutas")
            return False
    else:
        print(f"\n✗ Error verificando rutas: {response.status_code}")
        return False

def main():
    print("="*60)
    print("TEST SIMPLE: Validación y Generación de Ruta")
    print("="*60)
    
    # Crear 6 incidencias en zona oriental (22 puntos total)
    print("\n1. Creando 6 incidencias...")
    incidencias = [
        ("animal_muerto", -0.92, -78.61, "Animal 1"),  # 5 puntos
        ("zona_critica", -0.921, -78.611, "Zona 1"),   # 3 puntos
        ("zona_critica", -0.922, -78.612, "Zona 2"),   # 3 puntos
        ("animal_muerto", -0.923, -78.613, "Animal 2"), # 5 puntos
        ("zona_critica", -0.924, -78.614, "Zona 3"),   # 3 puntos
        ("zona_critica", -0.925, -78.615, "Zona 4"),   # 3 puntos
    ]
    
    ids = []
    for tipo, lat, lon, desc in incidencias:
        inc_id = crear_incidencia(tipo, lat, lon, desc)
        if inc_id:
            ids.append(inc_id)
        time.sleep(0.5)
    
    print(f"\n✓ {len(ids)} incidencias creadas (suma esperada: 22 puntos)")
    print("  Umbral: 20 puntos")
    print("  22 > 20 = TRUE → DEBERÍA generar ruta")
    
    # Validar todas las incidencias
    print("\n2. Validando incidencias...")
    for inc_id in ids:
        validar_incidencia(inc_id)
        time.sleep(0.5)
    
    # Verificar si se generó la ruta
    print("\n3. Verificando rutas generadas...")
    time.sleep(1)  # Esperar un poco
    verificar_rutas()
    
    print("\n" + "="*60)
    print("IMPORTANTE: Revisa el terminal de uvicorn para ver los logs")
    print("Busca líneas que contengan:")
    print("  - 'Iniciando validación de incidencia'")
    print("  - 'Umbral zona oriental'")
    print("  - 'UMBRAL SUPERADO'")
    print("  - 'Generando nueva ruta'")
    print("="*60)

if __name__ == "__main__":
    main()
