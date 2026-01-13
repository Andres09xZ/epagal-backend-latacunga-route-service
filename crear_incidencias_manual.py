"""
Script interactivo para crear y validar incidencias manualmente
Uso: python crear_incidencias_manual.py
"""
import requests
import time
from typing import Optional

BASE_URL = "http://localhost:8000"

def crear_incidencia(tipo: str, lat: float, lon: float, descripcion: str) -> Optional[int]:
    """Crea una incidencia y retorna su ID"""
    payload = {
        "tipo": tipo,
        "descripcion": descripcion,
        "lat": lat,
        "lon": lon,
        "usuario_id": 1
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/incidencias/", json=payload)
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Incidencia {data['id']} creada: {tipo} (gravedad={data['gravedad']}, zona={data['zona']})")
            return data['id']
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None

def validar_incidencia(inc_id: int) -> bool:
    """Valida una incidencia"""
    try:
        response = requests.post(f"{BASE_URL}/api/incidencias/{inc_id}/validate")
        if response.status_code == 200:
            data = response.json()
            if data.get('ruta_generada'):
                print(f"🎉 ¡RUTA GENERADA! ID={data['ruta_generada']['id']}, zona={data['ruta_generada']['zona']}")
                return True
            else:
                print(f"✅ Incidencia {inc_id} validada (sin generar ruta)")
                return False
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def ver_rutas_zona(zona: str):
    """Muestra las rutas de una zona"""
    try:
        response = requests.get(f"{BASE_URL}/api/rutas/zona/{zona}")
        if response.status_code == 200:
            data = response.json()
            rutas = data.get('rutas', [])
            print(f"\n📍 Rutas en zona {zona}: {len(rutas)}")
            for ruta in rutas:
                print(f"  - Ruta {ruta['id']}: gravedad={ruta['suma_gravedad']}, "
                      f"camiones={ruta['camiones_usados']}, "
                      f"estado={ruta.get('estado', 'N/A')}")
        else:
            print(f"❌ Error {response.status_code}")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")

def menu_principal():
    """Menú interactivo"""
    print("\n" + "="*60)
    print("🚛 SISTEMA DE INCIDENCIAS - EPAGAL LATACUNGA")
    print("="*60)
    print("\n[Opciones]")
    print("1. Caso 1: Generar Ruta 1 (Norte Oriental) - 6 incidencias")
    print("2. Caso 2: Anti-solapamiento (Cerca Ruta 1) - 3 incidencias")
    print("3. Caso 3: Generar Ruta 2 (Sur Oriental) - 6 incidencias")
    print("4. Caso 4: Generar Ruta 3 (Occidental) - 6 incidencias")
    print("5. Crear incidencia personalizada")
    print("6. Validar incidencia por ID")
    print("7. Ver rutas de zona Oriental")
    print("8. Ver rutas de zona Occidental")
    print("9. Limpiar base de datos")
    print("0. Salir")
    
    opcion = input("\nElige una opción: ")
    return opcion

def caso1_norte_oriental():
    """Caso 1: Genera 6 incidencias en norte oriental"""
    print("\n🎯 CASO 1: Generando Ruta 1 (Norte Oriental)")
    print("📊 Total esperado: 22 puntos (5+3+3+5+3+3)")
    print("⏱️  Creando 6 incidencias...\n")
    
    incidencias = [
        ("animal_muerto", -0.9200, -78.6100, "Animal muerto - Norte 1"),
        ("zona_critica", -0.9250, -78.6120, "Zona crítica - Norte 2"),
        ("zona_critica", -0.9280, -78.6150, "Zona crítica - Norte 3"),
        ("animal_muerto", -0.9300, -78.6080, "Animal muerto - Norte 4"),
        ("zona_critica", -0.9320, -78.6140, "Zona crítica - Norte 5"),
        ("zona_critica", -0.9330, -78.6160, "Zona crítica - Norte 6"),
    ]
    
    ids = []
    for tipo, lat, lon, desc in incidencias:
        inc_id = crear_incidencia(tipo, lat, lon, desc)
        if inc_id:
            ids.append(inc_id)
        time.sleep(0.3)
    
    print(f"\n✅ {len(ids)} incidencias creadas")
    input("\nPresiona Enter para validar todas las incidencias...")
    
    print("\n🔍 Validando incidencias...")
    for inc_id in ids:
        validar_incidencia(inc_id)
        time.sleep(0.5)
    
    print("\n📊 Verificando rutas generadas...")
    time.sleep(1)
    ver_rutas_zona("oriental")

def caso2_antisolapamiento():
    """Caso 2: 3 incidencias cerca de Ruta 1"""
    print("\n🎯 CASO 2: Anti-solapamiento (Cerca de Ruta 1)")
    print("📊 Total: 7 puntos (1+3+1)")
    print("⚠️  Estas incidencias están <500m de Ruta 1")
    print("⏱️  Creando 3 incidencias...\n")
    
    incidencias = [
        ("acopio", -0.9210, -78.6110, "Acopio cerca Norte 1"),
        ("zona_critica", -0.9260, -78.6130, "Zona crítica cerca Norte 2"),
        ("acopio", -0.9290, -78.6090, "Acopio cerca Norte 4"),
    ]
    
    ids = []
    for tipo, lat, lon, desc in incidencias:
        inc_id = crear_incidencia(tipo, lat, lon, desc)
        if inc_id:
            ids.append(inc_id)
        time.sleep(0.3)
    
    print(f"\n✅ {len(ids)} incidencias creadas")
    input("\nPresiona Enter para validar todas las incidencias...")
    
    print("\n🔍 Validando incidencias...")
    print("❗ NO debería generar nueva ruta (anti-solapamiento)")
    for inc_id in ids:
        validar_incidencia(inc_id)
        time.sleep(0.5)
    
    print("\n📊 Verificando rutas (debe seguir siendo 1)...")
    time.sleep(1)
    ver_rutas_zona("oriental")

def caso3_sur_oriental():
    """Caso 3: 6 incidencias en sur oriental"""
    print("\n🎯 CASO 3: Generando Ruta 2 (Sur Oriental)")
    print("📊 Total esperado: 22 puntos (5+3+3+5+3+3)")
    print("📍 Ubicación: Sur (lejos de Ruta 1)")
    print("⏱️  Creando 6 incidencias...\n")
    
    incidencias = [
        ("animal_muerto", -0.9800, -78.6100, "Animal muerto - Sur 1"),
        ("zona_critica", -0.9850, -78.6120, "Zona crítica - Sur 2"),
        ("zona_critica", -0.9880, -78.6150, "Zona crítica - Sur 3"),
        ("animal_muerto", -0.9900, -78.6080, "Animal muerto - Sur 4"),
        ("zona_critica", -0.9920, -78.6140, "Zona crítica - Sur 5"),
        ("zona_critica", -0.9930, -78.6160, "Zona crítica - Sur 6"),
    ]
    
    ids = []
    for tipo, lat, lon, desc in incidencias:
        inc_id = crear_incidencia(tipo, lat, lon, desc)
        if inc_id:
            ids.append(inc_id)
        time.sleep(0.3)
    
    print(f"\n✅ {len(ids)} incidencias creadas")
    input("\nPresiona Enter para validar todas las incidencias...")
    
    print("\n🔍 Validando incidencias...")
    for inc_id in ids:
        validar_incidencia(inc_id)
        time.sleep(0.5)
    
    print("\n📊 Verificando rutas generadas (debería haber 2)...")
    time.sleep(1)
    ver_rutas_zona("oriental")

def caso4_occidental():
    """Caso 4: 6 incidencias en zona occidental"""
    print("\n🎯 CASO 4: Generando Ruta 3 (Occidental)")
    print("📊 Total esperado: 22 puntos (5+3+3+5+3+3)")
    print("📍 Zona: Occidental (lon >= -78.6191)")
    print("⏱️  Creando 6 incidencias...\n")
    
    incidencias = [
        ("animal_muerto", -0.9200, -78.6300, "Animal muerto - Occidental 1"),
        ("zona_critica", -0.9250, -78.6320, "Zona crítica - Occidental 2"),
        ("zona_critica", -0.9280, -78.6350, "Zona crítica - Occidental 3"),
        ("animal_muerto", -0.9300, -78.6280, "Animal muerto - Occidental 4"),
        ("zona_critica", -0.9320, -78.6340, "Zona crítica - Occidental 5"),
        ("zona_critica", -0.9330, -78.6360, "Zona crítica - Occidental 6"),
    ]
    
    ids = []
    for tipo, lat, lon, desc in incidencias:
        inc_id = crear_incidencia(tipo, lat, lon, desc)
        if inc_id:
            ids.append(inc_id)
        time.sleep(0.3)
    
    print(f"\n✅ {len(ids)} incidencias creadas")
    input("\nPresiona Enter para validar todas las incidencias...")
    
    print("\n🔍 Validando incidencias...")
    for inc_id in ids:
        validar_incidencia(inc_id)
        time.sleep(0.5)
    
    print("\n📊 Verificando rutas generadas...")
    time.sleep(1)
    ver_rutas_zona("occidental")

def crear_personalizada():
    """Crear incidencia personalizada"""
    print("\n📝 Crear Incidencia Personalizada")
    print("\nTipos disponibles:")
    print("  1. animal_muerto (5 puntos)")
    print("  2. zona_critica (3 puntos)")
    print("  3. acopio (1 punto)")
    
    tipo_num = input("\nElige tipo (1-3): ")
    tipos = {"1": "animal_muerto", "2": "zona_critica", "3": "acopio"}
    tipo = tipos.get(tipo_num, "acopio")
    
    lat = float(input("Latitud (ej: -0.9200): "))
    lon = float(input("Longitud (ej: -78.6100): "))
    desc = input("Descripción: ")
    
    inc_id = crear_incidencia(tipo, lat, lon, desc)
    if inc_id:
        validar = input(f"\n¿Validar incidencia {inc_id}? (s/n): ")
        if validar.lower() == 's':
            validar_incidencia(inc_id)

def validar_por_id():
    """Validar incidencia por ID"""
    inc_id = int(input("\nIngresa el ID de la incidencia a validar: "))
    validar_incidencia(inc_id)

def limpiar_datos():
    """Limpia la base de datos"""
    print("\n⚠️  ¿Estás seguro de limpiar todos los datos?")
    confirmacion = input("Escribe 'SI' para confirmar: ")
    if confirmacion == "SI":
        import subprocess
        subprocess.run(["python", "limpiar_datos.py"])
    else:
        print("❌ Operación cancelada")

def main():
    """Función principal"""
    while True:
        opcion = menu_principal()
        
        if opcion == "1":
            caso1_norte_oriental()
        elif opcion == "2":
            caso2_antisolapamiento()
        elif opcion == "3":
            caso3_sur_oriental()
        elif opcion == "4":
            caso4_occidental()
        elif opcion == "5":
            crear_personalizada()
        elif opcion == "6":
            validar_por_id()
        elif opcion == "7":
            ver_rutas_zona("oriental")
        elif opcion == "8":
            ver_rutas_zona("occidental")
        elif opcion == "9":
            limpiar_datos()
        elif opcion == "0":
            print("\n👋 ¡Hasta luego!")
            break
        else:
            print("\n❌ Opción inválida")
        
        input("\nPresiona Enter para continuar...")

if __name__ == "__main__":
    main()
