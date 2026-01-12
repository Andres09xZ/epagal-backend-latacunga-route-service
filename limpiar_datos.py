"""
Script para limpiar la base de datos
Elimina todos los datos excepto el usuario administrador
"""
import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text

# Obtener URL de base de datos
DATABASE_URL = os.getenv("DB_URL") or os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("No se encontró DB_URL o DATABASE_URL en .env")

def limpiar_base_datos():
    """Limpia toda la base de datos excepto el usuario admin"""
    
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            print("🗑️  Iniciando limpieza de base de datos...")
            
            # Eliminar en el orden correcto por las foreign keys
            
            # 1. Geofencing - Alertas y estadísticas
            try:
                result = conn.execute(text("DELETE FROM estadisticas_geofencing"))
                conn.commit()
                print(f"   ✓ Eliminadas {result.rowcount} estadísticas de geofencing")
            except Exception as e:
                conn.rollback()
                print(f"   ⚠️  Tabla estadisticas_geofencing: {str(e)[:50]}")
            
            try:
                result = conn.execute(text("DELETE FROM geofence_alerts"))
                conn.commit()
                print(f"   ✓ Eliminadas {result.rowcount} alertas de geofencing")
            except Exception as e:
                conn.rollback()
                print(f"   ⚠️  Tabla geofence_alerts: {str(e)[:50]}")
            
            try:
                result = conn.execute(text("DELETE FROM historial_posiciones"))
                conn.commit()
                print(f"   ✓ Eliminadas {result.rowcount} posiciones GPS")
            except Exception as e:
                conn.rollback()
                print(f"   ⚠️  Tabla historial_posiciones: {str(e)[:50]}")
            
            # 2. Horarios
            try:
                result = conn.execute(text("DELETE FROM horarios_conductores"))
                conn.commit()
                print(f"   ✓ Eliminados {result.rowcount} horarios de conductores")
            except Exception as e:
                conn.rollback()
                print(f"   ⚠️  Tabla horarios_conductores: {str(e)[:50]}")
            
            # 3. Asignaciones (depende de conductores y rutas)
            try:
                result = conn.execute(text("DELETE FROM asignaciones_conductores"))
                conn.commit()
                print(f"   ✓ Eliminadas {result.rowcount} asignaciones")
            except Exception as e:
                conn.rollback()
                print(f"   ⚠️  Error en asignaciones: {str(e)[:50]}")
            
            # 4. Detalles de ruta (depende de rutas)
            try:
                result = conn.execute(text("DELETE FROM rutas_detalle"))
                conn.commit()
                print(f"   ✓ Eliminados {result.rowcount} detalles de ruta")
            except Exception as e:
                conn.rollback()
                print(f"   ⚠️  Error en rutas_detalle: {str(e)[:50]}")
            
            # 5. Rutas (depende de incidencias)
            try:
                result = conn.execute(text("DELETE FROM rutas_generadas"))
                conn.commit()
                print(f"   ✓ Eliminadas {result.rowcount} rutas")
            except Exception as e:
                conn.rollback()
                print(f"   ⚠️  Error en rutas_generadas: {str(e)[:50]}")
            
            # 6. Incidencias (independiente)
            try:
                result = conn.execute(text("DELETE FROM incidencias"))
                conn.commit()
                print(f"   ✓ Eliminadas {result.rowcount} incidencias")
            except Exception as e:
                conn.rollback()
                print(f"   ⚠️  Error en incidencias: {str(e)[:50]}")
            
            # 7. Conductores (depende de usuarios)
            try:
                result = conn.execute(text("DELETE FROM conductores"))
                conn.commit()
                print(f"   ✓ Eliminados {result.rowcount} conductores")
            except Exception as e:
                conn.rollback()
                print(f"   ⚠️  Error en conductores: {str(e)[:50]}")
            
            # 8. Usuarios no admin
            try:
                result = conn.execute(text("DELETE FROM usuarios WHERE tipo_usuario != 'admin'"))
                conn.commit()
                print(f"   ✓ Eliminados {result.rowcount} usuarios no admin")
            except Exception as e:
                conn.rollback()
                print(f"   ⚠️  Error en usuarios: {str(e)[:50]}")
            
            # Reiniciar secuencias
            print("\n🔄 Reiniciando secuencias...")
            try:
                conn.execute(text("ALTER SEQUENCE IF EXISTS estadisticas_geofencing_id_seq RESTART WITH 1"))
                conn.execute(text("ALTER SEQUENCE IF EXISTS geofence_alerts_id_seq RESTART WITH 1"))
                conn.execute(text("ALTER SEQUENCE IF EXISTS historial_posiciones_id_seq RESTART WITH 1"))
                conn.execute(text("ALTER SEQUENCE IF EXISTS horarios_conductores_id_seq RESTART WITH 1"))
                conn.execute(text("ALTER SEQUENCE IF EXISTS asignaciones_conductores_id_seq RESTART WITH 1"))
                conn.execute(text("ALTER SEQUENCE IF EXISTS rutas_detalle_id_seq RESTART WITH 1"))
                conn.execute(text("ALTER SEQUENCE IF EXISTS rutas_generadas_id_seq RESTART WITH 1"))
                conn.execute(text("ALTER SEQUENCE IF EXISTS incidencias_id_seq RESTART WITH 1"))
                conn.execute(text("ALTER SEQUENCE IF EXISTS conductores_id_seq RESTART WITH 1"))
                conn.commit()
                print("   ✓ Secuencias reiniciadas")
            except Exception as e:
                conn.rollback()
                print(f"   ⚠️  Error al reiniciar secuencias: {str(e)[:50]}")
            
            print("\n✅ Limpieza completada!")
            
            # Verificar usuario admin
            result = conn.execute(text(
                "SELECT id, username, email, tipo_usuario FROM usuarios WHERE tipo_usuario = 'admin'"
            ))
            admin = result.fetchone()
            
            if admin:
                print(f"\n👤 Usuario administrador:")
                print(f"   ID: {admin[0]}")
                print(f"   Username: {admin[1]}")
                print(f"   Email: {admin[2]}")
                print(f"   Tipo: {admin[3]}")
                print(f"\n🔐 Credenciales de acceso:")
                print(f"   Usuario: {admin[1]}")
                print(f"   Contraseña: admin123")
            else:
                print("\n⚠️  No se encontró usuario administrador")
            
            # Mostrar resumen
            print("\n📊 Resumen de la base de datos:")
            result = conn.execute(text("SELECT COUNT(*) FROM incidencias"))
            print(f"   Incidencias: {result.scalar()}")
            
            result = conn.execute(text("SELECT COUNT(*) FROM rutas_generadas"))
            print(f"   Rutas: {result.scalar()}")
            
            result = conn.execute(text("SELECT COUNT(*) FROM conductores"))
            print(f"   Conductores: {result.scalar()}")
            
            result = conn.execute(text("SELECT COUNT(*) FROM usuarios"))
            print(f"   Usuarios: {result.scalar()}")
            
    except Exception as e:
        print(f"\n❌ Error al limpiar la base de datos: {e}")
        raise
    finally:
        engine.dispose()

if __name__ == "__main__":
    print("=" * 60)
    print("🧹 LIMPIEZA DE BASE DE DATOS - EPAGAL")
    print("=" * 60)
    print("\n⚠️  Este script eliminará TODOS los datos excepto el admin")
    print("\n¿Estás seguro? Presiona Enter para continuar o Ctrl+C para cancelar...")
    input()
    
    limpiar_base_datos()
    
    print("\n" + "=" * 60)
    print("✨ Proceso completado. La base de datos está limpia.")
    print("=" * 60)
