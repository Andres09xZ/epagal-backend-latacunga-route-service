"""
Schemas Pydantic de la aplicación
"""
from app.schemas.incidencias import (
    TipoIncidencia,
    EstadoIncidencia,
    ZonaIncidencia,
    IncidenciaCreate,
    IncidenciaResponse,
    IncidenciaUpdate,
    IncidenciaStats
)

__all__ = [
    'TipoIncidencia',
    'EstadoIncidencia',
    'ZonaIncidencia',
    'IncidenciaCreate',
    'IncidenciaResponse',
    'IncidenciaUpdate',
    'IncidenciaStats'
]
