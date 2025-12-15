"""
Modelos SQLAlchemy para el sistema de gestión de incidencias y rutas
Fecha: 2025-12-13
"""
from sqlalchemy import (
    Column, Integer, String, Text, TIMESTAMP, Boolean, 
    SmallInteger, CheckConstraint, ForeignKey, Interval,
    Float, func
)
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from datetime import datetime

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
    estado = Column(String(15), default='planeada')  # planeada, en_ejecucion, completada
    notas = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Constraints
    __table_args__ = (
        CheckConstraint("zona IN ('oriental', 'occidental')", name='check_ruta_zona'),
        CheckConstraint("estado IN ('planeada', 'en_ejecucion', 'completada')", name='check_ruta_estado'),
    )

    # Relaciones
    detalles = relationship("RutaDetalle", back_populates="ruta", cascade="all, delete-orphan")

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
    Tipos: admin, conductor, ciudadano
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
    __table_args__ = (
        CheckConstraint("tipo_usuario IN ('admin', 'conductor', 'ciudadano')", name='check_tipo_usuario'),
    )

    # Relaciones
    conductor = relationship("Conductor", back_populates="usuario", uselist=False)

    def __repr__(self):
        return f"<Usuario(id={self.id}, username={self.username}, tipo={self.tipo_usuario})>"


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
    ruta = relationship("RutaGenerada")
    conductor = relationship("Conductor", back_populates="asignaciones")

    def __repr__(self):
        return f"<AsignacionConductor(id={self.id}, ruta={self.ruta_id}, conductor={self.conductor_id}, estado={self.estado})>"
