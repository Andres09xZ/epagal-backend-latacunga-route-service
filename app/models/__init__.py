# app/models/__init__.py
# Re-exportar todos los modelos del archivo models.py para mantener compatibilidad
import sys
from pathlib import Path

# Importar todos los modelos del archivo models.py (un nivel arriba)
parent_models = Path(__file__).parent.parent / "models.py"
if parent_models.exists():
    # Cargar el módulo models.py
    import importlib.util
    spec = importlib.util.spec_from_file_location("_parent_models", parent_models)
    _parent_models = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_parent_models)
    
    # Re-exportar todo
    for name in dir(_parent_models):
        if not name.startswith('_'):
            globals()[name] = getattr(_parent_models, name)

# También importar los modelos del subdirectorio
from app.models.geofencing import *
"""
Paquete de modelos para el sistema EPAGAL
"""

# Exportar modelos de geofencing para facilitar importaciones
from app.models.geofencing import (
    GeofenceAlert,
    GeofenceConfig,
    ZonaGeografica,
    HistorialPosicion,
    EstadisticaGeofencing
)

__all__ = [
    'GeofenceAlert',
    'GeofenceConfig', 
    'ZonaGeografica',
    'HistorialPosicion',
    'EstadisticaGeofencing'
]
