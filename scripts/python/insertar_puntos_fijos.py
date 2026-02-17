import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DB_URL") or os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Insertar puntos fijos
    sql = """
        INSERT INTO puntos_fijos (nombre, tipo, lat, lon, geom, activo) VALUES
            ('Depósito EPAGAL', 'deposito', -0.936, -78.613, ST_SetSRID(ST_MakePoint(-78.613, -0.936), 4326), true),
            ('Botadero Inchapo', 'botadero', -0.949, -78.663, ST_SetSRID(ST_MakePoint(-78.663, -0.949), 4326), true)
        ON CONFLICT (nombre) DO UPDATE SET activo = true
    """
    conn.execute(text(sql))
    conn.commit()
    print("✅ Puntos fijos insertados")
    
    # Verificar
    result = conn.execute(text("SELECT nombre, tipo, activo FROM puntos_fijos"))
    print("\n📍 Puntos fijos en la base de datos:")
    for row in result:
        print(f"   - {row[0]} ({row[1]}): {'activo' if row[2] else 'inactivo'}")
