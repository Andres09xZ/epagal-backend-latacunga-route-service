"""
Schemas Pydantic para horarios de recolección
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime, date, time, timedelta
from enum import Enum


class ZonaEnum(str, Enum):
    """Zonas de Latacunga"""
    ORIENTAL = "oriental"
    OCCIDENTAL = "occidental"


class TipoRecoleccion(str, Enum):
    """Tipos de recolección"""
    DOMESTICA = "domestica"
    COMERCIAL = "comercial"
    BARRIDO = "barrido"


class CamionTipo(str, Enum):
    """Tipos de camión"""
    LATERAL = "lateral"
    POSTERIOR = "posterior"


class EstadoEjecucion(str, Enum):
    """Estados de ejecución de horarios"""
    PROGRAMADA = "programada"
    EN_CURSO = "en_curso"
    COMPLETADA = "completada"
    CANCELADA = "cancelada"
    ATRASADA = "atrasada"


# ============================================
# SECTORES
# ============================================

class SectorCreate(BaseModel):
    """Schema para crear un sector"""
    nombre: str = Field(..., min_length=3, max_length=100)
    zona: ZonaEnum
    poligono: dict  # GeoJSON
    coordenadas_centro: dict  # GeoJSON Point
    poblacion_estimada: Optional[int] = None
    cantidad_viviendas: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "nombre": "La Matriz",
                "zona": "occidental",
                "poligono": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-78.6191, -0.9344],
                        [-78.6150, -0.9344],
                        [-78.6150, -0.9300],
                        [-78.6191, -0.9300],
                        [-78.6191, -0.9344]
                    ]]
                },
                "coordenadas_centro": {
                    "type": "Point",
                    "coordinates": [-78.6170, -0.9322]
                },
                "poblacion_estimada": 5000,
                "cantidad_viviendas": 1200
            }
        }


class SectorResponse(BaseModel):
    """Schema para respuesta de sector"""
    id: int
    nombre: str
    zona: str
    poblacion_estimada: Optional[int]
    cantidad_viviendas: Optional[int]
    activo: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SectorDetalle(SectorResponse):
    """Schema detallado de sector con geometría"""
    poligono: Optional[dict] = None
    coordenadas_centro: Optional[dict] = None
    cantidad_horarios: int = 0


# ============================================
# HORARIOS DE RECOLECCIÓN
# ============================================

class HorarioCreate(BaseModel):
    """Schema para crear un horario de recolección"""
    sector_id: int
    dias_semana: List[int] = Field(..., min_length=1, max_length=7)  # [1,3,5] = Lun, Mié, Vie
    hora_inicio: str = Field(..., pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    hora_fin: str = Field(..., pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    tipo: TipoRecoleccion = TipoRecoleccion.DOMESTICA
    descripcion: Optional[str] = None
    camion_tipo: Optional[CamionTipo] = None
    conductor_id: Optional[int] = None
    camion_placa: Optional[str] = None
    fecha_inicio_vigencia: date

    @field_validator('dias_semana')
    @classmethod
    def validar_dias_semana(cls, v):
        """Valida que los días estén entre 1 y 7"""
        for dia in v:
            if dia < 1 or dia > 7:
                raise ValueError(f"Día {dia} inválido. Debe estar entre 1 (Lun) y 7 (Dom)")
        return sorted(list(set(v)))  # Eliminar duplicados y ordenar

    class Config:
        json_schema_extra = {
            "example": {
                "sector_id": 1,
                "dias_semana": [1, 3, 5],
                "hora_inicio": "06:00",
                "hora_fin": "08:00",
                "tipo": "domestica",
                "descripcion": "Recolección domiciliaria matutina",
                "camion_tipo": "posterior",
                "fecha_inicio_vigencia": "2026-01-06"
            }
        }


class HorarioUpdate(BaseModel):
    """Schema para actualizar un horario"""
    dias_semana: Optional[List[int]] = None
    hora_inicio: Optional[str] = None
    hora_fin: Optional[str] = None
    tipo: Optional[TipoRecoleccion] = None
    descripcion: Optional[str] = None
    camion_tipo: Optional[CamionTipo] = None
    conductor_id: Optional[int] = None
    camion_placa: Optional[str] = None
    activo: Optional[bool] = None
    fecha_fin_vigencia: Optional[date] = None


class HorarioResponse(BaseModel):
    """Schema para respuesta de horario"""
    id: int
    sector_id: int
    sector_nombre: Optional[str] = None
    dias_semana: str
    dias_semana_nombres: List[str] = []
    hora_inicio: str
    hora_fin: str
    tipo: str
    descripcion: Optional[str]
    camion_tipo: Optional[str]
    conductor_id: Optional[int]
    conductor_nombre: Optional[str] = None
    camion_placa: Optional[str]
    distancia_km: Optional[float]
    duracion_estimada_minutos: Optional[int] = None
    activo: bool
    fecha_inicio_vigencia: datetime
    fecha_fin_vigencia: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================
# EJECUCIONES DE HORARIOS
# ============================================

class EjecucionCreate(BaseModel):
    """Schema para crear una ejecución de horario (usado internamente)"""
    horario_id: int
    fecha_programada: date
    hora_inicio_programada: str
    hora_fin_programada: str
    conductor_id: int
    camion_placa: str


class EjecucionIniciar(BaseModel):
    """Schema para iniciar una ejecución"""
    camion_placa: str
    observaciones: Optional[str] = None


class EjecucionFinalizar(BaseModel):
    """Schema para finalizar una ejecución"""
    toneladas_recolectadas: Optional[float] = Field(None, ge=0)
    viviendas_atendidas: Optional[int] = Field(None, ge=0)
    observaciones: Optional[str] = None
    incidentes: Optional[str] = None


class TrackingGPS(BaseModel):
    """Schema para punto de tracking GPS"""
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    velocidad: Optional[float] = Field(None, ge=0)


class EjecucionResponse(BaseModel):
    """Schema para respuesta de ejecución"""
    id: int
    horario_id: int
    sector_nombre: Optional[str] = None
    fecha_programada: datetime
    hora_inicio_programada: str
    hora_fin_programada: str
    fecha_inicio_real: Optional[datetime]
    fecha_fin_real: Optional[datetime]
    conductor_id: int
    conductor_nombre: Optional[str] = None
    camion_placa: str
    estado: str
    porcentaje_cumplimiento: Optional[float]
    observaciones: Optional[str]
    incidentes: Optional[str]
    toneladas_recolectadas: Optional[float]
    viviendas_atendidas: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class EjecucionDetalle(EjecucionResponse):
    """Schema detallado de ejecución con ruta"""
    ruta_recorrida: Optional[dict] = None  # GeoJSON
    cantidad_puntos_tracking: int = 0
    duracion_real_minutos: Optional[int] = None
    retraso_minutos: Optional[int] = None


# ============================================
# SUSPENSIONES
# ============================================

class SuspensionCreate(BaseModel):
    """Schema para crear una suspensión"""
    horario_id: int
    fecha_suspension: date
    motivo: str = Field(..., min_length=5)
    fecha_recuperacion: Optional[date] = None

    class Config:
        json_schema_extra = {
            "example": {
                "horario_id": 1,
                "fecha_suspension": "2026-01-01",
                "motivo": "Feriado nacional - Año Nuevo",
                "fecha_recuperacion": "2026-01-02"
            }
        }


class SuspensionResponse(BaseModel):
    """Schema para respuesta de suspensión"""
    id: int
    horario_id: int
    sector_nombre: Optional[str] = None
    fecha_suspension: datetime
    motivo: str
    fecha_recuperacion: Optional[datetime]
    notificado: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================
# CALENDARIO Y ESTADÍSTICAS
# ============================================

class CalendarioSemana(BaseModel):
    """Schema para calendario semanal"""
    fecha_inicio: date
    fecha_fin: date
    ejecuciones: List[EjecucionResponse]


class EstadisticasHorario(BaseModel):
    """Schema para estadísticas de un horario"""
    horario_id: int
    total_ejecuciones: int
    completadas: int
    en_curso: int
    canceladas: int
    atrasadas: int
    promedio_cumplimiento: float
    total_toneladas: float
    total_viviendas: int


class EstadisticasConductor(BaseModel):
    """Schema para estadísticas de conductor"""
    conductor_id: int
    conductor_nombre: str
    total_ejecuciones: int
    completadas: int
    promedio_cumplimiento: float
    total_toneladas: float
    total_viviendas: int


class ResumenDiario(BaseModel):
    """Schema para resumen diario"""
    fecha: date
    total_programadas: int
    completadas: int
    en_curso: int
    atrasadas: int
    canceladas: int
    porcentaje_cumplimiento: float
    total_toneladas: float
    total_viviendas: int
