"""
Test de endpoints con conductor Josue
Prueba todos los endpoints implementados
"""
import requests
import json
from datetime import datetime

# Configuración
BASE_URL = "http://10.52.239.59:9000/api"
CONDUCTOR_USERNAME = "josue"
CONDUCTOR_PASSWORD = "josue123"

# Colores para la consola
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_test(name, passed, details=""):
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{status} - {name}")
    if details:
        print(f"  {details}")
    print()

def print_section(name):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{name}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

# Variables globales
conductor_token = None
conductor_id = None
ruta_id = None

def test_login_conductor():
    """Test 1: Login de conductor"""
    global conductor_token, conductor_id
    
    print_section("TEST 1: Login Conductor")
    
    response = requests.post(
        f"{BASE_URL}/conductores/login",
        json={
            "username": CONDUCTOR_USERNAME,
            "password": CONDUCTOR_PASSWORD
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        conductor_token = data.get("access_token")
        conductor_id = data.get("conductor_id")
        
        print_test(
            "Login de conductor Josue",
            conductor_token is not None,
            f"Token: {conductor_token[:50]}...\nConductor ID: {conductor_id}"
        )
        return True
    else:
        print_test(
            "Login de conductor Josue",
            False,
            f"Status: {response.status_code}\nError: {response.text}"
        )
        return False

def test_rutas_activas_conductor():
    """Test 2: Obtener rutas activas del conductor"""
    global ruta_id
    
    print_section("TEST 2: Rutas Activas del Conductor")
    
    headers = {"Authorization": f"Bearer {conductor_token}"}
    response = requests.get(
        f"{BASE_URL}/conductores/{conductor_id}/rutas/activas",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        rutas = data.get("rutas", [])
        
        if rutas:
            ruta_id = rutas[0]["ruta_id"]
            print_test(
                "Obtener rutas activas",
                True,
                f"Total rutas: {data.get('total_rutas', 0)}\n"
                f"Primera ruta ID: {ruta_id}\n"
                f"Estado: {rutas[0].get('estado_ruta', 'N/A')}"
            )
        else:
            print_test(
                "Obtener rutas activas",
                True,
                f"{YELLOW}No hay rutas activas asignadas{RESET}"
            )
        return True
    else:
        print_test(
            "Obtener rutas activas",
            False,
            f"Status: {response.status_code}\nError: {response.text}"
        )
        return False

def test_estadisticas_conductor():
    """Test 3: Obtener estadísticas del conductor"""
    print_section("TEST 3: Estadísticas del Conductor")
    
    headers = {"Authorization": f"Bearer {conductor_token}"}
    response = requests.get(
        f"{BASE_URL}/conductores/me/estadisticas",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print_test(
            "Obtener estadísticas personales",
            True,
            f"Rutas completadas: {data.get('rutas_completadas', 0)}\n"
            f"Rutas en progreso: {data.get('rutas_en_progreso', 0)}\n"
            f"Incidencias completadas: {data.get('total_incidencias_completadas', 0)}\n"
            f"Tiempo promedio: {data.get('tiempo_promedio_ruta', 'N/A')}"
        )
        return True
    else:
        print_test(
            "Obtener estadísticas personales",
            False,
            f"Status: {response.status_code}\nError: {response.text}"
        )
        return False

def test_historial_rutas():
    """Test 4: Historial de rutas"""
    print_section("TEST 4: Historial de Rutas")
    
    response = requests.get(
        f"{BASE_URL}/rutas/historial/estado",
        params={"estado": "en_ejecucion", "limit": 5}
    )
    
    if response.status_code == 200:
        data = response.json()
        print_test(
            "Obtener historial de rutas en ejecución",
            True,
            f"Total: {data.get('total', 0)}\n"
            f"Rutas devueltas: {len(data.get('rutas', []))}\n"
            f"Estado filtrado: {data.get('filtros', {}).get('estado', 'N/A')}"
        )
        return True
    else:
        print_test(
            "Obtener historial de rutas",
            False,
            f"Status: {response.status_code}\nError: {response.text}"
        )
        return False

def test_calendario_rutas():
    """Test 5: Calendario de rutas"""
    print_section("TEST 5: Calendario de Rutas")
    
    response = requests.get(f"{BASE_URL}/rutas/calendario/activas")
    
    if response.status_code == 200:
        data = response.json()
        print_test(
            "Obtener calendario de rutas",
            True,
            f"Total días: {data.get('total_dias', 0)}\n"
            f"Rango: {data.get('rango_fechas', {}).get('fecha_inicio', 'N/A')} - "
            f"{data.get('rango_fechas', {}).get('fecha_fin', 'N/A')}\n"
            f"Total rutas: {data.get('estadisticas', {}).get('total_rutas', 0)}\n"
            f"Completadas: {data.get('estadisticas', {}).get('completadas', 0)}"
        )
        return True
    else:
        print_test(
            "Obtener calendario de rutas",
            False,
            f"Status: {response.status_code}\nError: {response.text}"
        )
        return False

def test_navegacion_ruta():
    """Test 6: Navegación de ruta (si hay ruta activa)"""
    print_section("TEST 6: Navegación de Ruta")
    
    if not ruta_id:
        print_test(
            "Obtener navegación de ruta",
            True,
            f"{YELLOW}Saltado: No hay ruta activa para probar{RESET}"
        )
        return True
    
    headers = {"Authorization": f"Bearer {conductor_token}"}
    response = requests.get(
        f"{BASE_URL}/rutas/{ruta_id}/navegacion",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print_test(
            "Obtener navegación de ruta",
            True,
            f"Ruta ID: {data.get('ruta_id', 'N/A')}\n"
            f"Progreso: {data.get('progreso', {}).get('completadas', 0)}/"
            f"{data.get('progreso', {}).get('total', 0)} incidencias\n"
            f"Siguiente punto: {data.get('siguiente_punto', {}).get('tipo', 'N/A')}"
        )
        return True
    else:
        print_test(
            "Obtener navegación de ruta",
            False,
            f"Status: {response.status_code}\nError: {response.text}"
        )
        return False

def test_completar_incidencia():
    """Test 7: Completar incidencia (simulado)"""
    print_section("TEST 7: Completar Incidencia")
    
    if not ruta_id:
        print_test(
            "Completar incidencia",
            True,
            f"{YELLOW}Saltado: No hay ruta activa para probar{RESET}"
        )
        return True
    
    # Obtener incidencias de la ruta
    response = requests.get(f"{BASE_URL}/rutas/{ruta_id}/detalles")
    
    if response.status_code != 200:
        print_test(
            "Completar incidencia",
            False,
            f"No se pudo obtener detalles de la ruta: {response.status_code}"
        )
        return False
    
    detalles = response.json()
    incidencias = [p for p in detalles.get("puntos", []) if p.get("tipo_punto") == "incidencia"]
    
    if not incidencias:
        print_test(
            "Completar incidencia",
            True,
            f"{YELLOW}No hay incidencias en la ruta para completar{RESET}"
        )
        return True
    
    # Intentar completar la primera incidencia pendiente
    incidencia_id = None
    for inc in incidencias:
        if inc.get("estado_incidencia") != "completada":
            incidencia_id = inc.get("incidencia_id")
            break
    
    if not incidencia_id:
        print_test(
            "Completar incidencia",
            True,
            f"{YELLOW}Todas las incidencias ya están completadas{RESET}"
        )
        return True
    
    headers = {"Authorization": f"Bearer {conductor_token}"}
    response = requests.post(
        f"{BASE_URL}/rutas/{ruta_id}/incidencia/{incidencia_id}/completar",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print_test(
            "Completar incidencia",
            True,
            f"Incidencia {incidencia_id} marcada como completada\n"
            f"Mensaje: {data.get('message', 'N/A')}"
        )
        return True
    else:
        print_test(
            "Completar incidencia",
            False,
            f"Status: {response.status_code}\nError: {response.text}"
        )
        return False

def run_all_tests():
    """Ejecutar todos los tests"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}TESTS DE ENDPOINTS - CONDUCTOR JOSUE{RESET}")
    print(f"{BLUE}Backend: {BASE_URL}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    tests = [
        test_login_conductor,
        test_rutas_activas_conductor,
        test_estadisticas_conductor,
        test_historial_rutas,
        test_calendario_rutas,
        test_navegacion_ruta,
        test_completar_incidencia
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"{RED}Error en test: {e}{RESET}\n")
            results.append(False)
    
    # Resumen
    print_section("RESUMEN DE TESTS")
    passed = sum(results)
    total = len(results)
    percentage = (passed / total * 100) if total > 0 else 0
    
    print(f"Tests ejecutados: {total}")
    print(f"{GREEN}Tests exitosos: {passed}{RESET}")
    print(f"{RED}Tests fallidos: {total - passed}{RESET}")
    print(f"Porcentaje de éxito: {percentage:.1f}%")
    
    if percentage == 100:
        print(f"\n{GREEN}🎉 ¡Todos los tests pasaron!{RESET}")
    elif percentage >= 70:
        print(f"\n{YELLOW}⚠️  La mayoría de tests pasaron{RESET}")
    else:
        print(f"\n{RED}❌ Muchos tests fallaron{RESET}")

if __name__ == "__main__":
    run_all_tests()
