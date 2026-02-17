from app.database import SessionLocal
from app.models import Config, Incidencia

db = SessionLocal()

# Verificar umbral
config = db.query(Config).filter(Config.clave == 'umbral_gravedad').first()
print(f"Umbral configurado: {config.valor if config else 'NO CONFIGURADO'}")

# Verificar incidencias validadas
incidencias = db.query(Incidencia).filter(Incidencia.estado == 'validada').all()
suma = sum(inc.gravedad for inc in incidencias)
print(f"\nIncidencias validadas: {len(incidencias)}")
print(f"Suma total gravedad: {suma}")
print(f"Supera umbral (>{config.valor if config else 20}): {suma > int(config.valor if config else 20)}")

# Listar incidencias
for inc in incidencias:
    print(f"  - ID={inc.id}, tipo={inc.tipo}, gravedad={inc.gravedad}, zona={inc.zona}")

db.close()
