# app/models/geofencing.py
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from datetime import datetime
from enum import Enum as PyEnum

from app.database import Base


class TipoAlerta(str, PyEnum):
    """Tipos de alertas de geofencing"""
    DESVIACION_RUTA = "desviacion_ruta"
    VELOCIDAD_EXCESIVA = "velocidad_excesiva"
    PARADA_PROLONGADA = "parada_prolongada"
    FUERA_ZONA_COBERTURA = "fuera_zona_cobertura"
    ZONA_INCORRECTA = "zona_incorrecta"
    PRECISION_GPS_BAJA = "precision_gps_baja"
    DATOS_GPS_INVALIDOS = "datos_gps_invalidos"
    SALTO_TEMPORAL_ANOMALO = "salto_temporal_anomalo"


class SeveridadAlerta(str, PyEnum):
    """Niveles de severidad de alertas"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class EstadoAlerta(str, PyEnum):
    """Estados del ciclo de vida de una alerta"""
    ACTIVA = "activa"
    RESUELTA = "resuelta"
    IGNORADA = "ignorada"
    ESCALADA = "escalada"


class GeofenceAlert(Base):
    """
    Alertas generadas por el sistema de geofencing
    """
    __tablename__ = "geofence_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    conductor_id = Column(Integer, ForeignKey("conductores.id"), nullable=False, index=True)
    ruta_id = Column(Integer, ForeignKey("rutas_generadas.id"))
    
    # Tipo y severidad
    tipo = Column(String, nullable=False, index=True)  # TipoAlerta enum
    severidad = Column(String, nullable=False)  # SeveridadAlerta enum
    estado = Column(String, default=EstadoAlerta.ACTIVA.value)
    
    # Ubicación donde se generó la alerta
    # geometria = Column(Geometry('POINT', srid=4326))  # Columna PostGIS, comentada para evitar problemas con el ORM
    latitud = Column(Float, nullable=False)
    longitud = Column(Float, nullable=False)
    
    # Descripción
    descripcion = Column(Text, nullable=False)
    
    # Datos específicos según tipo de alerta
    velocidad_kmh = Column(Float)  # Para VELOCIDAD_EXCESIVA
    distancia_desviacion_m = Column(Float)  # Para DESVIACION_RUTA
    tiempo_parada_min = Column(Integer)  # Para PARADA_PROLONGADA
    
    # Timestamps
    timestamp = Column(DateTime, nullable=False, index=True)
    resuelta_at = Column(DateTime)
    resuelta_por = Column(String(100))
    
    # Escalamiento
    contador_recurrencia = Column(Integer, default=1)
    recomendaciones = Column(Text)
    notas = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    conductor = relationship("Conductor", back_populates="alertas_geofencing")
    
    def __repr__(self):
        return f"<GeofenceAlert(id={self.id}, tipo={self.tipo}, conductor_id={self.conductor_id}, severidad={self.severidad})>"


class GeofenceConfig(Base):
    """
    Configuración global del sistema de geofencing
    """
    __tablename__ = "geofence_config"
    
    id = Column(Integer, primary_key=True)
    parametro = Column(String, unique=True, nullable=False)
    valor = Column(Float, nullable=False)
    unidad = Column(String)
    descripcion = Column(Text)
    activo = Column(Boolean, default=True)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<GeofenceConfig(parametro={self.parametro}, valor={self.valor} {self.unidad})>"


class ZonaGeografica(Base):
    """
    Definición de zonas geográficas (occidental, oriental, etc.)
    """
    __tablename__ = "zonas_geograficas"
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String, unique=True, nullable=False)
    tipo = Column(String)  # 'cobertura', 'operacional', 'restringida'
    
    # Geometría del polígono
    # geometria = Column(Geometry('POLYGON', srid=4326), nullable=False)  # Columna PostGIS, comentada
    
    # Metadatos
    descripcion = Column(Text)
    activa = Column(Boolean, default=True)
    color_hex = Column(String(7))  # Para visualización en mapa
    
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ZonaGeografica(nombre={self.nombre}, tipo={self.tipo})>"


class HistorialPosicion(Base):
    """
    Historial completo de posiciones GPS de conductores
    Tabla optimizada para análisis temporal
    """
    __tablename__ = "historial_posiciones"
    
    id = Column(Integer, primary_key=True, index=True)
    conductor_id = Column(Integer, ForeignKey("conductores.id"), nullable=False, index=True)
    ruta_id = Column(Integer, ForeignKey("rutas_generadas.id"))
    
    # Geometría PostGIS
    # geometria = Column(Geometry('POINT', srid=4326), nullable=False)  # Columna PostGIS, comentada
    
    # Coordenadas
    latitud = Column(Float, nullable=False)
    longitud = Column(Float, nullable=False)
    
    # Metadatos GPS
    precision_m = Column(Float)
    velocidad_kmh = Column(Float)
    direccion_grados = Column(Float)  # Bearing 0-360
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    conductor = relationship("Conductor")
    ruta = relationship("RutaGenerada")
    
    def __repr__(self):
        return f"<HistorialPosicion(conductor={self.conductor_id}, lat={self.latitud}, lon={self.longitud}, time={self.timestamp})>"


class EstadisticaGeofencing(Base):
    """
    Estadísticas agregadas de geofencing por conductor/período
    Para reportes y análisis de desempeño
    """
    __tablename__ = "estadisticas_geofencing"
    
    id = Column(Integer, primary_key=True)
    conductor_id = Column(Integer, ForeignKey("conductores.id"), nullable=False, index=True)
    
    # Período
    periodo_inicio = Column(DateTime, nullable=False)
    periodo_fin = Column(DateTime, nullable=False)
    
    # Contadores de alertas por tipo
    total_alertas = Column(Integer, default=0)
    alertas_desviacion = Column(Integer, default=0)
    alertas_velocidad = Column(Integer, default=0)
    alertas_parada = Column(Integer, default=0)
    alertas_zona = Column(Integer, default=0)
    alertas_gps = Column(Integer, default=0)
    
    # Métricas de desempeño
    distancia_total_km = Column(Float)
    velocidad_promedio_kmh = Column(Float)
    velocidad_maxima_kmh = Column(Float)
    tiempo_conduccion_horas = Column(Float)
    
    # Clasificación de conductor
    puntuacion_seguridad = Column(Float, default=100)  # 0-100
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    conductor = relationship("Conductor")
    
    def __repr__(self):
        return f"<EstadisticaGeofencing(conductor={self.conductor_id}, periodo={self.periodo_inicio} - {self.periodo_fin}, puntuacion={self.puntuacion_seguridad})>"
