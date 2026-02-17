from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

print("\n" + "="*60)
print("ESTADO DE INCIDENCIAS")
print("="*60)

# Incidencias por zona y estado
incidencias = db.execute(text("""
    SELECT zona, estado, COUNT(*), COALESCE(SUM(gravedad), 0) 
    FROM incidencias 
    GROUP BY zona, estado 
    ORDER BY zona, estado
""")).fetchall()

print("\nIncidencias por zona y estado:")
print("-" * 60)
for zona, estado, count, suma in incidencias:
    print(f"  {zona:12} | {estado:10} | {count:2} incidencias | Gravedad: {suma:3}")

# Suma de validadas por zona
print("\n" + "="*60)
print("VERIFICACIÓN DE UMBRAL (por defecto = 20)")
print("="*60)

for zona_nombre in ['occidental', 'oriental']:
    suma = db.execute(text(f"""
        SELECT COALESCE(SUM(gravedad), 0) 
        FROM incidencias 
        WHERE zona = '{zona_nombre}' AND estado = 'validada'
    """)).scalar()
    
    supera = "✓ SUPERA" if suma > 20 else "✗ NO supera"
    print(f"\n  Zona {zona_nombre:10}: {suma:3} {supera}")
    if suma > 20:
        print(f"    → DEBERÍA generar ruta automáticamente")

# Verificar rutas
print("\n" + "="*60)
print("RUTAS GENERADAS")
print("="*60)

rutas = db.execute(text("""
    SELECT id, zona, estado, suma_gravedad 
    FROM rutas_generadas 
    ORDER BY created_at DESC 
    LIMIT 5
""")).fetchall()

if rutas:
    print(f"\n  Total rutas encontradas: {len(rutas)}")
    for id, zona, estado, suma in rutas:
        print(f"  - Ruta #{id}: {zona:10} | {estado:12} | Gravedad: {suma}")
else:
    print("\n  ✗ No hay rutas generadas")

db.close()
print("\n" + "="*60)
