"""
Script para verificar y corregir el constraint de estados en rutas_generadas
"""
from app.database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        print("🔍 Verificando constraint actual...")
        
        # Ver el constraint actual
        result = conn.execute(text("""
            SELECT conname, pg_get_constraintdef(oid) 
            FROM pg_constraint 
            WHERE conrelid = 'rutas_generadas'::regclass 
            AND contype = 'c'
        """))
        
        print("\n📋 Constraints actuales:")
        for row in result:
            print(f"  - {row[0]}: {row[1]}")
        
        print("\n🔧 Eliminando constraint anterior rutas_generadas_estado_check...")
        conn.execute(text("ALTER TABLE rutas_generadas DROP CONSTRAINT IF EXISTS rutas_generadas_estado_check"))
        
        print("✅ Agregando nuevo constraint con 'asignada'...")
        conn.execute(text("""
            ALTER TABLE rutas_generadas ADD CONSTRAINT rutas_generadas_estado_check 
            CHECK (estado IN ('planeada', 'asignada', 'en_ejecucion', 'completada'))
        """))
        
        # También verificar el constraint de check_ruta_estado
        print("\n🔧 Eliminando constraint check_ruta_estado (si existe)...")
        conn.execute(text("ALTER TABLE rutas_generadas DROP CONSTRAINT IF EXISTS check_ruta_estado"))
        
        conn.commit()
        
        print("\n✅ Constraints actualizados correctamente!")
        
        # Verificar constraints finales
        result = conn.execute(text("""
            SELECT conname, pg_get_constraintdef(oid) 
            FROM pg_constraint 
            WHERE conrelid = 'rutas_generadas'::regclass 
            AND contype = 'c'
        """))
        
        print("\n📋 Constraints finales:")
        for row in result:
            print(f"  - {row[0]}: {row[1]}")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
