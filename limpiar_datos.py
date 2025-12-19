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
            # 1. Eliminar asignaciones primero (depende de conductores y rutas)
            result = conn.execute(text("DELETE FROM asignaciones_conductores"))
            print(f"   ✓ Eliminadas {result.rowcount} asignaciones")
            conn.commit()
            
            # 2. Eliminar detalles de ruta (depende de rutas)
            result = conn.execute(text("DELETE FROM rutas_detalle"))
            print(f"   ✓ Eliminados {result.rowcount} detalles de ruta")
            conn.commit()
            
            # 3. Eliminar rutas (depende de incidencias)
            result = conn.execute(text("DELETE FROM rutas_generadas"))
            print(f"   ✓ Eliminadas {result.rowcount} rutas")
            conn.commit()
            
            # 4. Eliminar incidencias (independiente)
            result = conn.execute(text("DELETE FROM incidencias"))
            print(f"   ✓ Eliminadas {result.rowcount} incidencias")
            conn.commit()
            
            # 5. Eliminar conductores (depende de usuarios)
            result = conn.execute(text("DELETE FROM conductores"))
            print(f"   ✓ Eliminados {result.rowcount} conductores")
            conn.commit()
            
            # 6. Eliminar usuarios no admin
            result = conn.execute(text("DELETE FROM usuarios WHERE tipo_usuario != 'admin'"))
            print(f"   ✓ Eliminados {result.rowcount} usuarios no admin")
            conn.commit()
            
            # Reiniciar secuencias
            conn.execute(text("ALTER SEQUENCE IF EXISTS asignaciones_conductores_id_seq RESTART WITH 1"))
            conn.execute(text("ALTER SEQUENCE IF EXISTS rutas_detalle_id_seq RESTART WITH 1"))
            conn.execute(text("ALTER SEQUENCE IF EXISTS rutas_generadas_id_seq RESTART WITH 1"))
            conn.execute(text("ALTER SEQUENCE IF EXISTS incidencias_id_seq RESTART WITH 1"))
            conn.execute(text("ALTER SEQUENCE IF EXISTS conductores_id_seq RESTART WITH 1"))
            conn.commit()
            
            print("\n✅ Limpieza completada exitosamente!")
            
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
