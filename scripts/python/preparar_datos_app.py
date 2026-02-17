"""
Script para preparar datos de prueba para la aplicación móvil
Crea conductores, incidencias y rutas listas para usar
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8081"
API_URL = f"{BASE_URL}/api"

def login_admin():
    """Login como administrador"""
    response = requests.post(
        f"{API_URL}/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Admin autenticado: {data['username']}")
        return data['access_token']
    else:
        print(f"❌ Error en login: {response.status_code}")
        return None

def crear_conductores_app(token, cantidad=3):
    """Crear conductores para la app"""
    print(f"\n{'='*70}")
    print(f"📱 CREANDO {cantidad} CONDUCTORES PARA LA APP")
    print('='*70)
    
    conductores = []
    zonas = ['oriental', 'occidental', 'oriental']
    licencias = ['C', 'C', 'D']
    
    for i in range(cantidad):
        conductor_data = {
            "username": f"operador{i+1}",
            "email": f"operador{i+1}@epagal.gob.ec",
            "password": "operador123",  # Misma password para todos
            "nombre_completo": f"Operador de Prueba {i+1}",
            "cedula": f"1805{100000 + i}",
            "telefono": f"09987654{10+i}",
            "licencia_tipo": licencias[i],
            "zona_preferida": zonas[i]
        }
        
        # Verificar si ya existe
        response = requests.get(
            f"{API_URL}/conductores/",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            existentes = response.json()
            existe = any(c['cedula'] == conductor_data['cedula'] for c in existentes)
            
            if existe:
                print(f"⚠️  Operador{i+1} ya existe - Saltando creación")
                conductor_existente = next(c for c in existentes if c['cedula'] == conductor_data['cedula'])
                conductores.append(conductor_existente)
                continue
        
        # Crear conductor
        response = requests.post(
            f"{API_URL}/conductores/",
            json=conductor_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            conductor = response.json()
            conductores.append(conductor)
            print(f"✅ Creado: {conductor['nombre_completo']}")
            print(f"   Username: {conductor['username']} | Password: operador123")
            print(f"   Zona: {conductor['zona_preferida']} | Licencia: {conductor['licencia_tipo']}")
        else:
            print(f"❌ Error al crear operador{i+1}: {response.status_code}")
    
    return conductores

def crear_incidencias_realistas(token, zona='oriental'):
    """Crear incidencias realistas para pruebas"""
    print(f"\n{'='*70}")
    print(f"🗑️ CREANDO INCIDENCIAS REALISTAS EN ZONA {zona.upper()}")
    print('='*70)
    
    # Incidencias para zona oriental (lon > -78.615)
    incidencias_oriental = [
        {
            "tipo": "acopio", 
            "lat": -0.9350, 
            "lon": -78.6100,
            "descripcion": "Punto de acopio saturado - Barrio La Merced",
            "gravedad": 5
        },
        {
            "tipo": "acopio", 
            "lat": -0.9360, 
            "lon": -78.6090,
            "descripcion": "Contenedor rebosado - Av. Eloy Alfaro",
            "gravedad": 5
        },
        {
            "tipo": "zona_critica", 
            "lat": -0.9370, 
            "lon": -78.6080,
            "descripcion": "Acumulación de basura - Mercado Cerrado",
            "gravedad": 3
        },
        {
            "tipo": "zona_critica", 
            "lat": -0.9380, 
            "lon": -78.6070,
            "descripcion": "Basura dispersa - Parque San Francisco",
            "gravedad": 3
        },
        {
            "tipo": "animal_muerto", 
            "lat": -0.9390, 
            "lon": -78.6060,
            "descripcion": "Animal en vía pública - Calle Quito",
            "gravedad": 5
        },
        {
            "tipo": "acopio", 
            "lat": -0.9330, 
            "lon": -78.6110,
            "descripcion": "Contenedor lleno - Barrio El Loreto",
            "gravedad": 5
        },
        {
            "tipo": "zona_critica", 
            "lat": -0.9320, 
            "lon": -78.6095,
            "descripcion": "Punto crítico - Terminal Terrestre",
            "gravedad": 3
        }
    ]
    
    # Incidencias para zona occidental (lon < -78.615)
    incidencias_occidental = [
        {
            "tipo": "acopio", 
            "lat": -0.9345, 
            "lon": -78.6200,
            "descripcion": "Punto de acopio lleno - Barrio San Felipe",
            "gravedad": 5
        },
        {
            "tipo": "acopio", 
            "lat": -0.9355, 
            "lon": -78.6210,
            "descripcion": "Contenedor saturado - Av. Amazonas",
            "gravedad": 5
        },
        {
            "tipo": "zona_critica", 
            "lat": -0.9365, 
            "lon": -78.6220,
            "descripcion": "Basura acumulada - Plaza de Toros",
            "gravedad": 3
        },
        {
            "tipo": "animal_muerto", 
            "lat": -0.9375, 
            "lon": -78.6230,
            "descripcion": "Animal fallecido - Vía a Ambato",
            "gravedad": 5
        },
        {
            "tipo": "zona_critica", 
            "lat": -0.9385, 
            "lon": -78.6240,
            "descripcion": "Zona crítica - Hospital IESS",
            "gravedad": 3
        }
    ]
    
    incidencias_a_crear = incidencias_oriental if zona == 'oriental' else incidencias_occidental
    
    incidencias_creadas = []
    for inc_data in incidencias_a_crear:
        response = requests.post(
            f"{API_URL}/incidencias/?auto_generar_ruta=false",
            json=inc_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code in [200, 201]:
            incidencia = response.json()
            incidencias_creadas.append(incidencia)
            print(f"✅ {incidencia['tipo']:15} | Gravedad: {incidencia['gravedad']} | {incidencia['descripcion'][:40]}")
        else:
            print(f"❌ Error al crear incidencia: {response.status_code}")
    
    print(f"\n📊 Total incidencias creadas: {len(incidencias_creadas)}")
    print(f"   Suma de gravedad: {sum(i['gravedad'] for i in incidencias_creadas)} puntos")
    
    return incidencias_creadas

def generar_ruta(token, zona='oriental'):
    """Generar ruta optimizada"""
    print(f"\n{'='*70}")
    print(f"🚛 GENERANDO RUTA OPTIMIZADA PARA ZONA {zona.upper()}")
    print('='*70)
    
    response = requests.post(
        f"{API_URL}/rutas/generar/{zona}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code in [200, 201]:
        ruta = response.json()
        print(f"✅ Ruta generada exitosamente")
        print(f"   ID: {ruta['id']}")
        print(f"   Zona: {ruta['zona']}")
        print(f"   Estado: {ruta['estado']}")
        print(f"   Camiones necesarios: {ruta['camiones_usados']}")
        print(f"   Suma gravedad: {ruta['suma_gravedad']} puntos")
        print(f"   Distancia total: {ruta['costo_total_metros']:.2f} metros")
        print(f"   Duración estimada: {ruta['duracion_estimada']}")
        return ruta
    else:
        print(f"❌ Error al generar ruta: {response.status_code}")
        print(response.text)
        return None

def asignar_conductores_a_ruta(token, ruta_id, conductores):
    """Asignar conductores a una ruta"""
    print(f"\n{'='*70}")
    print(f"👥 ASIGNANDO CONDUCTORES A RUTA {ruta_id}")
    print('='*70)
    
    # Obtener info de la ruta
    response = requests.get(
        f"{API_URL}/rutas/{ruta_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code != 200:
        print(f"❌ No se pudo obtener info de ruta")
        return []
    
    ruta = response.json()
    camiones_necesarios = ruta['camiones_usados']
    
    print(f"📊 Ruta necesita {camiones_necesarios} camión(es)")
    
    asignaciones = []
    tipos_camion = ['posterior', 'lateral']
    
    for i in range(min(camiones_necesarios, len(conductores))):
        conductor = conductores[i]
        camion_tipo = tipos_camion[i % len(tipos_camion)]
        
        asignacion_data = {
            "ruta_id": ruta_id,
            "conductor_id": conductor['id'],
            "camion_tipo": camion_tipo,
            "camion_id": f"LAT-{200 + i:03d}"
        }
        
        response = requests.post(
            f"{API_URL}/conductores/asignaciones/",
            json=asignacion_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code in [200, 201]:
            asignacion = response.json()
            asignaciones.append(asignacion)
            print(f"✅ {conductor['nombre_completo']:30} → {camion_tipo:10} | {asignacion_data['camion_id']}")
        else:
            print(f"❌ Error al asignar {conductor['nombre_completo']}: {response.status_code}")
    
    return asignaciones

def mostrar_credenciales_app(conductores):
    """Mostrar credenciales para la app móvil"""
    print(f"\n{'='*70}")
    print(f"📱 CREDENCIALES PARA LA APLICACIÓN MÓVIL")
    print('='*70)
    print("\nUsa estas credenciales en tu app móvil:\n")
    
    for i, conductor in enumerate(conductores, 1):
        print(f"👤 OPERADOR {i}")
        print(f"   Username: {conductor.get('username', 'N/A')}")
        print(f"   Password: operador123")
        print(f"   Nombre: {conductor['nombre_completo']}")
        print(f"   Zona: {conductor['zona_preferida']}")
        print(f"   Licencia: {conductor['licencia_tipo']}")
        print()

def verificar_datos_creados(token):
    """Verificar todos los datos creados"""
    print(f"\n{'='*70}")
    print(f"🔍 VERIFICACIÓN DE DATOS CREADOS")
    print('='*70)
    
    # Verificar incidencias pendientes
    response = requests.get(
        f"{API_URL}/incidencias/?estado=asignada",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        incidencias = response.json()
        print(f"✅ Incidencias asignadas: {len(incidencias)}")
    
    # Verificar rutas
    response = requests.get(
        f"{API_URL}/rutas/zona/oriental",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        rutas = data.get('rutas', [])
        print(f"✅ Rutas en zona oriental: {len(rutas)}")
        if rutas:
            ultima_ruta = rutas[0]
            print(f"   Última ruta: ID {ultima_ruta['id']} | Estado: {ultima_ruta['estado']}")
    
    # Verificar conductores disponibles
    response = requests.get(
        f"{API_URL}/conductores/disponibles",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        disponibles = response.json()
        print(f"✅ Conductores disponibles: {len(disponibles)}")

def main():
    print("\n" + "="*70)
    print("🚀 PREPARACIÓN DE DATOS PARA APLICACIÓN MÓVIL")
    print("="*70)
    
    # Login
    token = login_admin()
    if not token:
        print("\n❌ No se pudo autenticar. Verifica que el servidor esté corriendo.")
        return
    
    # Crear conductores
    conductores = crear_conductores_app(token, cantidad=3)
    
    # Crear incidencias zona oriental
    incidencias_oriental = crear_incidencias_realistas(token, zona='oriental')
    
    # Generar ruta oriental
    if incidencias_oriental:
        ruta_oriental = generar_ruta(token, zona='oriental')
        
        if ruta_oriental and conductores:
            # Asignar conductores
            asignaciones = asignar_conductores_a_ruta(token, ruta_oriental['id'], conductores)
    
    # Crear incidencias zona occidental
    incidencias_occidental = crear_incidencias_realistas(token, zona='occidental')
    
    # Generar ruta occidental
    if incidencias_occidental:
        ruta_occidental = generar_ruta(token, zona='occidental')
        
        if ruta_occidental and conductores:
            # Asignar conductores
            asignaciones_occ = asignar_conductores_a_ruta(token, ruta_occidental['id'], conductores)
    
    # Mostrar credenciales
    mostrar_credenciales_app(conductores)
    
    # Verificar datos
    verificar_datos_creados(token)
    
    # Resumen final
    print(f"\n{'='*70}")
    print("✅ DATOS PREPARADOS EXITOSAMENTE")
    print('='*70)
    print("\n📝 PRÓXIMOS PASOS:")
    print("   1. Abre tu aplicación móvil")
    print("   2. Ingresa con uno de los operadores (operador1/operador123)")
    print("   3. Verás tus rutas asignadas")
    print("   4. Podrás iniciar y completar rutas")
    print("   5. Ver detalles de incidencias en el mapa")
    print(f"\n🌐 Base URL: {BASE_URL}")
    print(f"📚 Documentación API: {BASE_URL}/docs")
    print('='*70)

if __name__ == "__main__":
    main()
