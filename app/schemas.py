"""
Esquemas Pydantic para validación y serialización de datos
Fecha: 2025-12-13
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from datetime import datetime, timedelta
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class TipoIncidencia(str, Enum):
    ACOPIO = "acopio"
    ZONA_CRITICA = "zona_critica"
    ANIMAL_MUERTO = "animal_muerto"


class GravedadIncidencia(int, Enum):
    ACOPIO = 1
    ZONA_CRITICA = 3
    ANIMAL_MUERTO = 5


class EstadoIncidencia(str, Enum):
    PENDIENTE = "pendiente"
    ASIGNADA = "asignada"
    COMPLETADA = "completada"
    CANCELADA = "cancelada"


class Zona(str, Enum):
    ORIENTAL = "oriental"
    OCCIDENTAL = "occidental"


class TipoCamion(str, Enum):
    LATERAL = "lateral"
    POSTERIOR = "posterior"


class TipoPunto(str, Enum):
    DEPOSITO = "deposito"
    INCIDENCIA = "incidencia"
    BOTADERO = "botadero"


class EstadoRuta(str, Enum):
    PLANEADA = "planeada"
    EN_EJECUCION = "en_ejecucion"
    COMPLETADA = "completada"


# ============================================================================
# SCHEMAS - INCIDENCIAS
# ============================================================================

class IncidenciaBase(BaseModel):
    tipo: TipoIncidencia
    descripcion: Optional[str] = None
    lat: float = Field(..., ge=-90, le=90, description="Latitud entre -90 y 90")
    lon: float = Field(..., ge=-180, le=180, description="Longitud entre -180 y 180")
    foto_url: Optional[str] = None
    ventana_inicio: Optional[datetime] = None
    ventana_fin: Optional[datetime] = None

    @validator('gravedad', pre=True, always=True)
    def asignar_gravedad(cls, v, values):
        """Asigna gravedad automáticamente según el tipo"""
        if 'tipo' in values:
            tipo = values['tipo']
            if tipo == TipoIncidencia.ACOPIO:
                return 1
            elif tipo == TipoIncidencia.ZONA_CRITICA:
                return 3
            elif tipo == TipoIncidencia.ANIMAL_MUERTO:
                return 5
        return v


class IncidenciaCreate(IncidenciaBase):
    usuario_id: Optional[int] = None

    class Config:
        schema_extra = {
            "example": {
                "tipo": "animal_muerto",
                "descripcion": "Perro en la vía pública",
                "lat": -0.9365,
                "lon": -78.6135,
                "foto_url": "https://example.com/foto.jpg"
            }
        }


class IncidenciaUpdate(BaseModel):
    estado: Optional[EstadoIncidencia] = None
    zona: Optional[Zona] = None
    ventana_inicio: Optional[datetime] = None
    ventana_fin: Optional[datetime] = None


class IncidenciaResponse(IncidenciaBase):
    id: int
    gravedad: int
    zona: Optional[str]
    estado: str
    reportado_en: datetime
    utm_easting: Optional[float]
    utm_northing: Optional[float]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# SCHEMAS - RUTAS GENERADAS
# ============================================================================

class RutaGeneradaBase(BaseModel):
    zona: Zona
    suma_gravedad: int = Field(..., gt=0, description="Suma de gravedad de incidencias")
    costo_total: Optional[float] = None
    duracion_estimada: Optional[timedelta] = None
    camiones_usados: Optional[int] = Field(None, ge=1, description="Número de camiones")
    notas: Optional[str] = None


class RutaGeneradaCreate(RutaGeneradaBase):
    pass


class RutaGeneradaUpdate(BaseModel):
    estado: Optional[EstadoRuta] = None
    notas: Optional[str] = None


class RutaGeneradaResponse(RutaGeneradaBase):
    id: int
    fecha_generacion: datetime
    estado: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# SCHEMAS - RUTAS DETALLE
# ============================================================================

class RutaDetalleBase(BaseModel):
    camion_tipo: TipoCamion
    camion_id: Optional[str] = None
    orden: int = Field(..., ge=1, description="Orden en la secuencia de ruta")
    tipo_punto: TipoPunto
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lon: Optional[float] = Field(None, ge=-180, le=180)
    llegada_estimada: Optional[datetime] = None
    tiempo_servicio: Optional[timedelta] = timedelta(minutes=10)
    carga_acumulada: Optional[int] = Field(None, ge=0)


class RutaDetalleCreate(RutaDetalleBase):
    ruta_id: int
    incidencia_id: Optional[int] = None


class RutaDetalleResponse(RutaDetalleBase):
    id: int
    ruta_id: int
    incidencia_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# SCHEMAS - PUNTOS FIJOS
# ============================================================================

class PuntoFijoBase(BaseModel):
    nombre: str = Field(..., max_length=50)
    tipo: Literal["deposito", "botadero"]
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    activo: bool = True


class PuntoFijoCreate(PuntoFijoBase):
    pass


class PuntoFijoUpdate(BaseModel):
    activo: Optional[bool] = None


class PuntoFijoResponse(PuntoFijoBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# SCHEMAS - CONFIG
# ============================================================================

class ConfigBase(BaseModel):
    clave: str = Field(..., max_length=50)
    valor: str
    descripcion: Optional[str] = None
    tipo_dato: Literal["string", "integer", "float", "boolean"] = "string"


class ConfigCreate(ConfigBase):
    pass


class ConfigUpdate(BaseModel):
    valor: Optional[str] = None
    descripcion: Optional[str] = None


class ConfigResponse(ConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# SCHEMAS COMPUESTOS - RESPUESTAS EXTENDIDAS
# ============================================================================

class RutaCompletaResponse(RutaGeneradaResponse):
    """Ruta con todos sus detalles incluidos"""
    detalles: list[RutaDetalleResponse] = []

    class Config:
        from_attributes = True


class EstadisticasZona(BaseModel):
    """Estadísticas de incidencias por zona"""
    zona: Optional[str]
    total_incidencias: int
    suma_gravedad: int
    animales_muertos: int
    zonas_criticas: int
    acopios: int
    reporte_mas_antiguo: Optional[datetime]
    reporte_mas_reciente: Optional[datetime]


class ResumenSistema(BaseModel):
    """Resumen general del sistema"""
    incidencias_pendientes: int
    incidencias_asignadas: int
    suma_gravedad_pendiente: int
    rutas_activas: int
    ultima_ruta_generada: Optional[datetime]
    zona_oriental: Optional[EstadisticasZona]
    zona_occidental: Optional[EstadisticasZona]
