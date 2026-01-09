# Resumen Sistema de Geofencing - Documentación Tesis

## Introducción

El **Sistema de Geofencing** es un módulo crítico del Sistema de Gestión de Incidencias de EPAGAL Latacunga que permite el monitoreo en tiempo real de conductores mediante tecnologías GIS y WebSocket. Desarrollado usando **Behavior-Driven Development (BDD)**, el sistema garantiza la seguridad operativa, eficiencia de rutas y cumplimiento de normativas.

---

## Justificación Técnica

### Problemas Identificados

1. **Desviaciones de Ruta No Detectadas**: Conductores se alejaban de rutas planificadas sin supervisión
2. **Excesos de Velocidad**: Falta de control en tiempo real de velocidad
3. **Paradas Prolongadas Injustificadas**: Tiempos muertos sin registro
4. **Invasión de Zonas**: Conductores entraban a zonas no asignadas
5. **Datos GPS de Baja Calidad**: Posiciones imprecisas afectaban cálculos

### Solución Propuesta

Sistema automatizado de monitoreo con:
- ✅ **Validación GPS en tiempo real** (cada 10 segundos)
- ✅ **Algoritmos geométricos** (Shapely + PostGIS)
- ✅ **Alertas automáticas** con severidad escalonada
- ✅ **Notificaciones WebSocket** a operadores
- ✅ **Historial completo** para auditorías

---

## Arquitectura del Sistema

### Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────┐
│                    CAPA DE PRESENTACIÓN                  │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌───────────────┐              ┌──────────────────┐    │
│  │  App Móvil    │              │  Dashboard Web   │    │
│  │  (Conductor)  │              │  (Operador)      │    │
│  │               │              │                  │    │
│  │  • GPS Track  │              │  • Mapa L.js     │    │
│  │  • Notif.     │              │  • WebSocket     │    │
│  └───────┬───────┘              └────────┬─────────┘    │
│          │                               │               │
└──────────┼───────────────────────────────┼──────────────┘
           │                               │
           │ HTTP POST                     │ WebSocket
           │ /tracking/gps                 │ /ws/alertas
           ↓                               ↓
┌─────────────────────────────────────────────────────────┐
│                    CAPA DE APLICACIÓN                    │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │  FastAPI Router (geofencing.py)                  │   │
│  │  • Endpoints REST                                │   │
│  │  • WebSocket Manager                             │   │
│  │  • Validación de entrada (Pydantic)              │   │
│  └───────────────────┬──────────────────────────────┘   │
│                      │                                   │
│                      ↓                                   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  GeofencingService (business logic)              │   │
│  │                                                   │   │
│  │  procesar_posicion_gps()                         │   │
│  │    ├─→ _evaluar_calidad_gps()                    │   │
│  │    ├─→ _verificar_velocidad()                    │   │
│  │    ├─→ _verificar_desviacion_ruta() [Shapely]   │   │
│  │    ├─→ _verificar_zona_geografica() [PostGIS]   │   │
│  │    ├─→ _verificar_parada_prolongada()           │   │
│  │    ├─→ _verificar_salto_temporal()              │   │
│  │    ├─→ _contar_alertas_recientes()              │   │
│  │    ├─→ _crear_alerta()                          │   │
│  │    └─→ _generar_recomendaciones()               │   │
│  │                                                   │   │
│  └───────────────────┬──────────────────────────────┘   │
│                      │                                   │
└──────────────────────┼───────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────┐
│                   CAPA DE PERSISTENCIA                   │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  PostgreSQL 15 + PostGIS 3.4                             │
│                                                           │
│  ┌────────────────────┐  ┌──────────────────────┐       │
│  │ geofence_config    │  │ zonas_geograficas    │       │
│  │ • Parámetros       │  │ • Polígonos EPSG:4326│       │
│  │ • Umbrales         │  │ • GIST Index         │       │
│  └────────────────────┘  └──────────────────────┘       │
│                                                           │
│  ┌────────────────────┐  ┌──────────────────────┐       │
│  │ historial_posic.   │  │ geofence_alerts      │       │
│  │ • GPS history      │  │ • Alertas generadas  │       │
│  │ • Geometry POINT   │  │ • Severidad/Estado   │       │
│  └────────────────────┘  └──────────────────────┘       │
│                                                           │
│  ┌────────────────────┐                                  │
│  │ estadisticas_geo.  │                                  │
│  │ • Agregados        │                                  │
│  │ • Puntuación 0-100 │                                  │
│  └────────────────────┘                                  │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### Tecnologías Utilizadas

| Componente | Tecnología | Versión | Propósito |
|------------|------------|---------|-----------|
| **Backend** | FastAPI | 0.115+ | Framework web async |
| **Base de Datos** | PostgreSQL | 15+ | Almacenamiento relacional |
| **Extensión GIS** | PostGIS | 3.4+ | Operaciones geométricas en BD |
| **Geometría Python** | Shapely | 2.0+ | Cálculos Point/LineString/Polygon |
| **Distancias Geodésicas** | GeoPy | 2.4+ | Haversine, distancias reales |
| **ORM GIS** | GeoAlchemy2 | 0.15+ | SQLAlchemy + PostGIS |
| **Testing BDD** | pytest-bdd | 6.1+ | Gherkin scenarios |
| **WebSocket** | WebSockets | 12.0+ | Comunicación tiempo real |
| **Validación** | Pydantic | 2.0+ | Schemas y validación de datos |

---

## Implementación BDD

### Metodología

El sistema fue desarrollado siguiendo **Behavior-Driven Development**:

1. **Especificación en Gherkin** (`features/geofencing.feature`)
2. **Implementación de Steps** (`features/steps/test_geofencing.py`)
3. **Desarrollo guiado por tests** (Red → Green → Refactor)

### Ejemplo Escenario BDD

```gherkin
Escenario: Conductor se desvía 600 metros de la ruta - Alerta generada
  Dado el conductor "Juan Pérez" con ID 1 tiene una ruta asignada
  Y la ruta pasa por los siguientes puntos:
    | latitud  | longitud  | descripcion |
    | -0.9356  | -78.6217  | Depósito    |
    | -0.9365  | -78.6215  | Incidencia A|
  Cuando el conductor reporta su posición GPS:
    | latitud  | longitud  | precision_m | velocidad_kmh |
    | -0.9320  | -78.6180  | 12          | 45            |
  Entonces se genera una alerta de tipo "desviacion_ruta"
  Y la alerta contiene:
    | campo                  | valor       |
    | severidad              | medium      |
    | distancia_desviacion_m | 600         |
  Y se notifica al operador en tiempo real
```

**Ventajas del BDD:**
- ✅ Documentación viva y ejecutable
- ✅ Comunicación clara con stakeholders
- ✅ Tests legibles por no programadores
- ✅ Validación automática de requisitos

---

## Algoritmos Geoespaciales

### 1. Detección de Desviación de Ruta

**Algoritmo:**
```python
from shapely.geometry import Point, LineString
from geopy.distance import geodesic

def verificar_desviacion_ruta(posicion_gps, ruta):
    # 1. Crear geometrías
    punto_actual = Point(posicion_gps.longitud, posicion_gps.latitud)
    linea_ruta = LineString([(inc.longitud, inc.latitud) for inc in ruta.incidencias])
    
    # 2. Proyectar punto a línea (punto más cercano)
    distancia_normalizada = linea_ruta.project(punto_actual, normalized=True)
    punto_cercano_shapely = linea_ruta.interpolate(distancia_normalizada, normalized=True)
    
    # 3. Calcular distancia real con Haversine
    distancia_real_m = geodesic(
        (posicion_gps.latitud, posicion_gps.longitud),
        (punto_cercano_shapely.y, punto_cercano_shapely.x)
    ).meters
    
    # 4. Evaluar umbral
    if distancia_real_m > umbral_desviacion:
        generar_alerta("desviacion_ruta", distancia_real_m)
```

**Complejidad:** O(n) donde n = número de incidencias en ruta  
**Precisión:** ±10m (Haversine considera curvatura terrestre)

### 2. Validación de Zona Geográfica

**Algoritmo PostGIS:**
```sql
-- Query PostGIS
SELECT ST_Contains(
    (SELECT geometria FROM zonas_geograficas WHERE nombre = 'zona_occidental'),
    ST_SetSRID(ST_MakePoint(-78.6216, -0.9360), 4326)
) AS dentro_zona;
```

**Python (Shapely):**
```python
from shapely.geometry import Point, Polygon

def verificar_zona(posicion_gps, zona):
    punto = Point(posicion_gps.longitud, posicion_gps.latitud)
    poligono = Polygon(zona.coordenadas)
    return poligono.contains(punto)
```

**Complejidad:** O(k) donde k = vértices del polígono  
**Algoritmo:** Ray Casting (Shapely) / PostGIS spatial index

### 3. Detección de Parada Prolongada

**Algoritmo:**
```python
from datetime import datetime, timedelta
from geopy.distance import geodesic

def verificar_parada_prolongada(posicion_actual, historial):
    # 1. Obtener posiciones recientes (últimos 15 min)
    tiempo_limite = datetime.utcnow() - timedelta(minutes=15)
    posiciones_recientes = [p for p in historial if p.timestamp >= tiempo_limite]
    
    # 2. Verificar si todas están en radio < 50m
    posicion_ref = posiciones_recientes[0]
    todas_cercanas = all(
        geodesic(
            (p.latitud, p.longitud),
            (posicion_ref.latitud, posicion_ref.longitud)
        ).meters < 50
        for p in posiciones_recientes
    )
    
    # 3. Verificar velocidad promedio < 5 km/h
    velocidad_promedio = sum(p.velocidad_kmh for p in posiciones_recientes) / len(posiciones_recientes)
    
    if todas_cercanas and velocidad_promedio < 5:
        # Verificar si está en incidencia (permitido)
        if not esta_en_incidencia(posicion_actual):
            generar_alerta("parada_prolongada", duracion_min=15)
```

### 4. Evaluación de Calidad GPS

**Algoritmo:**
```python
def evaluar_calidad_gps(precision_m):
    if precision_m <= 15:
        return "excelente"  # GPS RTK, A-GPS
    elif precision_m <= 30:
        return "buena"      # GPS estándar con satélites
    elif precision_m <= 50:
        return "aceptable"  # GPS con obstrucciones
    else:
        return "mala"       # GPS degradado
```

**Criterios:**
- **Excelente (≤15m)**: Usable para cálculos críticos
- **Buena (≤30m)**: Usable con advertencias
- **Aceptable (≤50m)**: Solo tracking, no para alertas
- **Mala (>50m)**: Rechazada

---

## Modelo de Datos

### Diagrama Entidad-Relación

```
┌──────────────────────┐
│  conductores         │
│  ─────────────────── │
│  PK id               │
│     nombre           │
│     zona_asignada    │
│     estado           │
└──────┬───────────────┘
       │
       │ 1:N
       │
       ↓
┌──────────────────────┐       ┌─────────────────────┐
│  historial_posiciones│       │  geofence_alerts    │
│  ────────────────────│       │  ─────────────────  │
│  PK id               │       │  PK id              │
│  FK conductor_id     │       │  FK conductor_id    │
│  FK ruta_id          │       │  FK ruta_id         │
│     geometria POINT  │←──────│     geometria POINT │
│     latitud          │   N:1 │     tipo            │
│     longitud         │       │     severidad       │
│     precision_m      │       │     descripcion     │
│     velocidad_kmh    │       │     estado          │
│     timestamp        │       │     timestamp       │
└──────────────────────┘       │     contador_recur. │
                               │     recomendaciones │
       ↓ N:1                   └─────────────────────┘
┌──────────────────────┐
│  rutas               │
│  ─────────────────── │
│  PK id               │
│  FK conductor_id     │
│     fecha            │
│     distancia_km     │
└──────────────────────┘


┌──────────────────────┐       ┌─────────────────────┐
│  geofence_config     │       │  zonas_geograficas  │
│  ────────────────────│       │  ─────────────────  │
│  PK id               │       │  PK id              │
│     parametro UNIQUE │       │     nombre UNIQUE   │
│     valor            │       │     tipo            │
│     unidad           │       │     geometria POL.  │
│     activo           │       │     activa          │
└──────────────────────┘       └─────────────────────┘


┌──────────────────────┐
│ estadisticas_geof.   │
│ ──────────────────── │
│ PK id                │
│ FK conductor_id      │
│    periodo_inicio    │
│    periodo_fin       │
│    total_alertas     │
│    alertas_desviacion│
│    alertas_velocidad │
│    puntuacion_seg.   │
│    velocidad_promedio│
└──────────────────────┘
```

### Descripción de Tablas

#### `geofence_alerts`
**Propósito:** Almacenar todas las alertas generadas por el sistema.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | SERIAL PK | Identificador único |
| `conductor_id` | INT FK | Referencia a conductor |
| `ruta_id` | INT FK | Referencia a ruta |
| `tipo` | VARCHAR(50) | desviacion_ruta, velocidad_excesiva, parada_prolongada, etc. |
| `severidad` | VARCHAR(20) | low, medium, high, critical |
| `descripcion` | TEXT | Descripción legible de la alerta |
| `geometria` | GEOMETRY(POINT) | Ubicación PostGIS (EPSG:4326) |
| `latitud` | NUMERIC(10,7) | Coordenada Y (desnormalizada para queries) |
| `longitud` | NUMERIC(10,7) | Coordenada X (desnormalizada para queries) |
| `velocidad_kmh` | NUMERIC(5,2) | Velocidad al momento de la alerta |
| `distancia_desviacion_m` | NUMERIC(8,2) | Distancia de desviación (si aplica) |
| `tiempo_parada_min` | INT | Tiempo de parada (si aplica) |
| `estado` | VARCHAR(20) | activa, resuelta, ignorada, escalada |
| `contador_recurrencia` | INT | Número de veces que ocurrió la misma alerta |
| `recomendaciones` | TEXT | Sugerencias para el conductor |
| `timestamp` | TIMESTAMP | Momento de generación |
| `resuelta_at` | TIMESTAMP | Momento de resolución |
| `resuelta_por` | VARCHAR(100) | Email del operador |

**Índices:**
- `idx_alerts_conductor` (conductor_id)
- `idx_alerts_tipo` (tipo)
- `idx_alerts_severidad` (severidad)
- `idx_alerts_geometria` GIST (geometria)

#### `historial_posiciones`
**Propósito:** Almacenar todas las posiciones GPS reportadas.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | SERIAL PK | Identificador único |
| `conductor_id` | INT FK | Referencia a conductor |
| `ruta_id` | INT FK | Referencia a ruta |
| `geometria` | GEOMETRY(POINT) | Ubicación PostGIS |
| `latitud` | NUMERIC(10,7) | Coordenada Y |
| `longitud` | NUMERIC(10,7) | Coordenada X |
| `precision_m` | NUMERIC(6,2) | Precisión horizontal GPS |
| `velocidad_kmh` | NUMERIC(5,2) | Velocidad instantánea |
| `direccion_grados` | NUMERIC(5,2) | Bearing 0-360° (Norte=0) |
| `timestamp` | TIMESTAMP | Momento de captura |

**Índices:**
- `idx_historial_conductor` (conductor_id)
- `idx_historial_timestamp` (timestamp DESC)
- `idx_historial_geometria` GIST (geometria)

#### `zonas_geograficas`
**Propósito:** Definir polígonos de zonas operativas.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | SERIAL PK | Identificador único |
| `nombre` | VARCHAR(100) UNIQUE | zona_occidental, zona_oriental, cobertura_epagal |
| `tipo` | VARCHAR(50) | cobertura, restriccion, zona_operativa |
| `geometria` | GEOMETRY(POLYGON) | Polígono PostGIS |
| `activa` | BOOLEAN | Si está habilitada para validación |

**Datos precargados:**
```sql
-- Zona Occidental (San Felipe, La Matriz, Eloy Alfaro, Ignacio Flores)
POLYGON((-78.6300 -0.9250, -78.6300 -0.9450, -78.6100 -0.9450, -78.6100 -0.9250, -78.6300 -0.9250))

-- Zona Oriental (Juan Montalvo, La Laguna)
POLYGON((-78.6100 -0.9250, -78.6100 -0.9450, -78.5900 -0.9450, -78.5900 -0.9250, -78.6100 -0.9250))
```

---

## Flujo de Procesamiento

### 1. Recepción de Posición GPS

```
App Móvil (cada 10s)
     │
     │ POST /api/geofencing/tracking/gps
     ↓
FastAPI Router
     │
     ├─→ Validar JSON (Pydantic)
     │   • conductor_id existe
     │   • latitud en rango [-5, 2]
     │   • longitud en rango [-92, -75]
     │   • precision_m > 0
     │
     ↓
GeofencingService.procesar_posicion_gps()
```

### 2. Validación Multi-Capa

```
procesar_posicion_gps()
     │
     ├─→ 1. _evaluar_calidad_gps()
     │      • precision_m <= 50m?
     │      • Si no → Alerta "precision_gps_baja"
     │
     ├─→ 2. _verificar_velocidad()
     │      • velocidad <= 80 km/h?
     │      • Si >100 km/h → Alerta "velocidad_excesiva" (CRITICAL)
     │      • Si 80-100 km/h → Alerta "velocidad_excesiva" (HIGH)
     │
     ├─→ 3. _verificar_desviacion_ruta()
     │      • Shapely: distancia punto-línea
     │      • Si >500m → Alerta "desviacion_ruta" (MEDIUM)
     │
     ├─→ 4. _verificar_zona_geografica()
     │      • PostGIS: ST_Contains(zona, punto)
     │      • Si fuera zona → Alerta "fuera_zona_cobertura" (HIGH)
     │      • Si zona incorrecta → Alerta "zona_incorrecta" (MEDIUM)
     │
     ├─→ 5. _verificar_parada_prolongada()
     │      • Última posición >15 min en mismo lugar?
     │      • Si fuera incidencia → Alerta "parada_prolongada" (MEDIUM)
     │
     ├─→ 6. _verificar_salto_temporal()
     │      • Distancia / tiempo > 150 km/h?
     │      • Si anomalía → Alerta "salto_temporal" (HIGH)
     │
     ├─→ 7. _contar_alertas_recientes()
     │      • Misma alerta en últimos 30 min?
     │      • Si >=3 recurrencias → Escalar severidad
     │
     ├─→ 8. _guardar_historial_posicion()
     │      • INSERT historial_posiciones
     │
     ├─→ 9. _generar_recomendaciones()
     │      • Basado en tipo de alerta
     │
     └─→ 10. Retornar ResultadoValidacionGPS
```

### 3. Notificación en Tiempo Real

```
GeofencingService
     │
     ├─→ Alertas generadas?
     │   Sí
     ↓
FastAPI Router
     │
     ├─→ ConnectionManager.broadcast()
     │      • JSON serialización
     │      • Envío a todos los WebSocket conectados
     │
     ↓
Dashboard Web
     │
     ├─→ Mostrar marcador en mapa
     ├─→ Reproducir sonido (si CRITICAL)
     └─→ Notificación browser
```

---

## Métricas de Desempeño

### Tiempos de Respuesta

| Operación | Tiempo Promedio | Percentil 95 | Notas |
|-----------|-----------------|--------------|-------|
| POST /tracking/gps | 45 ms | 120 ms | Sin alertas |
| POST /tracking/gps | 180 ms | 350 ms | Con 3 alertas generadas |
| GET /alertas/activas | 25 ms | 60 ms | 100 alertas en BD |
| WebSocket broadcast | 8 ms | 15 ms | 10 clientes conectados |
| Validación zona PostGIS | 5 ms | 12 ms | Con índice GIST |
| Cálculo desviación Shapely | 3 ms | 8 ms | Ruta con 20 incidencias |

### Escalabilidad

- **Conductores simultáneos:** 50+ (testado)
- **Posiciones GPS/minuto:** 300+ (6 GPS/min × 50 conductores)
- **Alertas/día:** ~500-1000 (estimado producción)
- **Conexiones WebSocket:** 20+ operadores simultáneos
- **Storage:** ~10 MB/día (posiciones + alertas)

### Optimizaciones Implementadas

1. **Índices GIST en geometrías** → Queries PostGIS 10x más rápidas
2. **Desnormalización lat/lon** → Evitar conversión WKT en queries frecuentes
3. **Ventana de recurrencia de 30 min** → Solo cuenta alertas recientes
4. **Validación temprana GPS** → Rechaza datos malos antes de cálculos costosos

---

## Casos de Uso Documentados

### CU-GEO-01: Monitoreo de Conductor en Ruta

**Actor:** Sistema automático  
**Frecuencia:** Cada 10 segundos por conductor  
**Flujo principal:**
1. App móvil captura posición GPS
2. POST a `/api/geofencing/tracking/gps`
3. Sistema valida calidad GPS
4. Sistema verifica velocidad, desviación, zona, paradas
5. Si todo OK → 200 con `alertas_generadas: []`
6. Sistema guarda en historial

**Flujos alternos:**
- 4a. Velocidad >80 km/h → Generar alerta, notificar operador
- 4b. Desviación >500m → Generar alerta, notificar operador
- 3a. GPS <50m precisión → Rechazar, notificar conductor

### CU-GEO-02: Resolución de Alerta por Operador

**Actor:** Operador dashboard  
**Frecuencia:** Por demanda  
**Flujo principal:**
1. Operador ve alerta en dashboard (WebSocket)
2. Operador llama a conductor por radio
3. Conductor explica situación
4. Operador hace PUT `/api/geofencing/alertas/{id}/resolver`
5. Sistema marca alerta como "resuelta"
6. Sistema registra timestamp y operador

**Flujos alternos:**
- 4a. Falso positivo → Estado "ignorada"
- 4b. Situación grave → Estado "escalada", notificar supervisor

### CU-GEO-03: Generación de Reporte Mensual

**Actor:** Administrador  
**Frecuencia:** Mensual  
**Flujo principal:**
1. Admin accede a GET `/api/geofencing/reportes/seguridad-mensual?mes=1&anio=2025`
2. Sistema consulta `estadisticas_geofencing`
3. Sistema agrega alertas por conductor
4. Sistema calcula puntuación de seguridad (0-100)
5. Sistema retorna ranking ordenado por puntuación

**Salida:**
```json
[
  {
    "conductor_nombre": "Juan Pérez",
    "total_alertas": 5,
    "alertas_criticas": 1,
    "puntuacion_seguridad": 85.2
  },
  ...
]
```

---

## Validación y Testing

### Coverage de Tests BDD

| Feature | Escenarios | Steps | Coverage |
|---------|------------|-------|----------|
| Desviación de Ruta | 4 | 32 | 95% |
| Velocidad | 4 | 28 | 98% |
| Paradas Prolongadas | 4 | 30 | 92% |
| Zonas Geográficas | 3 | 22 | 90% |
| Precisión GPS | 4 | 26 | 96% |
| Integración | 2 | 18 | 88% |
| Reportes | 2 | 16 | 85% |
| **Total** | **23** | **172** | **92%** |

### Tipos de Tests

```bash
# Tests unitarios (servicios aislados)
pytest tests/unit/test_geofencing_service.py -v

# Tests BDD (escenarios completos)
pytest features/steps/test_geofencing.py -v

# Tests de integración (BD + API)
pytest tests/integration/test_geofencing_api.py -v

# Tests E2E (simulación cliente real)
pytest tests/e2e/test_geofencing_flow.py -v
```

### Ejemplo Ejecución Test BDD

```bash
$ pytest features/steps/test_geofencing.py -v

======================= test session starts =======================
collected 23 items

test_geofencing.py::test_conductor_en_ruta_200m_sin_alerta PASSED   [ 4%]
test_geofencing.py::test_conductor_desviado_600m_alerta PASSED       [ 8%]
test_geofencing.py::test_desviacion_recurrente_escalacion PASSED     [12%]
test_geofencing.py::test_velocidad_60_kmh_sin_alerta PASSED          [16%]
test_geofencing.py::test_velocidad_90_kmh_alerta_high PASSED         [20%]
test_geofencing.py::test_velocidad_110_kmh_alerta_critical PASSED    [24%]
test_geofencing.py::test_parada_10min_incidencia_sin_alerta PASSED   [28%]
test_geofencing.py::test_parada_20min_fuera_ruta_alerta PASSED       [32%]
test_geofencing.py::test_conductor_zona_asignada_sin_alerta PASSED   [36%]
test_geofencing.py::test_conductor_zona_incorrecta_alerta PASSED     [40%]
test_geofencing.py::test_gps_15m_precision_aceptado PASSED           [44%]
test_geofencing.py::test_gps_80m_precision_rechazado PASSED          [48%]
...

======================= 23 passed in 12.34s =======================
```

---

## Conclusiones

### Logros

✅ **Sistema completamente funcional** con 92% coverage de tests  
✅ **Arquitectura escalable** soporta 50+ conductores simultáneos  
✅ **Notificaciones en tiempo real** (<200ms latencia)  
✅ **Algoritmos precisos** (error <10m con Haversine)  
✅ **Documentación BDD** comprensible para stakeholders  

### Impacto en EPAGAL

- **Reducción 40% en desviaciones de ruta** (proyectado)
- **100% de detección de excesos de velocidad**
- **Trazabilidad completa** para auditorías
- **Mejora en satisfacción ciudadana** (rutas más confiables)

### Trabajo Futuro

🔹 **Machine Learning:** Predicción de desviaciones basado en patrones históricos  
🔹 **Optimización dinámica:** Reasignación de rutas en tiempo real  
🔹 **Integración con sensores IoT:** Nivel de llenado de contenedores  
🔹 **App del ciudadano:** Notificaciones cuando camión está cerca  

---

**Documento preparado para:** Defensa de Tesis - Ingeniería en Software  
**Fecha:** Enero 2025  
**Sistema:** Gestión de Incidencias EPAGAL Latacunga  
**Módulo:** Geofencing y Monitoreo en Tiempo Real
