"""
Script para probar los endpoints de rutas actualizados
"""
import requests
import json

BASE_URL = "http://localhost:8081"

def login():
    """Login como admin"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Login exitoso: {data['username']}")
        return data['access_token']
    else:
        print(f"❌ Error en login: {response.status_code}")
        print(response.text)
        return None

def test_get_ruta(token, ruta_id):
    """Probar GET /api/rutas/{id}"""
    print(f"\n🔍 Probando GET /api/rutas/{ruta_id}")
    response = requests.get(
        f"{BASE_URL}/api/rutas/{ruta_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Ruta obtenida exitosamente")
        print(f"   - ID: {data['id']}")
        print(f"   - Zona: {data['zona']}")
        print(f"   - Estado: {data['estado']}")
        print(f"   - Puntos: {len(data.get('puntos', []))}")
        print(f"   - Polyline: {'✅ Presente' if data.get('polyline') else '⚠️ Vacío (esperado por ahora)'}")
        
        # Mostrar primer punto como ejemplo
        if data.get('puntos'):
            punto = data['puntos'][0]
            print(f"\n   Ejemplo de punto:")
            print(f"   - Tipo: {punto.get('tipo_punto')}")
            print(f"   - Secuencia: {punto.get('secuencia')}")
            if punto.get('incidencia_id'):
                print(f"   - Incidencia ID: {punto.get('incidencia_id')}")
                print(f"   - Tipo incidencia: {punto.get('tipo_incidencia')}")
                print(f"   - Gravedad: {punto.get('gravedad')}")
        
        return data
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None

def test_get_ruta_detalles(token, ruta_id):
    """Probar GET /api/rutas/{id}/detalles"""
    print(f"\n🔍 Probando GET /api/rutas/{ruta_id}/detalles")
    response = requests.get(
        f"{BASE_URL}/api/rutas/{ruta_id}/detalles",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Detalles obtenidos exitosamente")
        print(f"   - Ruta ID: {data['ruta']['id']}")
        print(f"   - Zona: {data['ruta']['zona']}")
        print(f"   - Incidencias: {len(data.get('incidencias', []))}")
        print(f"   - Puntos: {len(data.get('puntos', []))}")
        
        # Mostrar primera incidencia como ejemplo
        if data.get('incidencias'):
            inc = data['incidencias'][0]
            print(f"\n   Ejemplo de incidencia:")
            print(f"   - ID: {inc.get('id')}")
            print(f"   - Tipo: {inc.get('tipo')}")
            print(f"   - Gravedad: {inc.get('gravedad')}")
            print(f"   - Estado: {inc.get('estado')}")
            print(f"   - Ubicación: [{inc.get('lat')}, {inc.get('lon')}]")
        
        return data
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None

def listar_rutas(token):
    """Listar rutas disponibles para prueba"""
    print("\n📋 Listando rutas disponibles...")
    response = requests.get(
        f"{BASE_URL}/api/rutas/zona/oriental",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get('rutas'):
            print(f"✅ Encontradas {len(data['rutas'])} rutas en zona oriental")
            return data['rutas'][0]['id'] if data['rutas'] else None
        else:
            print("⚠️ No hay rutas en zona oriental")
            return None
    else:
        print(f"❌ Error al listar rutas: {response.status_code}")
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("PRUEBA DE ENDPOINTS DE RUTAS ACTUALIZADOS")
    print("=" * 60)
    
    # Login
    token = login()
    if not token:
        print("\n❌ No se pudo obtener token. Verifica que el servidor esté corriendo.")
        exit(1)
    
    # Obtener una ruta para probar
    ruta_id = listar_rutas(token)
    
    if not ruta_id:
        print("\n⚠️ No hay rutas disponibles para probar.")
        print("💡 Genera una ruta primero con POST /api/rutas/generar/oriental")
        exit(0)
    
    print(f"\n🎯 Usando ruta ID: {ruta_id}")
    
    # Probar ambos endpoints
    test_get_ruta(token, ruta_id)
    test_get_ruta_detalles(token, ruta_id)
    
    print("\n" + "=" * 60)
    print("✅ PRUEBAS COMPLETADAS")
    print("=" * 60)
