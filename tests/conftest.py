"""
Fixtures compartidas para tests unitarios de EPAGAL
"""
import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from app.models import Incidencia, Config


# ─────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────

GRAVEDAD_MAP = {
    "acopio": 1,
    "zona_critica": 3,
    "animal_muerto": 5,
}


def make_incidencia(id, tipo, lat, lon, zona="oriental", estado="validado"):
    """Crea una instancia mock de Incidencia con los valores dados."""
    inc = MagicMock(spec=Incidencia)
    inc.id = id
    inc.tipo = tipo
    inc.lat = lat
    inc.lon = lon
    inc.zona = zona
    inc.estado = estado
    inc.gravedad = GRAVEDAD_MAP[tipo]
    inc.descripcion = f"Descripcion de prueba para {tipo}"
    inc.foto_url = "/fotos_incidencias/test.jpg"
    inc.usuario_id = 1
    return inc


def make_config_mock(umbral=20, radio_km=3.0, intervalo_min=30):
    """Crea un mock de Config con los parámetros dados."""
    cfg = MagicMock(spec=Config)
    cfg.umbral_gravedad = umbral
    cfg.radio_clustering_km = radio_km
    cfg.intervalo_agrupacion_minutos = intervalo_min
    cfg.get_valor_convertido.return_value = umbral
    cfg.valor = str(umbral)
    return cfg


# ─────────────────────────────────────────────────────────────────
# Fixtures de base de datos
# ─────────────────────────────────────────────────────────────────

@pytest.fixture
def db():
    """Sesión de BD mock. No conecta a ninguna BD real."""
    return MagicMock(spec=Session)


@pytest.fixture
def db_con_config(db):
    """
    Sesión mock preconfigurada para devolver Config con
    umbral=20 y radio_clustering_km=3.0.
    """
    cfg_umbral = MagicMock()
    cfg_umbral.get_valor_convertido.return_value = 20
    cfg_umbral.valor = "3.0"

    def _query_side_effect(model):
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.first.return_value = cfg_umbral
        mock_q.all.return_value = []
        return mock_q

    db.query.side_effect = _query_side_effect
    return db


# ─────────────────────────────────────────────────────────────────
# Fixtures de incidencias
# ─────────────────────────────────────────────────────────────────

@pytest.fixture
def incidencias_oriental():
    """
    6 incidencias en zona oriental muy cercanas entre sí (< 2 km).
    Suma gravedad = 3+3+3+5+5+5 = 24  → supera umbral 20.
    Deben formar UN solo cluster con radio=3 km.
    """
    return [
        make_incidencia(1, "zona_critica",  -0.9340, -78.6140),
        make_incidencia(2, "zona_critica",  -0.9335, -78.6130),
        make_incidencia(3, "zona_critica",  -0.9350, -78.6120),
        make_incidencia(4, "animal_muerto", -0.9328, -78.6145),
        make_incidencia(5, "animal_muerto", -0.9360, -78.6135),
        make_incidencia(6, "animal_muerto", -0.9322, -78.6128),
    ]


@pytest.fixture
def incidencias_bajo_umbral():
    """
    2 zona_critica → suma gravedad = 6  → NO supera umbral 20.
    """
    return [
        make_incidencia(1, "zona_critica", -0.9340, -78.6140),
        make_incidencia(2, "zona_critica", -0.9335, -78.6130),
    ]


@pytest.fixture
def incidencias_dos_clusters():
    """
    8 incidencias que forman 2 clusters geográficos separados > 5 km:
      Cluster A (centro Latacunga): 3 × zona_critica  = 9  pts
      Cluster B (norte,  ~5 km):   5 × animal_muerto = 25 pts  ← debe ganar
    Con radio=3 km deben quedar en clusters distintos.
    """
    return [
        # Cluster A — centro
        make_incidencia(1, "zona_critica",  -0.9340, -78.6140),
        make_incidencia(2, "zona_critica",  -0.9341, -78.6141),
        make_incidencia(3, "zona_critica",  -0.9342, -78.6142),
        # Cluster B — norte (latitud ~0.90, aprox 4 km al norte)
        make_incidencia(4, "animal_muerto", -0.9000, -78.6140),
        make_incidencia(5, "animal_muerto", -0.9001, -78.6141),
        make_incidencia(6, "animal_muerto", -0.9002, -78.6142),
        make_incidencia(7, "animal_muerto", -0.9003, -78.6143),
        make_incidencia(8, "animal_muerto", -0.9004, -78.6144),
    ]
