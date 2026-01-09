# features/steps/test_geofencing.py
from pytest_bdd import scenarios, given, when, then, parsers
from shapely.geometry import Point, Polygon
from datetime import datetime, timedelta
import pytest
import os

from app.models.geofencing import GeofenceConfig, ZonaGeografica
from app.schemas.geofencing import PosicionGPS
from app.services.geofencing_service import GeofencingService

# Cargar scenarios del feature
feature_file = os.path.join(os.path.dirname(__file__), '..', 'geofencing.feature')
scenarios(feature_file)


# ===================================================================
# FIXTURES
# ===================================================================

@pytest.fixture
def geofencing_service(db_session):
    """Servicio de geofencing con configuración"""
    # Configurar parámetros
    configs = [
        GeofenceConfig(parametro="velocidad_maxima_kmh", valor=80, unidad="km/h", activo=True),
        GeofenceConfig(parametro="distancia_desviacion_m", valor=500, unidad="metros", activo=True),
        GeofenceConfig(parametro="tiempo_parada_min", valor=15, unidad="minutos", activo=True),
        GeofenceConfig(parametro="precision_minima_gps_m", valor=50, unidad="metros", activo=True),
    ]
    
    for config in configs:
        db_session.add(config)
    db_session.commit()
    
    return GeofencingService(db_session)


@pytest.fixture
def conductor_con_ruta(db_session):
    """Crear conductor con ruta asignada"""
    from app.models import Conductor, Ruta, Incidencia
    
    conductor = Conductor(
        id=1,
        nombre="Juan Pérez",
        zona_asignada="occidental",
        estado="en_ruta"
    )
    db_session.add(conductor)
    
    ruta = Ruta(
        id=1,
        conductor_id=1,
        fecha=datetime.utcnow()
    )
    db_session.add(ruta)
    
    # Incidencias de la ruta
    incidencias = [
        Incidencia(id=1, ruta_id=1, latitud=-0.9356, longitud=-78.6217, descripcion="Depósito"),
        Incidencia(id=2, ruta_id=1, latitud=-0.9365, longitud=-78.6215, descripcion="Incidencia A"),
        Incidencia(id=3, ruta_id=1, latitud=-0.9375, longitud=-78.6210, descripcion="Incidencia B"),
    ]
    
    for inc in incidencias:
        db_session.add(inc)
    
    db_session.commit()
    db_session.refresh(conductor)
    
    return conductor


# ===================================================================
# STEPS: Background
# ===================================================================

@given('el sistema de geofencing está activo')
def sistema_geofencing_activo(geofencing_service):
    assert geofencing_service is not None
    assert geofencing_service.config['velocidad_maxima_kmh'] == 80


@given(parsers.parse('existen las siguientes configuraciones de alertas:\n{table}'))
def configuraciones_alertas(table, db_session):
    """Ya configuradas en fixture geofencing_service"""
    pass


# ===================================================================
# STEPS: Desviación de Ruta
# ===================================================================

@given(parsers.parse('el conductor "{nombre}" con ID {conductor_id:d} tiene una ruta asignada'))
def conductor_tiene_ruta(nombre, conductor_id, conductor_con_ruta):
    assert conductor_con_ruta.id == conductor_id
    assert conductor_con_ruta.nombre == nombre


@given(parsers.parse('la ruta pasa por los siguientes puntos:\n{table}'))
def ruta_con_puntos(table, conductor_con_ruta):
    # Ya definidos en fixture
    assert len(conductor_con_ruta.ruta_actual.incidencias) == 3


@when(parsers.parse('el conductor reporta su posición GPS:\n{table}'))
def reportar_posicion_gps(table, geofencing_service, conductor_con_ruta, context):
    lines = table.strip().split('\n')
    headers = [h.strip() for h in lines[0].split('|')[1:-1]]
    values = [v.strip() for v in lines[1].split('|')[1:-1]]
    data = dict(zip(headers, values))
    
    posicion = PosicionGPS(
        conductor_id=conductor_con_ruta.id,
        latitud=float(data['latitud']),
        longitud=float(data['longitud']),
        precision_m=float(data.get('precision_m', 10)),
        velocidad_kmh=float(data.get('velocidad_kmh', 0)) if 'velocidad_kmh' in data else None,
        timestamp=datetime.utcnow()
    )
    
    resultado = geofencing_service.procesar_posicion_gps(posicion, conductor_con_ruta.id)
    context['resultado_validacion'] = resultado


@then('NO se genera ninguna alerta')
def no_se_genera_alerta(context):
    resultado = context['resultado_validacion']
    assert len(resultado.alertas_generadas) == 0


@then(parsers.parse('la distancia a la ruta es menor a {distancia:d} metros'))
def distancia_menor_a(distancia, context):
    resultado = context['resultado_validacion']
    assert resultado.distancia_a_ruta_m is not None
    assert resultado.distancia_a_ruta_m < distancia


@then(parsers.parse('el estado del conductor es "{estado}"'))
def verificar_estado_conductor(estado, context):
    resultado = context['resultado_validacion']
    assert resultado.estado_conductor == estado


@given(parsers.parse('la ruta va desde ({lat1}, {lon1}) hasta ({lat2}, {lon2})'))
def ruta_desde_hasta(lat1, lon1, lat2, lon2, conductor_con_ruta):
    # Simplificado para el test
    pass


@then(parsers.parse('se genera una alerta de tipo "{tipo_alerta}"'))
def se_genera_alerta_tipo(tipo_alerta, context):
    resultado = context['resultado_validacion']
    assert len(resultado.alertas_generadas) > 0
    assert any(alerta.tipo == tipo_alerta for alerta in resultado.alertas_generadas)


@then(parsers.parse('la alerta contiene:\n{table}'))
def alerta_contiene(table, context):
    lines = table.strip().split('\n')
    resultado = context['resultado_validacion']
    alerta = resultado.alertas_generadas[0]
    
    # Verificar campos específicos
    for line in lines[1:]:  # Saltar header
        campo, valor = [v.strip() for v in line.split('|')[1:-1]]
        
        if campo == 'severidad':
            assert alerta.severidad == valor
        elif campo == 'conductor_id':
            assert alerta.conductor_id == int(valor)
        elif campo == 'distancia_desviacion_m':
            if 'aproximadamente' in valor:
                esperado = float(valor.split()[-1])
                assert abs(alerta.distancia_desviacion_m - esperado) < 100
        elif campo == 'latitud_actual':
            assert abs(alerta.latitud - float(valor)) < 0.001


@then('se notifica al operador en tiempo real')
def notificar_operador(context):
    # Mock de notificación
    resultado = context['resultado_validacion']
    assert len(resultado.alertas_generadas) > 0


@then('se registra el evento en la base de datos')
def evento_registrado_bd(context, db_session):
    from app.models.geofencing import GeofenceAlert
    alertas = db_session.query(GeofenceAlert).all()
    assert len(alertas) > 0


# ===================================================================
# STEPS: Velocidad
# ===================================================================

@given(parsers.parse('el conductor con ID {conductor_id:d} está en ruta'))
def conductor_en_ruta(conductor_id, conductor_con_ruta):
    assert conductor_con_ruta.id == conductor_id


@when(parsers.parse('el conductor reporta velocidad de {velocidad:d} km/h'))
def reportar_velocidad(velocidad, geofencing_service, conductor_con_ruta, context):
    posicion = PosicionGPS(
        conductor_id=conductor_con_ruta.id,
        latitud=-0.9360,
        longitud=-78.6216,
        velocidad_kmh=float(velocidad),
        timestamp=datetime.utcnow()
    )
    
    resultado = geofencing_service.procesar_posicion_gps(posicion, conductor_con_ruta.id)
    context['resultado_validacion'] = resultado


@then('NO se genera alerta de velocidad')
def no_alerta_velocidad(context):
    resultado = context['resultado_validacion']
    alertas_velocidad = [a for a in resultado.alertas_generadas if a.tipo == 'velocidad_excesiva']
    assert len(alertas_velocidad) == 0


@then('se registra la velocidad en el historial')
def velocidad_en_historial(db_session):
    from app.models.geofencing import HistorialPosicion
    posiciones = db_session.query(HistorialPosicion).all()
    assert len(posiciones) > 0


@given(parsers.parse('el límite de velocidad es {limite:d} km/h'))
def limite_velocidad(limite, geofencing_service):
    assert geofencing_service.config['velocidad_maxima_kmh'] == limite


@then('se envía notificación al conductor')
def notificar_conductor(context):
    # Mock de notificación móvil
    assert len(context['resultado_validacion'].alertas_generadas) > 0


@then('se registra el evento con timestamp')
def evento_con_timestamp(context):
    alerta = context['resultado_validacion'].alertas_generadas[0]
    assert alerta.timestamp is not None


# ===================================================================
# STEPS: Paradas Prolongadas
# ===================================================================

@when(parsers.parse('el conductor permanece detenido durante {minutos:d} minutos en:\n{table}'))
def conductor_detenido(minutos, table, geofencing_service, conductor_con_ruta, context, db_session):
    lines = table.strip().split('\n')
    headers = [h.strip() for h in lines[0].split('|')[1:-1]]
    values = [v.strip() for v in lines[1].split('|')[1:-1]]
    data = dict(zip(headers, values))
    
    # Simular primera posición hace X minutos
    from app.models.geofencing import HistorialPosicion
    tiempo_inicial = datetime.utcnow() - timedelta(minutes=minutos)
    
    posicion_inicial = HistorialPosicion(
        conductor_id=conductor_con_ruta.id,
        latitud=float(data['latitud']),
        longitud=float(data['longitud']),
        velocidad_kmh=0,
        timestamp=tiempo_inicial
    )
    db_session.add(posicion_inicial)
    db_session.commit()
    
    # Reportar posición actual (misma ubicación)
    posicion_actual = PosicionGPS(
        conductor_id=conductor_con_ruta.id,
        latitud=float(data['latitud']),
        longitud=float(data['longitud']),
        velocidad_kmh=0,
        timestamp=datetime.utcnow()
    )
    
    resultado = geofencing_service.procesar_posicion_gps(posicion_actual, conductor_con_ruta.id)
    context['resultado_validacion'] = resultado


@then('NO se genera alerta de parada prolongada')
def no_alerta_parada(context):
    resultado = context['resultado_validacion']
    alertas_parada = [a for a in resultado.alertas_generadas if a.tipo == 'parada_prolongada']
    assert len(alertas_parada) == 0


@then('se registra la parada como normal')
def parada_normal(context):
    # Verificar que no hay alertas críticas
    resultado = context['resultado_validacion']
    assert all(a.severidad != 'critical' for a in resultado.alertas_generadas)


# ===================================================================
# STEPS: Zonas Geográficas
# ===================================================================

@given(parsers.parse('el conductor con ID {conductor_id:d} está asignado a zona "{zona}"'))
def conductor_asignado_zona(conductor_id, zona, conductor_con_ruta):
    conductor_con_ruta.zona_asignada = zona
    assert conductor_con_ruta.zona_asignada == zona


@given(parsers.parse('el área de cobertura de EPAGAL está delimitada por:\n{table}'))
def area_cobertura_epagal(table, db_session):
    lines = table.strip().split('\n')
    coords = []
    
    for line in lines[1:]:  # Saltar header
        lat, lon = [v.strip() for v in line.split('|')[1:-1]]
        coords.append((float(lon), float(lat)))  # lon, lat para Shapely
    
    # Cerrar polígono
    coords.append(coords[0])
    
    from geoalchemy2.shape import from_shape
    poligono = Polygon(coords)
    
    zona = ZonaGeografica(
        nombre="cobertura_epagal",
        tipo="cobertura",
        geometria=from_shape(poligono, srid=4326),
        activa=True
    )
    
    db_session.add(zona)
    db_session.commit()


@when(parsers.parse('la posición está dentro de zona "{zona}"'))
def posicion_en_zona(zona, context):
    resultado = context['resultado_validacion']
    assert resultado.en_zona_correcta


@then('NO se genera alerta de zona')
def no_alerta_zona(context):
    resultado = context['resultado_validacion']
    alertas_zona = [a for a in resultado.alertas_generadas 
                    if a.tipo in ['fuera_zona_cobertura', 'zona_incorrecta']]
    assert len(alertas_zona) == 0


# ===================================================================
# STEPS: Precisión GPS
# ===================================================================

@when(parsers.parse('el conductor reporta posición con precisión de {precision:d} metros'))
def reportar_con_precision(precision, geofencing_service, conductor_con_ruta, context):
    posicion = PosicionGPS(
        conductor_id=conductor_con_ruta.id,
        latitud=-0.9360,
        longitud=-78.6216,
        precision_m=float(precision),
        velocidad_kmh=40,
        timestamp=datetime.utcnow()
    )
    
    resultado = geofencing_service.procesar_posicion_gps(posicion, conductor_con_ruta.id)
    context['resultado_validacion'] = resultado


@then('los datos GPS se aceptan')
def datos_aceptados(context):
    resultado = context['resultado_validacion']
    assert resultado.valido


@then('se procesa la posición normalmente')
def posicion_procesada(context, db_session):
    from app.models.geofencing import HistorialPosicion
    posiciones = db_session.query(HistorialPosicion).all()
    assert len(posiciones) > 0


@given(parsers.parse('la precisión mínima requerida es {precision:d} metros'))
def precision_minima(precision, geofencing_service):
    assert geofencing_service.config['precision_minima_gps_m'] == precision


@then('la posición NO se usa para cálculos críticos')
def posicion_no_critica(context):
    resultado = context['resultado_validacion']
    assert resultado.calidad_gps == 'mala'


@then('se notifica al conductor para mejorar señal GPS')
def notificar_mejorar_gps(context):
    resultado = context['resultado_validacion']
    assert any('GPS' in rec for rec in resultado.recomendaciones)


# ===================================================================
# PYTEST HOOKS
# ===================================================================

@pytest.fixture
def context():
    """Context compartido entre steps"""
    return {}
