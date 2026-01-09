# app/schemas/geofencing.py
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class TipoAlerta(str, Enum):
    DESVIACION_RUTA = "desviacion_ruta"
    VELOCIDAD_EXCESIVA = "velocidad_excesiva"
    PARADA_PROLONGADA = "parada_prolongada"
    FUERA_ZONA_COBERTURA = "fuera_zona_cobertura"
    ZONA_INCORRECTA = "zona_incorrecta"
    PRECISION_GPS_BAJA = "precision_gps_baja"
    DATOS_GPS_INVALIDOS = "datos_gps_invalidos"
    SALTO_TEMPORAL_ANOMALO = "salto_temporal_anomalo"


class SeveridadAlerta(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class EstadoAlerta(str, Enum):
    ACTIVA = "activa"
    RESUELTA = "resuelta"
    IGNORADA = "ignorada"
    ESCALADA = "escalada"


class GeofenceAlertCreate(BaseModel):
    """Schema para crear nueva alerta de geofencing"""
    conductor_id: int
    ruta_id: Optional[int] = None
    tipo: TipoAlerta
    severidad: SeveridadAlerta
    latitud: float = Field(..., ge=-90, le=90)
    longitud: float = Field(..., ge=-180, le=180)
    descripcion: str
    velocidad_kmh: Optional[float] = None
    distancia_desviacion_m: Optional[float] = None
    tiempo_parada_min: Optional[int] = None


class GeofenceAlertResponse(BaseModel):
    """Schema para respuesta de alerta"""
    id: int
    conductor_id: int
    ruta_id: Optional[int]
    tipo: str
    severidad: str
    estado: str
    latitud: float
    longitud: float
    descripcion: str
    velocidad_kmh: Optional[float]
    distancia_desviacion_m: Optional[float]
    tiempo_parada_min: Optional[int]
    timestamp: datetime
    resuelta_at: Optional[datetime]
    resuelta_por: Optional[str]
    contador_recurrencia: int
    recomendaciones: Optional[str]
    notas: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class GeofenceAlertUpdate(BaseModel):
    """Schema para actualizar estado de alerta"""
    estado: Optional[EstadoAlerta] = None
    resuelta_at: Optional[datetime] = None
    resuelta_por: Optional[str] = None
    notas: Optional[str] = None


class GeofenceConfigUpdate(BaseModel):
    """Schema para actualizar configuración de geofencing"""
    parametro: str
    valor: float
    unidad: Optional[str] = None
    descripcion: Optional[str] = None
    activo: bool = True


class GeofenceConfigResponse(BaseModel):
    """Schema para respuesta de configuración"""
    id: int
    parametro: str
    valor: float
    unidad: Optional[str]
    descripcion: Optional[str]
    activo: bool
    fecha_actualizacion: datetime
    
    class Config:
        from_attributes = True


class PosicionGPS(BaseModel):
    """Schema para posición GPS del conductor"""
    conductor_id: int
    latitud: float = Field(..., ge=-90, le=90)
    longitud: float = Field(..., ge=-180, le=180)
    precision_m: Optional[float] = Field(None, ge=0)
    altitud_m: Optional[float] = None
    velocidad_kmh: Optional[float] = Field(None, ge=0)
    direccion_grados: Optional[float] = Field(None, ge=0, le=360)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('latitud')
    def validar_latitud_ecuador(cls, v):
        if not (-5.0 <= v <= 2.0):
            raise ValueError('Latitud fuera del rango aproximado de Ecuador')
        return v
    
    @validator('longitud')
    def validar_longitud_ecuador(cls, v):
        if not (-92.0 <= v <= -75.0):
            raise ValueError('Longitud fuera del rango aproximado de Ecuador')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "conductor_id": 1,
                "latitud": -0.9356,
                "longitud": -78.6217,
                "precision_m": 10.5,
                "altitud_m": 2850.0,
                "velocidad_kmh": 45.0,
                "direccion_grados": 135.5,
                "timestamp": "2026-01-09T10:30:00Z"
            }
        }


class ResultadoValidacionGPS(BaseModel):
    """Resultado de validación de posición GPS"""
    valido: bool
    alertas_generadas: List[GeofenceAlertResponse] = []
    distancia_a_ruta_m: Optional[float] = None
    en_zona_correcta: bool = True
    calidad_gps: str  # 'buena', 'aceptable', 'mala'
    recomendaciones: List[str] = []
    estado_conductor: str  # 'en_ruta_normal', 'desviado', 'detenido', etc.


class EstadisticasGeofencing(BaseModel):
    """Estadísticas de geofencing para un conductor"""
    conductor_id: int
    nombre_conductor: str
    fecha_inicio: datetime
    fecha_fin: datetime
    total_alertas: int
    alertas_por_tipo: Dict[str, int]
    distancia_total_km: float
    tiempo_total_min: float
    velocidad_promedio_kmh: float
    velocidad_maxima_kmh: float
    porcentaje_tiempo_en_ruta: float
    desviaciones_promedio_m: float
    score_seguridad: float
    patron_conduccion: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "conductor_id": 1,
                "nombre_conductor": "Juan Pérez",
                "fecha_inicio": "2026-01-01T00:00:00Z",
                "fecha_fin": "2026-01-31T23:59:59Z",
                "total_alertas": 15,
                "alertas_por_tipo": {
                    "desviacion_ruta": 8,
                    "velocidad_excesiva": 5,
                    "parada_prolongada": 2
                },
                "distancia_total_km": 450.5,
                "tiempo_total_min": 1200,
                "velocidad_promedio_kmh": 42.3,
                "velocidad_maxima_kmh": 78.5,
                "porcentaje_tiempo_en_ruta": 92.5,
                "desviaciones_promedio_m": 125.0,
                "score_seguridad": 85.5,
                "patron_conduccion": "bueno"
            }
        }


class ReporteSeguridadMensual(BaseModel):
    """Reporte consolidado de seguridad mensual"""
    periodo: str
    total_conductores: int
    total_alertas: int
    conductores_con_alertas: int
    promedio_alertas_por_conductor: float
    tipo_alerta_mas_frecuente: str
    conductores_destacados: List[Dict[str, Any]]  # Top 5 mejores
    conductores_riesgo: List[Dict[str, Any]]  # Top 5 con más alertas
    tendencia_mensual: str  # 'mejorando', 'estable', 'empeorando'
    recomendaciones: List[str]


class AlertaWebSocket(BaseModel):
    """Schema para enviar alertas por WebSocket"""
    type: str = "geofence_alert"
    data: GeofenceAlertResponse
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    prioridad: str  # 'baja', 'media', 'alta'
    requiere_accion: bool = False
    accion_sugerida: Optional[str] = None
