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
    EMITIDO = "emitido"          # Ciudadano reporta la incidencia
    RECIBIDO = "recibido"        # Operador recibe y registra
    VALIDADO = "validado"        # Operador valida la incidencia
    EN_EJECUCION = "en_ejecucion"  # Conductor en camino / atendiendo
    FINALIZADO = "finalizado"    # Incidencia atendida exitosamente
    RECHAZADO = "rechazado"      # Incidencia rechazada/cancelada


class ZonaIncidencia(str, Enum):
    """Zonas de Latacunga"""
    ORIENTAL = "oriental"
    OCCIDENTAL = "occidental"


class IncidenciaCreate(BaseModel):
    """Schema para crear una nueva incidencia"""
    tipo: TipoIncidencia
    descripcion: str = Field(..., min_length=10, description="Descripción de la incidencia (mínimo 10 caracteres)")
    foto_url: str = Field(..., description="URL de la foto adjunta (obligatoria)")
    lat: float = Field(..., ge=-90, le=90, description="Latitud entre -90 y 90")
    lon: float = Field(..., ge=-180, le=180, description="Longitud entre -180 y 180")
    usuario_id: int = Field(..., description="ID del ciudadano que reporta la incidencia")

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
    
    def determinar_zona(self) -> str:
        """
        Determina la zona basándose en las coordenadas
        Zona Oriental: longitud > -78.6191 (este de Latacunga)
        Zona Occidental: longitud <= -78.6191 (oeste de Latacunga)
        """
        LONGITUD_DIVISORIA = -78.6191
        return "oriental" if self.lon > LONGITUD_DIVISORIA else "occidental"

    class Config:
        json_schema_extra = {
            "example": {
                "tipo": "animal_muerto",
                "descripcion": "Animal muerto en la calle principal frente al parque",
                "foto_url": "https://storage.epagal.gob.ec/fotos/incidencia_001.jpg",
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
