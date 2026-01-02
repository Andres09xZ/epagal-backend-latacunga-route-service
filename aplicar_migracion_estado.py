"""
Script para aplicar migración: agregar estado 'asignada'
Ejecutar: python aplicar_migracion_estado.py
"""
import psycopg2
import os

# Usar directamente la conexión desde app/database.py
import sys
sys.path.append(os.path.dirname(__file__))

from app.database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        print("📊 Estados actuales de rutas:")
        result = conn.execute(text("SELECT estado, COUNT(*) FROM rutas_generadas GROUP BY estado"))
        for row in result:
            print(f"  - {row[0]}: {row[1]}")
        
        print("\n🔧 Eliminando constraint anterior...")
        conn.execute(text("ALTER TABLE rutas_generadas DROP CONSTRAINT IF EXISTS check_ruta_estado"))
        
        print("✅ Agregando nuevo constraint con estado 'asignada'...")
        conn.execute(text("""
            ALTER TABLE rutas_generadas ADD CONSTRAINT check_ruta_estado 
            CHECK (estado IN ('planeada', 'asignada', 'en_ejecucion', 'completada'))
        """))
        
        print("🔄 Actualizando rutas en_ejecucion sin fecha_inicio a 'asignada'...")
        result = conn.execute(text("""
            UPDATE rutas_generadas r
            SET estado = 'asignada'
            WHERE estado = 'en_ejecucion'
            AND EXISTS (
                SELECT 1 FROM asignaciones_conductores ac
                WHERE ac.ruta_id = r.id
                AND ac.fecha_inicio IS NULL
            )
        """))
        rows_updated = result.rowcount
        print(f"  ✓ Actualizadas {rows_updated} rutas")
        
        conn.commit()
        
        print("\n📊 Estados después de la migración:")
        result = conn.execute(text("SELECT estado, COUNT(*) FROM rutas_generadas GROUP BY estado"))
        for row in result:
            print(f"  - {row[0]}: {row[1]}")
    
    print("\n✅ Migración completada exitosamente!")
    
except Exception as e:
    print(f"\n❌ Error durante la migración: {e}")
    import traceback
    traceback.print_exc()
