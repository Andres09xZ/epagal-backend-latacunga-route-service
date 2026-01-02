"""
Modelos SQLAlchemy para la base de datos
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey, Text, Enum  # type: ignore[import]
from sqlalchemy.dialects.postgresql import UUID  # type: ignore[import]
from sqlalchemy.orm import relationship  # type: ignore[import]
from datetime import datetime
from app.database import Base
import uuid
import enum


class User(Base):
    """Modelo de usuario (coincide con esquema Neon)"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(Text, unique=True, index=True)
    username = Column(Text, unique=True, index=True, nullable=False)
    password_hash = Column(String(128))
    role = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    deleted_at = Column(DateTime(timezone=True))
    phone = Column(Text, unique=True)
    display_name = Column(Text)
    status = Column(Text, default='ACTIVE')


class Conductor(Base):
    """Modelo de conductor"""
    __tablename__ = "conductores"

    id = Column(Integer, primary_key=True, index=True)
    cedula = Column(String, unique=True, index=True, nullable=False)
    nombre_completo = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    telefono = Column(String, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    licencia_tipo = Column(String, nullable=False)  # C, D, E, etc
    zona_preferida = Column(String, nullable=True)
    estado = Column(String, default="disponible")  # disponible, ocupado, descansa
    usuario_id = Column(Integer, nullable=True)  # Sin FK (users.id es UUID)
    fecha_contratacion = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    vehiculos = relationship("Vehiculo", back_populates="conductor")
    asignaciones = relationship("Asignacion", back_populates="conductor")


class Vehiculo(Base):
    """Modelo de vehículo"""
    __tablename__ = "vehiculos"

    id = Column(Integer, primary_key=True, index=True)
    placa = Column(String, unique=True, index=True, nullable=False)
    marca = Column(String, nullable=False)
    modelo = Column(String, nullable=False)
    capacidad_toneladas = Column(Float, nullable=False)
    año = Column(Integer, nullable=False)
    estado = Column(String, default="disponible")
    conductor_id = Column(Integer, ForeignKey("conductores.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    conductor = relationship("Conductor", back_populates="vehiculos")
    asignaciones = relationship("Asignacion", back_populates="vehiculo")


class Ruta(Base):
    """Modelo de ruta"""
    __tablename__ = "rutas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String, nullable=True)
    distancia_km = Column(Float, nullable=False)
    tiempo_estimado_minutos = Column(Integer, nullable=False)
    estado = Column(String, default="activa")
    created_at = Column(DateTime, default=datetime.utcnow)

    asignaciones = relationship("Asignacion", back_populates="ruta")


class Incidencia(Base):
    """Modelo de incidencia/reporte ciudadano (coincide con Neon)"""
    __tablename__ = "incidencias"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(20), nullable=False)
    gravedad = Column(Integer, nullable=False)
    descripcion = Column(Text)
    foto_url = Column(String(255))
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    zona = Column(String(10))
    estado = Column(String(15))
    ventana_inicio = Column(DateTime, nullable=True)
    ventana_fin = Column(DateTime, nullable=True)
    reportado_en = Column(DateTime)
    usuario_id = Column(Integer)  # Sin FK (users.id es UUID)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)



# Modelo de Tarea
class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4)
    titulo = Column(String, nullable=False)
    descripcion = Column(Text, nullable=True)
    tipo = Column(String, nullable=False, default="RECOLECCION")
    prioridad = Column(String, nullable=False, default="MEDIA")
    estado = Column(String, nullable=False, default="PENDIENTE")
    progreso = Column(Integer, default=0)
    fecha_limite = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    conductor_id = Column(Integer, ForeignKey("conductores.id"), nullable=True)
    ruta_id = Column(Integer, ForeignKey("rutas.id"), nullable=True)

    conductor = relationship("Conductor")
    ruta = relationship("Ruta")

class ReportType(str, enum.Enum):
    ZONA_CRITICA = "ZONA_CRITICA"
    PUNTO_ACOPIO_LLENO = "PUNTO_ACOPIO_LLENO"

class ReportState(str, enum.Enum):
    ENVIADO = "ENVIADO"
    EN_PROCESO = "EN_PROCESO"
    COMPLETADO = "COMPLETADO"
    CERRADO = "CERRADO"

class Report(Base):
    """Modelo de reporte de incidencias desde APK (schema real de Neon)"""
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    type = Column(String(50), nullable=False)
    lat = Column(Float)
    lon = Column(Float)
    photo_url = Column(Text)
    description = Column(Text)
    status = Column(String(20))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    synced = Column(Boolean, default=False)
    report_location_id = Column(UUID(as_uuid=True))
    deleted_at = Column(DateTime)


class Asignacion(Base):
    """Modelo de asignación de ruta a conductor"""
    __tablename__ = "asignaciones"

    id = Column(Integer, primary_key=True, index=True)
    conductor_id = Column(Integer, ForeignKey("conductores.id"), nullable=False)
    vehiculo_id = Column(Integer, ForeignKey("vehiculos.id"), nullable=False)
    ruta_id = Column(Integer, ForeignKey("rutas.id"), nullable=False)
    fecha_asignacion = Column(DateTime, default=datetime.utcnow)
    fecha_inicio = Column(DateTime, nullable=True)
    fecha_fin = Column(DateTime, nullable=True)
    estado = Column(String, default="pendiente")
    created_at = Column(DateTime, default=datetime.utcnow)

    conductor = relationship("Conductor", back_populates="asignaciones")
    vehiculo = relationship("Vehiculo", back_populates="asignaciones")
    ruta = relationship("Ruta", back_populates="asignaciones")
