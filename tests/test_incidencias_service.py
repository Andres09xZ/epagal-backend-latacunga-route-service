"""
Tests unitarios — C2 (solo validadas) y C3 (umbral configurable)
Historia de Usuario TS-16: Agrupacion automatica de reportes para generar rutas
"""
import pytest
from unittest.mock import MagicMock, patch
from tests.conftest import make_incidencia
from app.services.incidencia_service import IncidenciaService


# ─────────────────────────────────────────────────────────────────
# C2 — Solo incidencias en estado "validado" se consideran
# ─────────────────────────────────────────────────────────────────

class TestClasificacionZona:
    """Clasificación automática de zona por longitud."""

    def test_longitud_oriental(self):
        zona = IncidenciaService.clasificar_zona(lon=-78.6140, lat=-0.9340)
        assert zona == "oriental"

    def test_longitud_occidental(self):
        zona = IncidenciaService.clasificar_zona(lon=-78.6200, lat=-0.9340)
        assert zona == "occidental"

    def test_lat_fuera_de_latacunga_lanza_error(self):
        with pytest.raises(ValueError, match="Latitud"):
            IncidenciaService.clasificar_zona(lon=-78.6140, lat=-2.0)

    def test_lon_fuera_de_latacunga_lanza_error(self):
        with pytest.raises(ValueError, match="Longitud"):
            IncidenciaService.clasificar_zona(lon=-79.5, lat=-0.9340)


class TestCalcularSumaGravedad:
    """C2: Solo las incidencias 'validado' cuentan para el umbral."""

    def test_suma_solo_incidencias_validadas(self):
        db = MagicMock()
        validadas = [
            make_incidencia(1, "zona_critica",  -0.9340, -78.6140, estado="validado"),
            make_incidencia(2, "animal_muerto", -0.9335, -78.6130, estado="validado"),
        ]
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = validadas
        db.query.return_value = mock_q

        suma = IncidenciaService.calcular_suma_gravedad_zona(db, "oriental")
        assert suma == 8  # zona_critica(3) + animal_muerto(5)

    def test_suma_cero_si_no_hay_validadas(self):
        db = MagicMock()
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = []
        db.query.return_value = mock_q

        suma = IncidenciaService.calcular_suma_gravedad_zona(db, "oriental")
        assert suma == 0

    def test_suma_todas_las_gravedades(self, incidencias_oriental):
        db = MagicMock()
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = incidencias_oriental
        db.query.return_value = mock_q

        suma = IncidenciaService.calcular_suma_gravedad_zona(db, "oriental")
        assert suma == 24  # 3+3+3+5+5+5

    @pytest.mark.parametrize("tipo,gravedad_esperada", [
        ("acopio",       1),
        ("zona_critica", 3),
        ("animal_muerto", 5),
    ])
    def test_gravedad_por_tipo(self, tipo, gravedad_esperada):
        db = MagicMock()
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = [make_incidencia(1, tipo, -0.9340, -78.6140)]
        db.query.return_value = mock_q

        suma = IncidenciaService.calcular_suma_gravedad_zona(db, "oriental")
        assert suma == gravedad_esperada


# ─────────────────────────────────────────────────────────────────
# C3 — Umbral de gravedad configurable
# ─────────────────────────────────────────────────────────────────

class TestVerificarUmbralRuta:
    """C3: El umbral de gravedad es configurable y se verifica estrictamente (>)."""

    def _mock_db_con_umbral(self, umbral: int, incidencias: list):
        db = MagicMock()

        cfg = MagicMock()
        cfg.valor = str(umbral)

        call_count = {"n": 0}

        def query_side(model):
            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q
            # Primera llamada → Config, segunda → Incidencias
            call_count["n"] += 1
            if call_count["n"] == 1:
                mock_q.first.return_value = cfg
            else:
                mock_q.all.return_value = incidencias
            return mock_q

        db.query.side_effect = query_side
        return db

    def test_supera_umbral_default_20(self, incidencias_oriental):
        """Suma=24 > umbral=20 → debe generar ruta."""
        db = self._mock_db_con_umbral(20, incidencias_oriental)
        debe_generar, suma = IncidenciaService.verificar_umbral_ruta(db, "oriental")
        assert debe_generar is True
        assert suma == 24

    def test_no_supera_umbral_default_20(self, incidencias_bajo_umbral):
        """Suma=6 > umbral=20 → False, no debe generar ruta."""
        db = self._mock_db_con_umbral(20, incidencias_bajo_umbral)
        debe_generar, suma = IncidenciaService.verificar_umbral_ruta(db, "oriental")
        assert debe_generar is False
        assert suma == 6

    def test_umbral_igual_a_suma_no_genera(self):
        """Suma=20 == umbral=20 → False (debe ser estrictamente mayor)."""
        incs = [
            make_incidencia(1, "animal_muerto", -0.9340, -78.6140),  # 5
            make_incidencia(2, "animal_muerto", -0.9335, -78.6130),  # 5
            make_incidencia(3, "animal_muerto", -0.9350, -78.6120),  # 5
            make_incidencia(4, "animal_muerto", -0.9328, -78.6145),  # 5
        ]  # suma = 20 exacto
        db = self._mock_db_con_umbral(20, incs)
        debe_generar, suma = IncidenciaService.verificar_umbral_ruta(db, "oriental")
        assert debe_generar is False
        assert suma == 20

    def test_umbral_personalizado_bajo(self, incidencias_bajo_umbral):
        """Con umbral=5, suma=6 → True."""
        db = self._mock_db_con_umbral(5, incidencias_bajo_umbral)
        debe_generar, suma = IncidenciaService.verificar_umbral_ruta(db, "oriental")
        assert debe_generar is True
        assert suma == 6

    def test_umbral_personalizado_alto(self, incidencias_oriental):
        """Con umbral=100, suma=24 → False."""
        db = self._mock_db_con_umbral(100, incidencias_oriental)
        debe_generar, suma = IncidenciaService.verificar_umbral_ruta(db, "oriental")
        assert debe_generar is False
        assert suma == 24


# ─────────────────────────────────────────────────────────────────
# Haversine — función auxiliar de distancias
# ─────────────────────────────────────────────────────────────────

class TestCalcularDistanciaHaversine:

    def test_mismo_punto_es_cero(self):
        d = IncidenciaService.calcular_distancia_haversine(
            -0.9340, -78.6140,
            -0.9340, -78.6140
        )
        assert d == pytest.approx(0.0, abs=1.0)

    def test_distancia_conocida_latacunga(self):
        """
        Parque Vicente León → Terminal Terrestre (~2 km aprox).
        Verificamos que el valor esté en rango razonable.
        """
        d = IncidenciaService.calcular_distancia_haversine(
            -0.9344, -78.6156,   # Parque Vicente León
            -0.9540, -78.6156    # ~2.2 km al sur
        )
        assert 2000 < d < 2500

    def test_distancia_es_simetrica(self):
        d1 = IncidenciaService.calcular_distancia_haversine(
            -0.9340, -78.6140, -0.9360, -78.6160
        )
        d2 = IncidenciaService.calcular_distancia_haversine(
            -0.9360, -78.6160, -0.9340, -78.6140
        )
        assert d1 == pytest.approx(d2, abs=0.1)

    def test_distancia_mayor_que_cero_puntos_distintos(self):
        d = IncidenciaService.calcular_distancia_haversine(
            -0.9340, -78.6140,
            -0.9360, -78.6160
        )
        assert d > 0
