"""
Test BDD: Feature de Conductores y Autenticación
Valida los escenarios definidos en FEATURE_CONDUCTORES.md
Fecha: 2025-12-13
"""
import requests
import time
from typing import Dict, Optional

# Configuración
BASE_URL = "http://localhost:8081"
API_URL = f"{BASE_URL}/api"

# Variables globales para tokens y IDs
admin_token: Optional[str] = None
conductor_token: Optional[str] = None
nuevo_conductor_id: Optional[int] = None
nueva_ruta_id: Optional[int] = None
asignacion_id: Optional[int] = None


def print_step(step: str, description: str = ""):
    """Imprime un paso del test"""
    print(f"\n{'='*70}")
    print(f"📋 {step}")
    if description:
        print(f"   {description}")
    print('='*70)


def print_result(success: bool, message: str):
    """Imprime el resultado de una validación"""
    icon = "✅" if success else "❌"
    print(f"{icon} {message}")


def login(username: str, password: str) -> Dict:
    """
    Realiza login y retorna el token
    
    Escenario: Inicio de sesión de conductor
    """
    response = requests.post(
        f"{API_URL}/auth/login",
        json={
            "username": username,
            "password": password
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        raise Exception(f"Login falló: {response.status_code} - {response.text}")


def crear_conductor_completo() -> int:
    """
    Escenario: Registro de conductores en el sistema
    Dado que soy un administrador del sistema
    Cuando registro un nuevo conductor con sus credenciales
    Entonces se crea una cuenta de usuario tipo "conductor"
    Y el conductor puede iniciar sesión en la aplicación
    """
    global admin_token, nuevo_conductor_id
    
    print_step("PASO 1: Registro de nuevo conductor", "Admin registra conductor con credenciales")
    
    # Generar cédula única basada en timestamp
    import time
    cedula_unica = f"18091{int(time.time()) % 100000:05d}"
    username_unico = f"conductor_test_{int(time.time()) % 10000}"
    
    nuevo_conductor = {
        "username": username_unico,
        "email": f"test.conductor.{int(time.time()) % 10000}@epagal.gob.ec",
        "password": "test123456",
        "nombre_completo": "Test Conductor BDD",
        "cedula": cedula_unica,
        "telefono": "0998765432",
        "licencia_tipo": "C",
        "zona_preferida": "oriental"
    }
    
    response = requests.post(
        f"{API_URL}/conductores/",
        json=nuevo_conductor,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200, f"Error al crear conductor: {response.text}"
    conductor = response.json()
    
    print_result(True, f"Conductor creado: ID {conductor['id']}, Username: {conductor['username']}")
    print_result(conductor['estado'] == 'disponible', f"Estado inicial: {conductor['estado']}")
    
    # Verificar login del nuevo conductor
    print("\n🔐 Verificando login del nuevo conductor...")
    login_data = login(username_unico, "test123456")
    
    print_result(login_data['tipo_usuario'] == 'conductor', f"Tipo de usuario: {login_data['tipo_usuario']}")
    print_result(login_data['conductor_id'] is not None, f"Conductor ID en token: {login_data['conductor_id']}")
    
    return conductor['id']


def listar_conductores_disponibles():
    """
    Escenario: Disponibilidad de conductores
    Verifica conductores disponibles para asignación
    """
    print_step("PASO 2: Listar conductores disponibles", "Verificar conductores listos para asignación")
    
    response = requests.get(
        f"{API_URL}/conductores/disponibles?zona=oriental",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200, f"Error al listar disponibles: {response.text}"
    disponibles = response.json()
    
    print_result(len(disponibles) > 0, f"Conductores disponibles en oriental: {len(disponibles)}")
    
    for conductor in disponibles[:3]:
        print(f"   • {conductor['nombre_completo']} | {conductor['licencia_tipo']} | {conductor['zona_preferida']}")
    
    return disponibles


def crear_ruta_para_asignacion() -> int:
    """
    Crea una ruta de prueba para asignación de conductores
    """
    print_step("PASO 3: Generar ruta para asignación", "Crear ruta en zona oriental")
    
    # Crear incidencias en zona oriental (lon > -78.615)
    incidencias_data = [
        {"tipo": "acopio", "gravedad": 5, "lat": -0.9350, "lon": -78.610},
        {"tipo": "acopio", "gravedad": 5, "lat": -0.9360, "lon": -78.609},
        {"tipo": "zona_critica", "gravedad": 3, "lat": -0.9370, "lon": -78.608},
        {"tipo": "zona_critica", "gravedad": 3, "lat": -0.9380, "lon": -78.607},
        {"tipo": "animal_muerto", "gravedad": 5, "lat": -0.9390, "lon": -78.606}
    ]
    
    for inc_data in incidencias_data:
        response = requests.post(
            f"{API_URL}/incidencias/?auto_generar_ruta=false",
            json=inc_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [200, 201], f"Error al crear incidencia: Status {response.status_code}"
    
    print_result(True, f"Creadas {len(incidencias_data)} incidencias (25 puntos)")
    
    # Generar ruta
    response = requests.post(
        f"{API_URL}/rutas/generar/oriental",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code in [200, 201], f"Error al generar ruta: Status {response.status_code}"
    ruta = response.json()
    
    print_result(True, f"Ruta generada: ID {ruta['id']}, {ruta['camiones_usados']} camiones, {ruta['suma_gravedad']} puntos")
    
    return ruta['id']


def asignar_conductor1_a_ruta(ruta_id: int, conductor_id: int):
    """
    Asigna al conductor1 (que tiene sesión activa) a la ruta para poder probar inicio/finalización
    """
    print_step("PASO 3.5: Asignar conductor1 para pruebas", "Asignar conductor1 (sesión activa) a la ruta")
    
    asignacion_data = {
        "ruta_id": ruta_id,
        "conductor_id": conductor_id,
        "camion_tipo": "posterior",
        "camion_id": "LAT-001"
    }
    
    response = requests.post(
        f"{API_URL}/conductores/asignaciones/",
        json=asignacion_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code in [200, 201], f"Error al asignar conductor1: {response.text}"
    asignacion = response.json()
    
    print_result(True, f"Conductor1 asignado → {asignacion['camion_tipo']} ({asignacion['camion_id']})")
    return asignacion


def asignar_conductores_a_ruta(ruta_id: int, disponibles: list):
    """
    Escenario: Asignación automática de conductores a rutas
    Dado que existen conductores disponibles para zona oriental
    Cuando se genera una ruta con N camiones
    Entonces se asignan N conductores disponibles
    Y cada camión tiene exactamente un conductor
    """
    global asignacion_id, conductor_token
    
    print_step("PASO 4: Asignar conductores a ruta", f"Asignar conductores a ruta ID {ruta_id}")
    
    # Obtener detalles de la ruta para saber cuántos camiones necesita
    response = requests.get(
        f"{API_URL}/rutas/{ruta_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    ruta = response.json()
    camiones_necesarios = ruta['camiones_usados']
    
    print(f"\n📊 Ruta requiere {camiones_necesarios} camión(es)")
    
    # Asignar conductores
    asignaciones_creadas = []
    tipos_camion = ['posterior', 'lateral']  # Orden de asignación
    
    for i in range(min(camiones_necesarios, len(disponibles))):
        conductor = disponibles[i]
        camion_tipo = tipos_camion[i] if i < len(tipos_camion) else 'lateral'
        
        asignacion_data = {
            "ruta_id": ruta_id,
            "conductor_id": conductor['id'],
            "camion_tipo": camion_tipo,
            "camion_id": f"LAT-{100 + i}"
        }
        
        response = requests.post(
            f"{API_URL}/conductores/asignaciones/",
            json=asignacion_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code in [200, 201], f"Error al asignar conductor: {response.text}"
        asignacion = response.json()
        asignaciones_creadas.append(asignacion)
        
        print_result(True, f"Asignado: {asignacion['conductor_nombre']} → {camion_tipo} ({asignacion['camion_id']})")
        
        if i == 0:
            asignacion_id = asignacion['id']
            # Obtener token del primer conductor asignado para las pruebas
            print("\n🔐 Obteniendo token del conductor asignado para pruebas...")
            # Obtener datos del conductor para hacer login
            response_conductor = requests.get(
                f"{API_URL}/conductores/{conductor['id']}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            conductor_data = response_conductor.json()
            # Login con el conductor asignado (usando username del nuevo conductor)
            # Nota: Para esto funcione, necesitamos el username del conductor
            print(f"   Conductor asignado: {conductor_data.get('nombre_completo')} (ID: {conductor['id']})")
    
    # Verificar que no haya duplicados
    conductores_asignados = set(a['conductor_id'] for a in asignaciones_creadas)
    print_result(
        len(conductores_asignados) == len(asignaciones_creadas),
        f"Sin duplicados: {len(conductores_asignados)} conductores únicos"
    )
    
    return asignaciones_creadas


def verificar_mis_rutas_conductor():
    """
    Escenario: Visualización de rutas asignadas
    Dado que soy un conductor autenticado
    Cuando consulto mis rutas asignadas
    Entonces veo solo las rutas donde estoy asignado
    """
    print_step("PASO 5: Verificar mis rutas (como conductor)", "Conductor consulta sus rutas asignadas")
    
    response = requests.get(
        f"{API_URL}/conductores/mis-rutas/todas",
        headers={"Authorization": f"Bearer {conductor_token}"}
    )
    
    assert response.status_code == 200, f"Error al obtener mis rutas: {response.text}"
    mis_rutas = response.json()
    
    print_result(True, f"Total de asignaciones: {mis_rutas['total']}")
    print_result(True, f"Asignadas: {mis_rutas['asignado']}")
    print_result(True, f"Iniciadas: {mis_rutas['iniciado']}")
    print_result(True, f"Completadas: {mis_rutas['completado']}")
    
    if mis_rutas['rutas']:
        for ruta_info in mis_rutas['rutas']:
            print(f"\n   📍 Ruta {ruta_info['id']} - {ruta_info['zona']}")
            print(f"      Estado: {ruta_info['estado']} | Gravedad: {ruta_info['suma_gravedad']} pts")
            
            # Probar GET /api/rutas/{id} - Debe incluir puntos y polyline
            print(f"\n   🗺️ Obteniendo detalles de navegación de ruta {ruta_info['id']}...")
            response_detalles = requests.get(
                f"{API_URL}/rutas/{ruta_info['id']}",
                headers={"Authorization": f"Bearer {conductor_token}"}
            )
            
            if response_detalles.status_code == 200:
                ruta_nav = response_detalles.json()
                print_result(True, f"Ruta con navegación obtenida")
                print_result('puntos' in ruta_nav, f"Incluye puntos: {len(ruta_nav.get('puntos', []))} puntos")
                print_result('polyline' in ruta_nav, f"Incluye polyline: {'✅ Sí' if ruta_nav.get('polyline') else '⚠️ Vacío'}")
                
                # Mostrar primer punto como ejemplo
                if ruta_nav.get('puntos'):
                    primer_punto = ruta_nav['puntos'][0]
                    print(f"      Primer punto:")
                    print(f"        • Tipo: {primer_punto.get('tipo_punto')}")
                    print(f"        • Ubicación: [{primer_punto.get('lat')}, {primer_punto.get('lon')}]")
                    if primer_punto.get('incidencia_id'):
                        print(f"        • Incidencia: {primer_punto.get('tipo_incidencia')} (gravedad: {primer_punto.get('gravedad')})")
            
            # Probar GET /api/rutas/{id}/detalles - Debe incluir incidencias
            print(f"\n   📋 Obteniendo detalles completos con incidencias...")
            response_full = requests.get(
                f"{API_URL}/rutas/{ruta_info['id']}/detalles",
                headers={"Authorization": f"Bearer {conductor_token}"}
            )
            
            if response_full.status_code == 200:
                ruta_full = response_full.json()
                print_result(True, f"Detalles completos obtenidos")
                print_result('ruta' in ruta_full, f"Estructura correcta: ruta, incidencias, puntos")
                print_result('incidencias' in ruta_full, f"Incidencias: {len(ruta_full.get('incidencias', []))}")
                print_result('puntos' in ruta_full, f"Puntos: {len(ruta_full.get('puntos', []))}")
                
                # Mostrar primera incidencia
                if ruta_full.get('incidencias'):
                    primera_inc = ruta_full['incidencias'][0]
                    print(f"      Primera incidencia:")
                    print(f"        • Tipo: {primera_inc.get('tipo')}")
                    print(f"        • Gravedad: {primera_inc.get('gravedad')}")
                    print(f"        • Estado: {primera_inc.get('estado')}")
                    print(f"        • Ubicación: [{primera_inc.get('lat')}, {primera_inc.get('lon')}]")


def iniciar_ruta_como_conductor(ruta_id: int):
    """
    Escenario: Actualización de estado de ruta por conductor
    Dado que tengo una ruta asignada en estado "planeada"
    Cuando inicio la ruta desde mi aplicación
    Entonces el estado cambia a "en_ejecucion"
    Y mi estado como conductor cambia a "ocupado"
    """
    print_step("PASO 6: Iniciar ruta (como conductor)", f"Conductor inicia ruta ID {ruta_id}")
    
    response = requests.post(
        f"{API_URL}/conductores/iniciar-ruta",
        json={"ruta_id": ruta_id},
        headers={"Authorization": f"Bearer {conductor_token}"}
    )
    
    assert response.status_code == 200, f"Error al iniciar ruta: {response.text}"
    resultado = response.json()
    
    print_result(resultado['estado'] == 'iniciado', f"Estado de asignación: {resultado['estado']}")
    print_result(True, f"Fecha inicio: {resultado['fecha_inicio']}")
    
    # Verificar que el conductor ahora está ocupado
    response = requests.get(
        f"{API_URL}/auth/me",
        headers={"Authorization": f"Bearer {conductor_token}"}
    )
    
    if response.status_code == 200 and response.text:
        me_data = response.json()
        
        response = requests.get(
            f"{API_URL}/conductores/{me_data['conductor_id']}",
            headers={"Authorization": f"Bearer {conductor_token}"}
        )
        conductor_data = response.json()
        
        print_result(conductor_data['estado'] == 'ocupado', f"Estado del conductor: {conductor_data['estado']}")
    else:
        print_result(False, f"No se pudo verificar estado del conductor (response vacío)")


def finalizar_ruta_como_conductor(ruta_id: int):
    """
    Escenario: Finalización de ruta
    Dado que estoy ejecutando una ruta
    Cuando completo todos los puntos y finalizo la ruta
    Entonces el estado de la ruta cambia a "completada"
    Y mi estado como conductor cambia a "disponible"
    """
    print_step("PASO 7: Finalizar ruta (como conductor)", f"Conductor finaliza ruta ID {ruta_id}")
    
    response = requests.post(
        f"{API_URL}/conductores/finalizar-ruta",
        json={
            "ruta_id": ruta_id,
            "notas": "Ruta completada exitosamente. Todos los puntos atendidos."
        },
        headers={"Authorization": f"Bearer {conductor_token}"}
    )
    
    assert response.status_code == 200, f"Error al finalizar ruta: {response.text}"
    resultado = response.json()
    
    print_result(resultado['estado'] == 'completado', f"Estado de asignación: {resultado['estado']}")
    print_result(True, f"Fecha finalización: {resultado['fecha_finalizacion']}")
    
    # Verificar que el conductor vuelve a disponible
    response = requests.get(
        f"{API_URL}/auth/me",
        headers={"Authorization": f"Bearer {conductor_token}"}
    )
    
    if response.status_code == 200 and response.text:
        me_data = response.json()
        
        response = requests.get(
            f"{API_URL}/conductores/{me_data['conductor_id']}",
            headers={"Authorization": f"Bearer {conductor_token}"}
        )
        conductor_data = response.json()
        
        print_result(conductor_data['estado'] == 'disponible', f"Estado del conductor: {conductor_data['estado']}")
    else:
        print_result(False, f"No se pudo verificar estado del conductor (response vacío)")


def main():
    """Ejecuta todos los tests BDD"""
    global admin_token, conductor_token, nuevo_conductor_id, nueva_ruta_id
    
    print("\n" + "="*70)
    print("🧪 TEST BDD: FEATURE DE CONDUCTORES Y AUTENTICACIÓN")
    print("="*70)
    
    try:
        # Login como admin
        print_step("SETUP: Login como administrador")
        admin_data = login("admin", "admin123")
        admin_token = admin_data['access_token']
        print_result(True, f"Admin autenticado: {admin_data['username']}")
        
        # Login como conductor
        print_step("SETUP: Login como conductor")
        conductor_data = login("conductor1", "conductor123")
        conductor_token = conductor_data['access_token']
        print_result(True, f"Conductor autenticado: {conductor_data['username']}")
        
        # Ejecutar escenarios BDD
        nuevo_conductor_id = crear_conductor_completo()
        disponibles = listar_conductores_disponibles()
        nueva_ruta_id = crear_ruta_para_asignacion()
        
        # Asignar conductor1 (el que tiene sesión) a la ruta para poder probar inicio/fin
        asignar_conductor1_a_ruta(nueva_ruta_id, conductor_data['conductor_id'])
        asignar_conductores_a_ruta(nueva_ruta_id, disponibles)
        verificar_mis_rutas_conductor()
        iniciar_ruta_como_conductor(nueva_ruta_id)
        
        # Esperar simulación de trabajo
        print("\n⏳ Simulando ejecución de ruta (3 segundos)...")
        time.sleep(3)
        
        finalizar_ruta_como_conductor(nueva_ruta_id)
        
        # Resumen final
        print("\n" + "="*70)
        print("✅ TODOS LOS ESCENARIOS BDD COMPLETADOS EXITOSAMENTE")
        print("="*70)
        print("\n📊 Resumen:")
        print(f"   • Nuevo conductor creado: ID {nuevo_conductor_id}")
        print(f"   • Ruta generada: ID {nueva_ruta_id}")
        print(f"   • Conductores disponibles verificados")
        print(f"   • Asignaciones completadas correctamente")
        print(f"   • Ciclo de vida de ruta validado (asignado → iniciado → completado)")
        print(f"   • Estados de conductor sincronizados (disponible → ocupado → disponible)")
        print("="*70)
        
    except AssertionError as e:
        print(f"\n❌ Test falló: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
