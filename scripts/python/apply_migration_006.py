"""
Script para aplicar la migración 006:
Ampliar CHECK constraint de estado en tabla incidencias.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.database import engine
from sqlalchemy import text

STATEMENTS = [
    "ALTER TABLE incidencias DROP CONSTRAINT IF EXISTS check_estado",
    "ALTER TABLE incidencias DROP CONSTRAINT IF EXISTS incidencias_estado_check",
    """ALTER TABLE incidencias ADD CONSTRAINT check_estado
       CHECK (estado IN ('emitido', 'pendiente', 'validada', 'asignada', 'completada', 'cancelada'))""",
    "ALTER TABLE incidencias ALTER COLUMN estado TYPE VARCHAR(20)",
    "ALTER TABLE incidencias ALTER COLUMN estado SET DEFAULT 'emitido'",
]

with engine.connect() as conn:
    for stmt in STATEMENTS:
        print(f"Ejecutando: {stmt[:60]}...")
        conn.execute(text(stmt))
    conn.commit()
    print("\n✅ Migración 006 aplicada correctamente.")
    print("   check_estado ahora acepta: emitido, pendiente, validada, asignada, completada, cancelada")
