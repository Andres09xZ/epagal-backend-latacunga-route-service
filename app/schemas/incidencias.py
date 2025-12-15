"""
Schemas Pydantic para incidencias
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum


class TipoIncidencia(str, Enum):
    """Tipos de incidencia con su gravedad asociada"""
    ACOPIO = "acopio"  # gravedad 1
    ZONA_CRITICA = "zona_critica"  # gravedad 3
    ANIMAL_MUERTO = "animal_muerto"  # gravedad 5


class EstadoIncidencia(str, Enum):
    """Estados posibles de una incidencia"""
    PENDIENTE = "pendiente"
    VALIDADA = "validada"  # Incidencia validada antes de asignarse
    ASIGNADA = "asignada"
    COMPLETADA = "completada"
    CANCELADA = "cancelada"


class ZonaIncidencia(str, Enum):
    """Zonas de Latacunga"""
    ORIENTAL = "oriental"
    OCCIDENTAL = "occidental"


class IncidenciaCreate(BaseModel):
    """Schema para crear una nueva incidencia"""
    tipo: TipoIncidencia
    descripcion: Optional[str] = None
    foto_url: Optional[str] = None
    lat: float = Field(..., ge=-90, le=90, description="Latitud entre -90 y 90")
    lon: float = Field(..., ge=-180, le=180, description="Longitud entre -180 y 180")
    usuario_id: Optional[int] = None

    @field_validator('lat')
    @classmethod
    def validar_latitud_latacunga(cls, v):
        """Valida que la latitud esté dentro de Latacunga"""
        LAT_MIN, LAT_MAX = -0.97, -0.90
        if not (LAT_MIN <= v <= LAT_MAX):
            raise ValueError(
                f"Latitud {v} fuera del rango de Latacunga ({LAT_MIN} a {LAT_MAX})"
            )
        return v
    
    @field_validator('lon')
    @classmethod
    def validar_longitud_latacunga(cls, v):
        """Valida que la longitud esté dentro de Latacunga"""
        LON_MIN, LON_MAX = -78.65, -78.58
        if not (LON_MIN <= v <= LON_MAX):
            raise ValueError(
                f"Longitud {v} fuera del rango de Latacunga ({LON_MIN} a {LON_MAX})"
            )
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "tipo": "acopio",
                "descripcion": "Punto de acopio en esquina principal",
                "lat": -0.9344,
                "lon": -78.6156,
                "usuario_id": 123
            }
        }

class IncidenciaResponse(BaseModel):
    """Schema para respuesta de incidencia"""
    id: int
    tipo: str
    gravedad: int
    descripcion: Optional[str]
    foto_url: Optional[str]
    lat: float
    lon: float
    zona: Optional[str]
    estado: str
    ventana_inicio: Optional[datetime]
    ventana_fin: Optional[datetime]
    reportado_en: datetime
    usuario_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class IncidenciaUpdate(BaseModel):
    """Schema para actualizar una incidencia"""
    estado: Optional[EstadoIncidencia] = None
    descripcion: Optional[str] = None
    foto_url: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "estado": "completada",
                "descripcion": "Recolectado exitosamente"
            }
        }


class IncidenciaStats(BaseModel):
    """Estadísticas de incidencias"""
    total: int
    pendientes: int
    validadas: int
    asignadas: int
    completadas: int
    por_tipo: dict
    por_zona: dict
