"""
Script de prueba para los nuevos endpoints de rutas
Ejecutar: python test_nuevos_endpoints.py
"""
import requests
import json
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:9000/api"
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

# Colores para consola
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_test(test_name):
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}🧪 TEST: {test_name}{Colors.END}")
    print(f"{Colors.CYAN}{'='*80}{Colors.END}")

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.YELLOW}ℹ️  {message}{Colors.END}")

def print_json(data, title="Response"):
    print(f"\n{Colors.CYAN}{title}:{Colors.END}")
    print(json.dumps(data, indent=2, ensure_ascii=False))

def login_admin():
    """Login como admin y obtener token"""
    print_test("Login Admin")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": ADMIN_USER, "password": ADMIN_PASS}
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        print_success(f"Login exitoso")
        return token
    else:
        print_error(f"Login fallido: {response.status_code}")
        return None

def test_historial_estado(token):
    """Test GET /api/rutas/historial/estado"""
    print_test("GET /api/rutas/historial/estado")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Todas las rutas
    print_info("Test 1: Todas las rutas")
    response = requests.get(f"{BASE_URL}/rutas/historial/estado", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print_success(f"Total rutas: {data['total']}")
        print_json(data, "Respuesta completa")
    else:
        print_error(f"Error: {response.status_code}")
        print(response.text)
    
    # Test 2: Solo rutas asignadas
    print_info("\nTest 2: Solo rutas asignadas")
    response = requests.get(
        f"{BASE_URL}/rutas/historial/estado?estado=asignada",
        headers=headers
    )
    if response.status_code == 200:
        data = response.json()
        print_success(f"Rutas asignadas: {data['total']}")
    else:
        print_error(f"Error: {response.status_code}")
    
    # Test 3: Rutas en ejecución
    print_info("\nTest 3: Rutas en ejecución")
    response = requests.get(
        f"{BASE_URL}/rutas/historial/estado?estado=en_ejecucion",
        headers=headers
    )
    if response.status_code == 200:
        data = response.json()
        print_success(f"Rutas en ejecución: {data['total']}")
    else:
        print_error(f"Error: {response.status_code}")
    
    # Test 4: Rutas completadas
    print_info("\nTest 4: Rutas completadas")
    response = requests.get(
        f"{BASE_URL}/rutas/historial/estado?estado=completada",
        headers=headers
    )
    if response.status_code == 200:
        data = response.json()
        print_success(f"Rutas completadas: {data['total']}")
    else:
        print_error(f"Error: {response.status_code}")

def test_calendario_activas(token):
    """Test GET /api/rutas/calendario/activas"""
    print_test("GET /api/rutas/calendario/activas")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Todas las rutas
    print_info("Test 1: Todas las rutas del calendario")
    response = requests.get(f"{BASE_URL}/rutas/calendario/activas", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print_success(f"Total días con rutas: {data['total_dias']}")
        print_success(f"Estadísticas: {data['estadisticas']}")
        print_json(data, "Respuesta completa")
    else:
        print_error(f"Error: {response.status_code}")
        print(response.text)
    
    # Test 2: Solo zona occidental
    print_info("\nTest 2: Solo zona occidental")
    response = requests.get(
        f"{BASE_URL}/rutas/calendario/activas?zona=occidental",
        headers=headers
    )
    if response.status_code == 200:
        data = response.json()
        print_success(f"Rutas zona occidental: {data['estadisticas']['total_rutas']}")
    else:
        print_error(f"Error: {response.status_code}")

def test_rutas_activas_conductor(token):
    """Test GET /api/conductores/{id}/rutas/activas"""
    print_test("GET /api/conductores/{id}/rutas/activas")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Obtener lista de conductores primero
    print_info("Obteniendo lista de conductores...")
    response = requests.get(f"{BASE_URL}/conductores/", headers=headers)
    if response.status_code == 200:
        conductores = response.json()
        if conductores:
            conductor_id = conductores[0]['id']
            print_success(f"Probando con conductor ID: {conductor_id}")
            
            # Test del endpoint
            response = requests.get(
                f"{BASE_URL}/conductores/{conductor_id}/rutas/activas",
                headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                print_success(f"Rutas activas del conductor: {data['total_rutas_activas']}")
                print_json(data, "Respuesta completa")
            else:
                print_error(f"Error: {response.status_code}")
                print(response.text)
        else:
            print_info("No hay conductores en el sistema")
    else:
        print_error(f"Error obteniendo conductores: {response.status_code}")

def test_ruta_navegacion(token):
    """Test GET /api/rutas/{id}/navegacion"""
    print_test("GET /api/rutas/{id}/navegacion")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Obtener una ruta primero
    print_info("Obteniendo lista de rutas...")
    response = requests.get(f"{BASE_URL}/rutas/historial/estado?limit=1", headers=headers)
    if response.status_code == 200:
        rutas = response.json()['rutas']
        if rutas:
            ruta_id = rutas[0]['id']
            print_success(f"Probando navegación con ruta ID: {ruta_id}")
            
            # Test del endpoint
            response = requests.get(
                f"{BASE_URL}/rutas/{ruta_id}/navegacion",
                headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                print_success(f"Navegación obtenida")
                print_json(data, "Respuesta completa")
            else:
                print_error(f"Error: {response.status_code}")
                print(response.text)
        else:
            print_info("No hay rutas en el sistema")
    else:
        print_error(f"Error obteniendo rutas: {response.status_code}")

def test_completar_incidencia(token):
    """Test POST /api/rutas/{id}/incidencia/{incidencia_id}/completar"""
    print_test("POST /api/rutas/{id}/incidencia/{incidencia_id}/completar")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Obtener una ruta con incidencias
    print_info("Buscando ruta con incidencias pendientes...")
    response = requests.get(
        f"{BASE_URL}/rutas/historial/estado?estado=en_ejecucion&limit=1",
        headers=headers
    )
    
    if response.status_code == 200:
        rutas = response.json()['rutas']
        if rutas:
            ruta_id = rutas[0]['id']
            print_success(f"Probando con ruta ID: {ruta_id}")
            
            # Obtener detalles de la ruta para conseguir una incidencia
            response = requests.get(
                f"{BASE_URL}/rutas/{ruta_id}/detalles",
                headers=headers
            )
            
            if response.status_code == 200:
                detalles = response.json()
                incidencias = [p for p in detalles['puntos'] if p['tipo_punto'] == 'incidencia']
                
                if incidencias:
                    incidencia_id = incidencias[0]['incidencia_id']
                    print_success(f"Intentando completar incidencia ID: {incidencia_id}")
                    
                    # Test del endpoint
                    response = requests.post(
                        f"{BASE_URL}/rutas/{ruta_id}/incidencia/{incidencia_id}/completar",
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        print_success("Incidencia marcada como completada")
                        print_json(data, "Respuesta completa")
                    else:
                        print_error(f"Error: {response.status_code}")
                        print(response.text)
                else:
                    print_info("La ruta no tiene incidencias")
            else:
                print_error(f"Error obteniendo detalles: {response.status_code}")
        else:
            print_info("No hay rutas en ejecución")
    else:
        print_error(f"Error: {response.status_code}")

def test_estadisticas_conductor(token):
    """Test GET /api/conductores/me/estadisticas"""
    print_test("GET /api/conductores/me/estadisticas")
    
    # Primero necesitamos un token de conductor
    print_info("Este endpoint requiere token de conductor")
    print_info("Saltando test por ahora (requiere login de conductor)")
    
    # Si quieres probarlo, necesitas:
    # 1. Login con credenciales de conductor
    # 2. Usar ese token para llamar al endpoint
    
    print_info("Ejemplo de uso:")
    print("""
    # Login conductor
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": "conductor_username", "password": "conductor_password"}
    )
    conductor_token = response.json()["access_token"]
    
    # Obtener estadísticas
    response = requests.get(
        f"{BASE_URL}/conductores/me/estadisticas",
        headers={"Authorization": f"Bearer {conductor_token}"}
    )
    """)

def run_all_tests():
    """Ejecutar todos los tests"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║                  🧪 TEST DE NUEVOS ENDPOINTS - RUTAS                       ║")
    print("║                        Backend Latacunga Clean                             ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}\n")
    
    print_info(f"Base URL: {BASE_URL}")
    print_info(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Login
    token = login_admin()
    if not token:
        print_error("No se pudo obtener token de admin. Abortando tests.")
        return
    
    # Ejecutar tests
    try:
        test_historial_estado(token)
        test_calendario_activas(token)
        test_rutas_activas_conductor(token)
        test_ruta_navegacion(token)
        test_completar_incidencia(token)
        test_estadisticas_conductor(token)
        
        # Resumen final
        print(f"\n{Colors.BOLD}{Colors.GREEN}")
        print("╔════════════════════════════════════════════════════════════════════════════╗")
        print("║                        ✅ TESTS COMPLETADOS                                ║")
        print("╚════════════════════════════════════════════════════════════════════════════╝")
        print(f"{Colors.END}\n")
        
    except Exception as e:
        print_error(f"Error durante los tests: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()
