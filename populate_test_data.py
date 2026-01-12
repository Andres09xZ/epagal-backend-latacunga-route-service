"""
Script para poblar la base de datos con datos de prueba
y verificar que los endpoints funcionan correctamente
"""
import os
import sys
from pathlib import Path
import requests
import psycopg2
from psycopg2.extras import RealDictCursor

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
DB_URL = os.getenv("DATABASE_URL")
API_BASE = "https://epagal-backend-routing-latest.onrender.com/api"

def ejecutar_sql_file():
    """Ejecuta el archivo SQL de datos de prueba"""
    print_info("Conectando a la base de datos...")
    
    if not DB_URL:
        print_error("DATABASE_URL no está configurado")
        return False
    
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Leer archivo SQL
        sql_file = Path(__file__).parent / "database" / "insert_test_data.sql"
        print_info(f"Leyendo archivo: {sql_file}")
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        # Ejecutar SQL
        print_info("Ejecutando script SQL...")
        cur.execute(sql)
        conn.commit()
        
        # Verificar datos insertados
        print_success("SQL ejecutado correctamente\n")
        
        # Contar sectores
        cur.execute("SELECT COUNT(*) as count FROM sectores")
        sectores_count = cur.fetchone()['count']
        print_success(f"Sectores en DB: {sectores_count}")
        
        # Contar horarios
        cur.execute("SELECT COUNT(*) as count FROM horarios_recoleccion")
        horarios_count = cur.fetchone()['count']
        print_success(f"Horarios en DB: {horarios_count}")
        
        # Contar ejecuciones activas
        cur.execute("SELECT COUNT(*) as count FROM ejecuciones_horario WHERE estado = 'en_curso'")
        ejecuciones_count = cur.fetchone()['count']
        print_success(f"Ejecuciones activas: {ejecuciones_count}")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print_error(f"Error al ejecutar SQL: {e}")
        return False

def verificar_endpoint(endpoint_path, nombre):
    """Verifica que un endpoint responda correctamente"""
    url = f"{API_BASE}{endpoint_path}"
    print_info(f"Verificando: {nombre}")
    print(f"  URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else 1
            print_success(f"  Status: 200 OK - {count} registros")
            return True
        else:
            print_error(f"  Status: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print_error(f"  Timeout - El servidor no respondió a tiempo")
        return False
    except Exception as e:
        print_error(f"  Error: {e}")
        return False

def verificar_health():
    """Verifica el endpoint de health"""
    url = "https://epagal-backend-routing-latest.onrender.com/health"
    print_info("Verificando estado del backend...")
    print(f"  URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"  Status: {data.get('status', 'unknown')}")
            print_success(f"  Version: {data.get('version', 'unknown')}")
            
            checks = data.get('checks', {})
            for check_name, check_status in checks.items():
                if check_status == "ok":
                    print_success(f"  {check_name}: {check_status}")
                else:
                    print_warning(f"  {check_name}: {check_status}")
            
            return True
        else:
            print_error(f"  Status: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"  Error: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("  SCRIPT DE DATOS DE PRUEBA - EPAGAL LATACUNGA")
    print("="*60 + "\n")
    
    # Paso 1: Verificar health del backend
    print("\n1. VERIFICACIÓN DEL BACKEND\n" + "-"*60)
    backend_ok = verificar_health()
    
    if not backend_ok:
        print_warning("\nEl backend no está respondiendo correctamente.")
        print_warning("Esperando a que el deployment termine...")
        print_info("Puedes verificar el progreso en:")
        print("  https://github.com/Andres09xZ/epagal-backend-latacunga-route-service/actions")
        print("  https://dashboard.render.com")
        return
    
    # Paso 2: Insertar datos de prueba (si hay DATABASE_URL)
    if DB_URL:
        print("\n2. INSERCIÓN DE DATOS DE PRUEBA\n" + "-"*60)
        sql_ok = ejecutar_sql_file()
        
        if not sql_ok:
            print_warning("\nNo se pudieron insertar datos de prueba.")
            print_info("Puedes ejecutar el SQL manualmente desde:")
            print("  backend-routing/database/insert_test_data.sql")
    else:
        print_warning("\nDATABASE_URL no configurado - Saltando inserción de datos")
        print_info("Los datos de prueba deben insertarse manualmente en Supabase")
    
    # Paso 3: Verificar endpoints
    print("\n3. VERIFICACIÓN DE ENDPOINTS\n" + "-"*60)
    
    endpoints = [
        ("/horarios/sectores", "Sectores"),
        ("/horarios", "Horarios de Recolección"),
        ("/tracking/activos", "Tracking Activos"),
    ]
    
    results = []
    for path, name in endpoints:
        ok = verificar_endpoint(path, name)
        results.append(ok)
        print()
    
    # Resumen
    print("\n" + "="*60)
    print("  RESUMEN")
    print("="*60)
    
    total = len(results)
    exitosos = sum(results)
    
    if exitosos == total:
        print_success(f"\n✓ Todos los endpoints funcionan correctamente ({exitosos}/{total})")
        print_success("\nPuedes probar la aplicación en:")
        print("  https://tesis-1-z78t.onrender.com/horarios")
        print("  https://tesis-1-z78t.onrender.com/tracking")
    else:
        print_warning(f"\n⚠ {exitosos}/{total} endpoints funcionando")
        print_info("\nSi los endpoints fallan, verifica:")
        print("  1. Que el backend esté desplegado (GitHub Actions)")
        print("  2. Que la base de datos tenga las tablas (migrations)")
        print("  3. Que haya datos de ejemplo insertados")
    
    print()

if __name__ == "__main__":
    main()
