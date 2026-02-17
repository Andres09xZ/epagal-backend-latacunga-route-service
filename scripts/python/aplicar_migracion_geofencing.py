#!/usr/bin/env python3
"""
Script para aplicar migración de Geofencing a Neon PostgreSQL
Compatible con PostgreSQL 15+ y PostGIS 3.4+
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv

# Colores para terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")

def verificar_postgis(cursor):
    """Verificar que PostGIS está instalado"""
    try:
        cursor.execute("SELECT PostGIS_Version();")
        version = cursor.fetchone()[0]
        print_success(f"PostGIS instalado: {version}")
        return True
    except Exception as e:
        print_error(f"PostGIS no encontrado: {e}")
        return False

def habilitar_postgis(cursor):
    """Habilitar extensión PostGIS"""
    try:
        print_info("Habilitando PostGIS...")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis CASCADE;")
        cursor.execute("SELECT PostGIS_Version();")
        version = cursor.fetchone()[0]
        print_success(f"PostGIS habilitado: {version}")
        return True
    except Exception as e:
        print_error(f"Error al habilitar PostGIS: {e}")
        return False

def aplicar_migracion(cursor, archivo_sql):
    """Aplicar migración desde archivo SQL"""
    try:
        print_info(f"Leyendo {archivo_sql}...")
        with open(archivo_sql, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        print_info("Ejecutando migración...")
        cursor.execute(sql)
        print_success("Migración ejecutada correctamente")
        return True
    except FileNotFoundError:
        print_error(f"Archivo no encontrado: {archivo_sql}")
        return False
    except Exception as e:
        print_error(f"Error al ejecutar migración: {e}")
        return False

def verificar_tablas(cursor):
    """Verificar que las tablas se crearon correctamente"""
    tablas_esperadas = [
        'geofence_config',
        'zonas_geograficas',
        'historial_posiciones',
        'geofence_alerts',
        'estadisticas_geofencing'
    ]
    
    print_info("Verificando tablas creadas...")
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = ANY(%s)
        ORDER BY table_name;
    """, (tablas_esperadas,))
    
    tablas_creadas = [row[0] for row in cursor.fetchall()]
    
    for tabla in tablas_esperadas:
        if tabla in tablas_creadas:
            print_success(f"Tabla '{tabla}' creada")
        else:
            print_error(f"Tabla '{tabla}' NO encontrada")
    
    return len(tablas_creadas) == len(tablas_esperadas)

def verificar_configuracion(cursor):
    """Verificar configuración insertada"""
    print_info("Verificando configuración...")
    cursor.execute("SELECT COUNT(*) FROM geofence_config;")
    count = cursor.fetchone()[0]
    
    if count >= 10:
        print_success(f"Configuración insertada: {count} parámetros")
        
        # Mostrar algunos parámetros
        cursor.execute("""
            SELECT parametro, valor, unidad 
            FROM geofence_config 
            WHERE parametro IN ('velocidad_maxima_kmh', 'distancia_desviacion_m', 'tiempo_parada_min')
            ORDER BY parametro;
        """)
        
        print("\nParámetros principales:")
        for row in cursor.fetchall():
            print(f"  • {row[0]}: {row[1]} {row[2]}")
        
        return True
    else:
        print_error(f"Solo {count} parámetros encontrados (esperado: 10+)")
        return False

def verificar_zonas(cursor):
    """Verificar zonas geográficas insertadas"""
    print_info("Verificando zonas geográficas...")
    cursor.execute("SELECT COUNT(*) FROM zonas_geograficas;")
    count = cursor.fetchone()[0]
    
    if count >= 3:
        print_success(f"Zonas geográficas insertadas: {count}")
        
        # Mostrar zonas
        cursor.execute("""
            SELECT nombre, tipo, activa 
            FROM zonas_geograficas 
            ORDER BY nombre;
        """)
        
        print("\nZonas disponibles:")
        for row in cursor.fetchall():
            estado = "✓" if row[2] else "✗"
            print(f"  {estado} {row[0]} ({row[1]})")
        
        return True
    else:
        print_error(f"Solo {count} zonas encontradas (esperado: 3)")
        return False

def verificar_indices(cursor):
    """Verificar índices espaciales GIST"""
    print_info("Verificando índices espaciales GIST...")
    cursor.execute("""
        SELECT 
            tablename,
            indexname
        FROM pg_indexes
        WHERE indexname LIKE '%geometria%'
        ORDER BY tablename, indexname;
    """)
    
    indices = cursor.fetchall()
    if indices:
        print_success(f"{len(indices)} índices GIST creados")
        for tabla, indice in indices:
            print(f"  • {tabla}: {indice}")
        return True
    else:
        print_warning("No se encontraron índices GIST")
        return False

def test_postgis(cursor):
    """Probar funcionalidad PostGIS"""
    print_info("Probando funcionalidad PostGIS...")
    
    try:
        # Test 1: Crear punto
        cursor.execute("""
            SELECT ST_AsText(ST_SetSRID(ST_MakePoint(-78.6216, -0.9360), 4326));
        """)
        punto = cursor.fetchone()[0]
        print_success(f"Test punto: {punto}")
        
        # Test 2: Función punto_en_zona
        cursor.execute("""
            SELECT punto_en_zona(-0.9360, -78.6216, 'zona_occidental');
        """)
        resultado = cursor.fetchone()[0]
        print_success(f"Test punto_en_zona: {resultado}")
        
        return True
    except Exception as e:
        print_error(f"Error en test PostGIS: {e}")
        return False

def main():
    print_header("MIGRACIÓN GEOFENCING - NEON POSTGRESQL")
    
    # Cargar variables de entorno
    load_dotenv()
    
    # Intentar DATABASE_URL primero, luego DB_URL (compatibilidad)
    DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("DB_URL")
    
    if not DATABASE_URL:
        print_error("DATABASE_URL o DB_URL no configurada en .env")
        print_info("Ejemplo: DATABASE_URL=postgresql://user:pass@ep-xxx.neon.tech/neondb?sslmode=require")
        print_info("O bien: DB_URL=postgresql://user:pass@ep-xxx.neon.tech/neondb?sslmode=require")
        sys.exit(1)
    
    # Informar qué variable se está usando
    var_name = "DATABASE_URL" if os.getenv("DATABASE_URL") else "DB_URL"
    print_info(f"Usando variable de entorno: {var_name}")
    
    # Verificar que es una URL de Neon
    if "neon.tech" in DATABASE_URL:
        print_success("Conectando a Neon PostgreSQL...")
    else:
        print_warning("No parece ser una URL de Neon PostgreSQL")
    
    # Conectar a la base de datos
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cursor = conn.cursor()
        print_success("Conexión establecida")
    except Exception as e:
        print_error(f"Error de conexión: {e}")
        sys.exit(1)
    
    try:
        # Paso 1: Verificar/Habilitar PostGIS
        print_header("PASO 1: VERIFICAR POSTGIS")
        if not verificar_postgis(cursor):
            if not habilitar_postgis(cursor):
                print_error("No se pudo habilitar PostGIS")
                print_info("Habilita PostGIS manualmente desde Neon Console:")
                print_info("  CREATE EXTENSION IF NOT EXISTS postgis CASCADE;")
                sys.exit(1)
        
        # Paso 2: Aplicar migración
        print_header("PASO 2: APLICAR MIGRACIÓN")
        archivo_migracion = "migrations/005_sistema_geofencing.sql"
        if not aplicar_migracion(cursor, archivo_migracion):
            sys.exit(1)
        
        # Paso 3: Verificar tablas
        print_header("PASO 3: VERIFICAR TABLAS")
        if not verificar_tablas(cursor):
            print_error("Algunas tablas no se crearon correctamente")
            sys.exit(1)
        
        # Paso 4: Verificar configuración
        print_header("PASO 4: VERIFICAR CONFIGURACIÓN")
        verificar_configuracion(cursor)
        
        # Paso 5: Verificar zonas
        print_header("PASO 5: VERIFICAR ZONAS GEOGRÁFICAS")
        verificar_zonas(cursor)
        
        # Paso 6: Verificar índices
        print_header("PASO 6: VERIFICAR ÍNDICES")
        verificar_indices(cursor)
        
        # Paso 7: Test PostGIS
        print_header("PASO 7: TEST POSTGIS")
        test_postgis(cursor)
        
        # Resumen final
        print_header("✅ MIGRACIÓN COMPLETADA")
        print_success("Sistema de geofencing instalado correctamente")
        print_info("Próximos pasos:")
        print("  1. Iniciar servidor: uvicorn app.main:app --reload")
        print("  2. Verificar health: curl http://localhost:8000/api/geofencing/health")
        print("  3. Ejecutar tests: pytest features/steps/test_geofencing.py -v")
        
    except Exception as e:
        print_error(f"Error inesperado: {e}")
        sys.exit(1)
    
    finally:
        cursor.close()
        conn.close()
        print_info("Conexión cerrada")

if __name__ == "__main__":
    main()
