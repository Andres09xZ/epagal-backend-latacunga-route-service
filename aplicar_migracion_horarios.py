#!/usr/bin/env python3
"""
Script para aplicar la migración del sistema de horarios a Neon PostgreSQL
Ejecutar: python aplicar_migracion_horarios.py
"""

from app.database import engine
from sqlalchemy import text
import os
from dotenv import load_dotenv

def aplicar_migracion():
    """Aplica la migración 004_sistema_horarios.sql"""
    
    # Cargar variables de entorno
    load_dotenv()
    
    print("=" * 80)
    print("🚀 APLICANDO MIGRACIÓN: Sistema de Horarios")
    print("=" * 80)
    print()
    
    # Leer el archivo SQL
    migration_file = "migrations/004_sistema_horarios.sql"
    
    if not os.path.exists(migration_file):
        print(f"❌ Error: No se encuentra el archivo {migration_file}")
        return False
    
    print(f"📄 Leyendo archivo: {migration_file}")
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    print(f"✅ Archivo leído correctamente")
    print()
    
    # Ejecutar todo el SQL como un solo bloque
    try:
        # Obtener conexión raw de psycopg2
        raw_conn = engine.raw_connection()
        cursor = raw_conn.cursor()
        
        print("🔌 Conectado a Neon PostgreSQL")
        print()
        
        print("⚙️  Ejecutando migración completa...")
        
        try:
            # Ejecutar todo el contenido SQL
            cursor.execute(sql_content)
            raw_conn.commit()
            
            print("    ✅ Migración ejecutada exitosamente")
            print()
            
        except Exception as e:
            error_msg = str(e)
            print(f"    ❌ Error: {error_msg}")
            raw_conn.rollback()
            raise
        finally:
            cursor.close()
            raw_conn.close()
        
        print("=" * 80)
        print("🎉 MIGRACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 80)
        print()
        print("📊 Tablas creadas:")
        print("   ✅ sectores")
        print("   ✅ horarios_recoleccion")
        print("   ✅ ejecuciones_horario")
        print("   ✅ puntos_tracking_horario")
        print("   ✅ suspensiones_horario")
        print()
        print("🗺️  PostGIS habilitado para geometrías")
        print("📅 Vistas creadas para horarios de hoy")
        print("🔄 Triggers configurados para updated_at")
        print()
        
        return True
            
    except Exception as e:
        print()
        print("=" * 80)
        print("❌ ERROR AL APLICAR MIGRACIÓN")
        print("=" * 80)
        print(f"Error: {str(e)}")
        print()
        print("💡 Sugerencias:")
        print("   1. Verifica que la conexión a Neon PostgreSQL esté activa")
        print("   2. Revisa que el usuario tenga permisos de CREATE TABLE")
        print("   3. Verifica que PostGIS esté disponible en Neon")
        print("   4. Si algunas tablas ya existen, eso es normal (IF NOT EXISTS)")
        print()
        return False

def verificar_tablas():
    """Verifica que las tablas se hayan creado correctamente"""
    
    print("🔍 Verificando tablas creadas...")
    print()
    
    tablas_esperadas = [
        'sectores',
        'horarios_recoleccion',
        'ejecuciones_horario',
        'puntos_tracking_horario',
        'suspensiones_horario'
    ]
    
    try:
        with engine.connect() as connection:
            for tabla in tablas_esperadas:
                result = connection.execute(text(f"""
                    SELECT COUNT(*) as count 
                    FROM information_schema.tables 
                    WHERE table_name = '{tabla}'
                """))
                
                count = result.fetchone()[0]
                
                if count > 0:
                    print(f"   ✅ {tabla}")
                else:
                    print(f"   ❌ {tabla} - NO ENCONTRADA")
            
            print()
            print("🎯 Verificación completada")
            
    except Exception as e:
        print(f"❌ Error al verificar: {str(e)}")

if __name__ == "__main__":
    try:
        # Aplicar migración
        exito = aplicar_migracion()
        
        if exito:
            # Verificar tablas
            verificar_tablas()
            
            print("✨ El sistema de horarios está listo para usarse")
            print()
            print("📝 Próximos pasos:")
            print("   1. Iniciar el servidor: uvicorn app.main:app --reload --port 9000")
            print("   2. Abrir dashboard: http://localhost:9000/dashboard/")
            print("   3. Crear sectores y horarios desde el dashboard")
            print()
        else:
            print("⚠️  La migración no se completó correctamente")
            exit(1)
            
    except KeyboardInterrupt:
        print()
        print("⚠️  Migración cancelada por el usuario")
        exit(1)
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        exit(1)
