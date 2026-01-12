#!/usr/bin/env python
"""
Script para crear datos de ejemplo en la base de datos
Ejecutar: python seed_data.py
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import (
    Incidencia, RutaGenerada, RutaDetalle, Conductor, Usuario,
    AsignacionConductor, PuntoFijo, Config, Base
)
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password):
    return pwd_context.hash(password)


def seed_database():
    """Inserta datos de ejemplo en la base de datos"""
    db = SessionLocal()
    
    try:
        # Crear tablas si no existen
        Base.metadata.create_all(bind=engine)
        
        # 1. Crear usuarios (conductores)
        print("📝 Creando usuarios...")
        usuarios = []
        for i in range(1, 4):
            usuario = Usuario(
                username=f"conductor{i}",
                email=f"conductor{i}@latacunga.gob.ec",
                password_hash=hash_password("pass123"),
                tipo_usuario="conductor",
                activo=True
            )
            db.add(usuario)
            db.flush()
            usuarios.append(usuario)
        
        # 2. Crear conductores
        print("🚗 Creando conductores...")
        conductores = []
        nombres = [
            ("Juan Pérez García", "1234567890"),
            ("María López Rodríguez", "0987654321"),
            ("Carlos Sánchez Martínez", "1122334455")
        ]
        
        for i, (nombre, cedula) in enumerate(nombres):
            conductor = Conductor(
                usuario_id=usuarios[i].id,
                nombre_completo=nombre,
                cedula=cedula,
                telefono=f"099123456{i}",
                licencia_tipo="C",
                estado="disponible",
                zona_preferida="oriental" if i % 2 == 0 else "occidental"
            )
            db.add(conductor)
            db.flush()
            conductores.append(conductor)
        
        # 3. Crear incidencias
        print("🚨 Creando incidencias...")
        incidencias = []
        tipos = ["acopio", "zona_critica", "animal_muerto"]
        estados = ["pendiente", "validada", "asignada", "completada"]
        
        coordenadas = [
            (-0.9326, -78.6139, "oriental"),  # Latacunga centro
            (-0.9400, -78.6000, "occidental"),
            (-0.9250, -78.6200, "oriental"),
            (-0.9150, -78.6100, "occidental"),
            (-0.9350, -78.6150, "oriental"),
        ]
        
        for i, (lat, lon, zona) in enumerate(coordenadas):
            incidencia = Incidencia(
                tipo=tipos[i % len(tipos)],
                gravedad=[1, 3, 5][i % 3],
                descripcion=f"Incidencia de prueba {i+1}: {tipos[i % len(tipos)].replace('_', ' ').title()}",
                foto_url=None,
                lat=lat,
                lon=lon,
                geom=f"POINT({lon} {lat})",
                zona=zona,
                ventana_inicio=datetime.utcnow(),
                ventana_fin=datetime.utcnow() + timedelta(hours=8),
                estado=estados[i % len(estados)],
                reportado_en=datetime.utcnow() - timedelta(hours=i),
                usuario_id=usuarios[0].id if i < len(usuarios) else None
            )
            db.add(incidencia)
            db.flush()
            incidencias.append(incidencia)
        
        # 4. Crear rutas generadas
        print("🗺️  Creando rutas...")
        rutas = []
        for zona_name in ["oriental", "occidental"]:
            ruta = RutaGenerada(
                zona=zona_name,
                fecha_generacion=datetime.utcnow(),
                suma_gravedad=sum(inc.gravedad for inc in incidencias if inc.zona == zona_name),
                costo_total=25.5,
                duracion_estimada=timedelta(hours=4),
                camiones_usados=2,
                estado="en_ejecucion",
                notas=f"Ruta de prueba para zona {zona_name}"
            )
            db.add(ruta)
            db.flush()
            rutas.append(ruta)
        
        # 5. Crear puntos fijos
        print("📍 Creando puntos fijos...")
        puntos_fijos = [
            PuntoFijo(
                nombre="Depósito Oriental",
                tipo="deposito",
                lat=-0.935,
                lon=-78.612,
                geom="POINT(-78.612 -0.935)"
            ),
            PuntoFijo(
                nombre="Depósito Occidental",
                tipo="deposito",
                lat=-0.925,
                lon=-78.625,
                geom="POINT(-78.625 -0.925)"
            ),
            PuntoFijo(
                nombre="Botadero Latacunga",
                tipo="botadero",
                lat=-0.940,
                lon=-78.610,
                geom="POINT(-78.610 -0.940)"
            ),
        ]
        for pf in puntos_fijos:
            db.add(pf)
        
        # 6. Crear asignaciones de conductores a rutas
        print("👨‍💼 Creando asignaciones de conductores...")
        for i, ruta in enumerate(rutas):
            for j in range(2):
                conductor = conductores[i % len(conductores)]
                asignacion = AsignacionConductor(
                    ruta_id=ruta.id,
                    conductor_id=conductor.id,
                    camion_tipo="lateral" if j % 2 == 0 else "posterior",
                    camion_id=f"PIC-{1000+i}{j}",
                    fecha_asignacion=datetime.utcnow(),
                    fecha_inicio=datetime.utcnow(),
                    estado="iniciado"
                )
                db.add(asignacion)
        
        # 7. Crear detalles de ruta
        print("📌 Creando detalles de ruta...")
        for ruta in rutas:
            incidencias_ruta = [inc for inc in incidencias if inc.zona == ruta.zona]
            
            for orden, inc in enumerate(incidencias_ruta[:3]):  # Máximo 3 incidencias por ruta
                detalle = RutaDetalle(
                    ruta_id=ruta.id,
                    camion_tipo="lateral" if orden % 2 == 0 else "posterior",
                    camion_id=f"PIC-{1000+ruta.id}{orden}",
                    orden=orden + 1,
                    incidencia_id=inc.id,
                    tipo_punto="incidencia",
                    lat=inc.lat,
                    lon=inc.lon,
                    llegada_estimada=datetime.utcnow() + timedelta(hours=orden),
                    carga_acumulada=orden + 1
                )
                db.add(detalle)
        
        # 8. Crear configuraciones
        print("⚙️  Creando configuraciones...")
        config_items = [
            Config(clave="umbral_gravedad", valor="20", tipo_dato="integer", descripcion="Umbral de gravedad para alertas"),
            Config(clave="zona_oriental", valor="oriental", tipo_dato="string", descripcion="Nombre de zona oriental"),
            Config(clave="zona_occidental", valor="occidental", tipo_dato="string", descripcion="Nombre de zona occidental"),
        ]
        for cfg in config_items:
            # Verificar que no exista
            existing = db.query(Config).filter(Config.clave == cfg.clave).first()
            if not existing:
                db.add(cfg)
        
        # Commit de todos los cambios
        db.commit()
        print("\n✅ Datos de ejemplo creados exitosamente!")
        
        # Mostrar resumen
        print("\n📊 Resumen de datos creados:")
        print(f"  - Usuarios: {db.query(Usuario).count()}")
        print(f"  - Conductores: {db.query(Conductor).count()}")
        print(f"  - Incidencias: {db.query(Incidencia).count()}")
        print(f"  - Rutas: {db.query(RutaGenerada).count()}")
        print(f"  - Asignaciones: {db.query(AsignacionConductor).count()}")
        print(f"  - Puntos Fijos: {db.query(PuntoFijo).count()}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error al crear datos: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
