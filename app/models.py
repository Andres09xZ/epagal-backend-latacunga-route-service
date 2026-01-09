"""
Modelos SQLAlchemy para el sistema de gestión de incidencias y rutas
Fecha: 2025-12-13
"""
from sqlalchemy import (
    Column, Integer, String, Text, TIMESTAMP, Boolean,
    SmallInteger, CheckConstraint, ForeignKey, Interval,
    Float, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from datetime import datetime
import uuid

from app.database import Base


class Incidencia(Base):
    """
    Modelo para reportes de incidencias ciudadanas
    Tipos: acopio, zona_critica, animal_muerto
    """
    __tablename__ = "incidencias"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(20), nullable=False)
    gravedad = Column(SmallInteger, nullable=False)  # 1, 3 o 5
    descripcion = Column(Text)
    foto_url = Column(String(255))
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    geom = Column(Geometry('POINT', srid=4326), nullable=False)
    utm_easting = Column(Float)
    utm_northing = Column(Float)
    zona = Column(String(10))  # 'oriental' o 'occidental'
    ventana_inicio = Column(TIMESTAMP)
    ventana_fin = Column(TIMESTAMP)
    estado = Column(String(15), default='pendiente')  # pendiente, asignada, completada, cancelada
    reportado_en = Column(TIMESTAMP, default=datetime.utcnow)
    usuario_id = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Constraints
    __table_args__ = (
        CheckConstraint("tipo IN ('acopio', 'zona_critica', 'animal_muerto')", name='check_tipo'),
        CheckConstraint("gravedad IN (1, 3, 5)", name='check_gravedad'),
        CheckConstraint("zona IN ('oriental', 'occidental')", name='check_zona'),
        CheckConstraint("estado IN ('pendiente', 'validada', 'asignada', 'completada', 'cancelada')", name='check_estado'),
    )

    # Relaciones
    detalles_ruta = relationship("RutaDetalle", back_populates="incidencia")

    def __repr__(self):
        return f"<Incidencia(id={self.id}, tipo={self.tipo}, gravedad={self.gravedad}, estado={self.estado})>"


class RutaGenerada(Base):
    """
    Modelo para rutas optimizadas generadas por OR-Tools
    Una ruta puede incluir múltiples camiones
    """
    __tablename__ = "rutas_generadas"

    id = Column(Integer, primary_key=True, index=True)
    zona = Column(String(10), nullable=False)  # 'oriental' o 'occidental'
    fecha_generacion = Column(TIMESTAMP, default=datetime.utcnow)
    suma_gravedad = Column(Integer, nullable=False)
    costo_total = Column(Float)  # distancia o tiempo total
    duracion_estimada = Column(Interval)
    camiones_usados = Column(SmallInteger)
    estado = Column(String(15), default='planeada')  # planeada, asignada, en_ejecucion, completada
    notas = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Constraints
    __table_args__ = (
        CheckConstraint("zona IN ('oriental', 'occidental')", name='check_ruta_zona'),
        CheckConstraint("estado IN ('planeada', 'asignada', 'en_ejecucion', 'completada')", name='check_ruta_estado'),
    )

    # Relaciones
    detalles = relationship("RutaDetalle", back_populates="ruta", cascade="all, delete-orphan")
    asignaciones = relationship("AsignacionConductor", back_populates="ruta", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<RutaGenerada(id={self.id}, zona={self.zona}, estado={self.estado}, camiones={self.camiones_usados})>"


class RutaDetalle(Base):
    """
    Modelo para puntos individuales en una ruta
    Incluye: depósito, incidencias y botadero
    """
    __tablename__ = "rutas_detalle"

    id = Column(Integer, primary_key=True, index=True)
    ruta_id = Column(Integer, ForeignKey('rutas_generadas.id', ondelete='CASCADE'), nullable=False)
    camion_tipo = Column(String(10))  # 'lateral' o 'posterior'
    camion_id = Column(String(20))  # placa del camión
    orden = Column(SmallInteger, nullable=False)  # secuencia en la ruta
    incidencia_id = Column(Integer, ForeignKey('incidencias.id', ondelete='SET NULL'), nullable=True)
    tipo_punto = Column(String(15))  # 'deposito', 'incidencia', 'botadero'
    lat = Column(Float)
    lon = Column(Float)
    llegada_estimada = Column(TIMESTAMP)
    tiempo_servicio = Column(Interval, default='10 minutes')
    carga_acumulada = Column(SmallInteger)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Constraints
    __table_args__ = (
        CheckConstraint("camion_tipo IN ('lateral', 'posterior')", name='check_camion_tipo'),
        CheckConstraint("tipo_punto IN ('deposito', 'incidencia', 'botadero')", name='check_tipo_punto'),
    )

    # Relaciones
    ruta = relationship("RutaGenerada", back_populates="detalles")
    incidencia = relationship("Incidencia", back_populates="detalles_ruta")

    def __repr__(self):
        return f"<RutaDetalle(id={self.id}, ruta={self.ruta_id}, orden={self.orden}, tipo={self.tipo_punto})>"


class PuntoFijo(Base):
    """
    Modelo para puntos fijos del sistema: depósito y botadero
    """
    __tablename__ = "puntos_fijos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)
    tipo = Column(String(15))  # 'deposito' o 'botadero'
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    geom = Column(Geometry('POINT', srid=4326), nullable=False)
    activo = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Constraints
    __table_args__ = (
        CheckConstraint("tipo IN ('deposito', 'botadero')", name='check_punto_tipo'),
    )

    def __repr__(self):
        return f"<PuntoFijo(id={self.id}, nombre={self.nombre}, tipo={self.tipo})>"


class Config(Base):
    """
    Modelo para configuración global del sistema
    """
    __tablename__ = "config"

    id = Column(Integer, primary_key=True, index=True)
    clave = Column(String(50), unique=True, nullable=False)
    valor = Column(Text, nullable=False)
    descripcion = Column(Text)
    tipo_dato = Column(String(20), default='string')  # string, integer, float, boolean
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Constraints
    __table_args__ = (
        CheckConstraint("tipo_dato IN ('string', 'integer', 'float', 'boolean')", name='check_tipo_dato'),
    )

    def __repr__(self):
        return f"<Config(clave={self.clave}, valor={self.valor})>"

    def get_valor_convertido(self):
        """Convierte el valor según el tipo de dato especificado"""
        if self.tipo_dato == 'integer':
            return int(self.valor)
        elif self.tipo_dato == 'float':
            return float(self.valor)
        elif self.tipo_dato == 'boolean':
            return self.valor.lower() in ('true', '1', 'yes', 'si')
        return self.valor


class Usuario(Base):
    """
    Modelo para usuarios del sistema
    Tipos: admin, conductor, ciudadano, operador
    """
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    tipo_usuario = Column(String(15), nullable=False, default='ciudadano')
    activo = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Constraints
    # TODO: Migrar constraint para incluir 'operador'
    # __table_args__ = (
    #     CheckConstraint("tipo_usuario IN ('admin', 'conductor', 'ciudadano', 'operador')", name='check_tipo_usuario'),
    # )

    # Relaciones
    conductor = relationship("Conductor", back_populates="usuario", uselist=False)

    def __repr__(self):
        return f"<Usuario(id={self.id}, username={self.username}, tipo={self.tipo_usuario})>"


class Report(Base):
    """Modelo de reporte de incidencias desde APK (coincide con esquema de Neon/Supabase)."""
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    type = Column(String(50), nullable=False)
    lat = Column(Float)
    lon = Column(Float)
    photo_url = Column(Text)
    description = Column(Text)
    status = Column(String(20))
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    synced = Column(Boolean, default=False)
    report_location_id = Column(UUID(as_uuid=True))
    deleted_at = Column(TIMESTAMP)

    def __repr__(self):
        return f"<Report(id={self.id}, type={self.type}, status={self.status})>"


class Conductor(Base):
    """
    Modelo para conductores de camiones recolectores
    Extiende información del usuario con datos específicos del conductor
    """
    __tablename__ = "conductores"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id', ondelete='CASCADE'), unique=True, nullable=False)
    nombre_completo = Column(String(100), nullable=False)
    cedula = Column(String(10), unique=True, nullable=False, index=True)
    telefono = Column(String(15))
    licencia_tipo = Column(String(5))  # Tipo C, D, E
    fecha_contratacion = Column(TIMESTAMP, default=datetime.utcnow)
    estado = Column(String(15), default='disponible')  # disponible, ocupado, inactivo
    zona_preferida = Column(String(15), default='ambas')  # oriental, occidental, ambas
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Constraints
    __table_args__ = (
        CheckConstraint("estado IN ('disponible', 'ocupado', 'inactivo')", name='check_conductor_estado'),
        CheckConstraint("zona_preferida IN ('oriental', 'occidental', 'ambas')", name='check_conductor_zona'),
        CheckConstraint("licencia_tipo IN ('C', 'D', 'E')", name='check_licencia_tipo'),
    )

    # Relaciones
    usuario = relationship("Usuario", back_populates="conductor")
    asignaciones = relationship("AsignacionConductor", back_populates="conductor", cascade="all, delete-orphan")
    alertas_geofencing = relationship("GeofenceAlert", back_populates="conductor", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Conductor(id={self.id}, nombre={self.nombre_completo}, estado={self.estado})>"


class AsignacionConductor(Base):
    """
    Modelo para asignaciones de conductores a rutas
    Cada camión en una ruta tiene un conductor asignado
    """
    __tablename__ = "asignaciones_conductores"

    id = Column(Integer, primary_key=True, index=True)
    ruta_id = Column(Integer, ForeignKey('rutas_generadas.id', ondelete='CASCADE'), nullable=False)
    conductor_id = Column(Integer, ForeignKey('conductores.id', ondelete='CASCADE'), nullable=False)
    camion_tipo = Column(String(10), nullable=False)  # 'lateral' o 'posterior'
    camion_id = Column(String(20))  # placa del camión (opcional)
    fecha_asignacion = Column(TIMESTAMP, default=datetime.utcnow)
    fecha_inicio = Column(TIMESTAMP, nullable=True)
    fecha_finalizacion = Column(TIMESTAMP, nullable=True)
    estado = Column(String(15), default='asignado')  # asignado, iniciado, completado, cancelado
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Constraints
    __table_args__ = (
        CheckConstraint("camion_tipo IN ('lateral', 'posterior')", name='check_asignacion_camion_tipo'),
        CheckConstraint("estado IN ('asignado', 'iniciado', 'completado', 'cancelado')", name='check_asignacion_estado'),
    )

    # Relaciones
    ruta = relationship("RutaGenerada", back_populates="asignaciones")
    conductor = relationship("Conductor", back_populates="asignaciones")

    def __repr__(self):
        return f"<AsignacionConductor(id={self.id}, ruta={self.ruta_id}, conductor={self.conductor_id}, estado={self.estado})>"


class Sector(Base):
    """
    Modelo para sectores geográficos de Latacunga
    Divididos en zona oriental y occidental
    """
    __tablename__ = "sectores"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True)
    zona = Column(String(10), nullable=False)  # 'oriental' o 'occidental'
    poligono = Column(Geometry('POLYGON', srid=4326), nullable=False)
    coordenadas_centro = Column(Geometry('POINT', srid=4326), nullable=False)
    poblacion_estimada = Column(Integer)
    cantidad_viviendas = Column(Integer)
    activo = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Constraints
    __table_args__ = (
        CheckConstraint("zona IN ('oriental', 'occidental')", name='check_sector_zona'),
    )

    # Relaciones
    horarios = relationship("HorarioRecoleccion", back_populates="sector")

    def __repr__(self):
        return f"<Sector(id={self.id}, nombre={self.nombre}, zona={self.zona})>"


class HorarioRecoleccion(Base):
    """
    Modelo para horarios fijos de recolección por sector
    Define días de la semana y horas de operación
    """
    __tablename__ = "horarios_recoleccion"

    id = Column(Integer, primary_key=True, index=True)
    sector_id = Column(Integer, ForeignKey('sectores.id'), nullable=False)
    
    # Días de la semana (1=Lun, 2=Mar, ..., 7=Dom) almacenado como string "1,3,5"
    dias_semana = Column(String(20), nullable=False)  # "1,3,5" = Lun, Mié, Vie
    hora_inicio = Column(String(5), nullable=False)  # "06:00"
    hora_fin = Column(String(5), nullable=False)  # "08:00"
    
    # Tipo de recolección
    tipo = Column(String(20), default='domestica')  # domestica, comercial, barrido
    descripcion = Column(Text)
    
    # Recursos asignados
    camion_tipo = Column(String(15))  # posterior, lateral
    conductor_id = Column(Integer, ForeignKey('conductores.id'), nullable=True)
    camion_placa = Column(String(20))
    
    # Ruta predefinida
    ruta_optimizada = Column(Geometry('LINESTRING', srid=4326), nullable=True)
    distancia_km = Column(Float)
    duracion_estimada = Column(Interval)  # Intervalo de tiempo
    
    # Control de vigencia
    activo = Column(Boolean, default=True)
    fecha_inicio_vigencia = Column(TIMESTAMP, nullable=False)
    fecha_fin_vigencia = Column(TIMESTAMP, nullable=True)
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Constraints
    __table_args__ = (
        CheckConstraint("tipo IN ('domestica', 'comercial', 'barrido')", name='check_horario_tipo'),
        CheckConstraint("camion_tipo IN ('lateral', 'posterior')", name='check_horario_camion_tipo'),
    )

    # Relaciones
    sector = relationship("Sector", back_populates="horarios")
    conductor = relationship("Conductor", foreign_keys=[conductor_id])
    ejecuciones = relationship("EjecucionHorario", back_populates="horario")
    suspensiones = relationship("SuspensionHorario", back_populates="horario")

    def __repr__(self):
        return f"<HorarioRecoleccion(id={self.id}, sector={self.sector_id}, dias={self.dias_semana})>"


class EjecucionHorario(Base):
    """
    Modelo para el registro de ejecución diaria de horarios
    Rastrea cumplimiento y métricas
    """
    __tablename__ = "ejecuciones_horario"

    id = Column(Integer, primary_key=True, index=True)
    horario_id = Column(Integer, ForeignKey('horarios_recoleccion.id'), nullable=False)
    
    # Planificación
    fecha_programada = Column(TIMESTAMP, nullable=False)
    hora_inicio_programada = Column(String(5), nullable=False)
    hora_fin_programada = Column(String(5), nullable=False)
    
    # Ejecución real
    fecha_inicio_real = Column(TIMESTAMP, nullable=True)
    fecha_fin_real = Column(TIMESTAMP, nullable=True)
    
    # Asignación
    conductor_id = Column(Integer, ForeignKey('conductores.id'), nullable=False)
    camion_placa = Column(String(20), nullable=False)
    
    # Estado
    estado = Column(String(15), default='programada')  # programada, en_curso, completada, cancelada, atrasada
    porcentaje_cumplimiento = Column(Float)  # 0-100
    
    # Tracking GPS
    ruta_recorrida = Column(Geometry('LINESTRING', srid=4326), nullable=True)
    
    # Observaciones
    observaciones = Column(Text)
    incidentes = Column(Text)
    
    # Métricas
    toneladas_recolectadas = Column(Float)
    viviendas_atendidas = Column(Integer)
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Constraints
    __table_args__ = (
        CheckConstraint("estado IN ('programada', 'en_curso', 'completada', 'cancelada', 'atrasada')", name='check_ejecucion_estado'),
    )

    # Relaciones
    horario = relationship("HorarioRecoleccion", back_populates="ejecuciones")
    conductor = relationship("Conductor")
    puntos_tracking = relationship("PuntoTrackingHorario", back_populates="ejecucion")

    def __repr__(self):
        return f"<EjecucionHorario(id={self.id}, horario={self.horario_id}, fecha={self.fecha_programada}, estado={self.estado})>"


class PuntoTrackingHorario(Base):
    """
    Modelo para puntos GPS de tracking en tiempo real
    """
    __tablename__ = "puntos_tracking_horario"

    id = Column(Integer, primary_key=True, index=True)
    ejecucion_id = Column(Integer, ForeignKey('ejecuciones_horario.id'), nullable=False)
    
    punto = Column(Geometry('POINT', srid=4326), nullable=False)
    timestamp = Column(TIMESTAMP, default=datetime.utcnow)
    velocidad = Column(Float)  # km/h
    
    # Relaciones
    ejecucion = relationship("EjecucionHorario", back_populates="puntos_tracking")

    def __repr__(self):
        return f"<PuntoTrackingHorario(id={self.id}, ejecucion={self.ejecucion_id})>"


class SuspensionHorario(Base):
    """
    Modelo para suspensiones temporales de horarios
    Feriados, mantenimiento, etc.
    """
    __tablename__ = "suspensiones_horario"

    id = Column(Integer, primary_key=True, index=True)
    horario_id = Column(Integer, ForeignKey('horarios_recoleccion.id'), nullable=False)
    
    fecha_suspension = Column(TIMESTAMP, nullable=False)
    motivo = Column(Text, nullable=False)
    fecha_recuperacion = Column(TIMESTAMP, nullable=True)  # Día alternativo
    
    notificado = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey('usuarios.id'), nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relaciones
    horario = relationship("HorarioRecoleccion", back_populates="suspensiones")
    usuario = relationship("Usuario")

    def __repr__(self):
        return f"<SuspensionHorario(id={self.id}, horario={self.horario_id}, fecha={self.fecha_suspension})>"
