"""
Script para verificar endpoints del backend
"""
import requests
import json

# Colores para terminal
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")

# Configuración
API_BASE = "https://epagal-backend-routing-latest.onrender.com"

def verificar_endpoint(url, nombre):
    """Verifica que un endpoint responda correctamente"""
    print_info(f"Verificando: {nombre}")
    print(f"  URL: {url}")
    
    try:
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            try:
                data = response.json()
                count = len(data) if isinstance(data, list) else 1
                print_success(f"  Status: 200 OK - {count} registros")
                
                # Mostrar muestra de datos
                if isinstance(data, list) and len(data) > 0:
                    print(f"  Ejemplo: {json.dumps(data[0], indent=2, ensure_ascii=False)[:200]}...")
                elif isinstance(data, dict):
                    print(f"  Datos: {json.dumps(data, indent=2, ensure_ascii=False)[:200]}...")
                    
                return True, data
            except:
                print_success(f"  Status: 200 OK")
                print(f"  Response: {response.text[:200]}")
                return True, None
        else:
            print_error(f"  Status: {response.status_code}")
            print(f"  Response: {response.text[:300]}")
            return False, None
            
    except requests.exceptions.Timeout:
        print_error(f"  Timeout - El servidor no respondió a tiempo")
        return False, None
    except Exception as e:
        print_error(f"  Error: {e}")
        return False, None

def main():
    print("\n" + "="*70)
    print("  VERIFICACIÓN DE ENDPOINTS - EPAGAL BACKEND")
    print("="*70 + "\n")
    
    # 1. Health check
    print("1. HEALTH CHECK\n" + "-"*70)
    ok, health_data = verificar_endpoint(f"{API_BASE}/health", "Health Check")
    
    if not ok:
        print_warning("\n⚠ El backend no está respondiendo correctamente.")
        print_info("El deployment podría estar en progreso...")
        print_info("Verifica en: https://github.com/Andres09xZ/epagal-backend-latacunga-route-service/actions")
        return
    
    if health_data:
        print(f"\n  Version: {health_data.get('version', 'unknown')}")
        checks = health_data.get('checks', {})
        for name, status in checks.items():
            if status == "ok":
                print_success(f"  {name}: {status}")
            else:
                print_warning(f"  {name}: {status}")
    
    print()
    
    # 2. API Root
    print("\n2. API ROOT\n" + "-"*70)
    ok, root_data = verificar_endpoint(f"{API_BASE}/", "API Root")
    print()
    
    # 3. Endpoints de Horarios
    print("\n3. ENDPOINTS DE HORARIOS\n" + "-"*70)
    
    endpoints_horarios = [
        (f"{API_BASE}/api/horarios/sectores", "GET Sectores"),
        (f"{API_BASE}/api/horarios", "GET Horarios"),
    ]
    
    horarios_ok = []
    for url, name in endpoints_horarios:
        ok, data = verificar_endpoint(url, name)
        horarios_ok.append(ok)
        print()
    
    # 4. Endpoints de Tracking
    print("\n4. ENDPOINTS DE TRACKING\n" + "-"*70)
    
    endpoints_tracking = [
        (f"{API_BASE}/api/tracking/activos", "GET Camiones Activos"),
    ]
    
    tracking_ok = []
    for url, name in endpoints_tracking:
        ok, data = verificar_endpoint(url, name)
        tracking_ok.append(ok)
        print()
    
    # 5. Documentación
    print("\n5. DOCUMENTACIÓN\n" + "-"*70)
    ok, _ = verificar_endpoint(f"{API_BASE}/docs", "Swagger UI")
    print()
    
    # Resumen
    print("\n" + "="*70)
    print("  RESUMEN")
    print("="*70)
    
    total_horarios = len(horarios_ok)
    total_tracking = len(tracking_ok)
    exitosos_horarios = sum(horarios_ok)
    exitosos_tracking = sum(tracking_ok)
    
    if exitosos_horarios == total_horarios and exitosos_tracking == total_tracking:
        print_success(f"\n✓ TODOS LOS ENDPOINTS FUNCIONAN CORRECTAMENTE")
        print_success(f"  Horarios: {exitosos_horarios}/{total_horarios}")
        print_success(f"  Tracking: {exitosos_tracking}/{total_tracking}")
        print_success("\n✓ Puedes probar la aplicación en:")
        print("  https://tesis-1-z78t.onrender.com/horarios")
        print("  https://tesis-1-z78t.onrender.com/tracking")
    else:
        print_error(f"\n✗ ALGUNOS ENDPOINTS FALLAN:")
        print(f"  Horarios: {exitosos_horarios}/{total_horarios}")
        print(f"  Tracking: {exitosos_tracking}/{total_tracking}")
        
        if exitosos_horarios < total_horarios or exitosos_tracking < total_tracking:
            print_warning("\n⚠ POSIBLES CAUSAS:")
            print("  1. El backend aún no se ha desplegado con los nuevos cambios")
            print("  2. La base de datos no tiene las tablas necesarias")
            print("  3. No hay datos de ejemplo en la base de datos")
            
            print_info("\n📋 SIGUIENTE PASO:")
            print("  Insertar datos de ejemplo en la base de datos de Supabase:")
            print("  Ejecuta el archivo: backend-routing/database/insert_test_data.sql")
            print("  En el SQL Editor de Supabase")
    
    print()

if __name__ == "__main__":
    main()
