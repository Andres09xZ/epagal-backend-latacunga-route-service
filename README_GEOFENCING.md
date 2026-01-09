# Sistema de Geofencing - EPAGAL Latacunga

## 📋 Descripción

Sistema completo de geofencing para monitoreo en tiempo real de conductores, implementado con **Behavior-Driven Development (BDD)** usando pytest-bdd.

El sistema detecta y alerta sobre:
- ✅ Desviaciones de ruta (>500m)
- ✅ Velocidad excesiva (>80 km/h)
- ✅ Paradas prolongadas (>15 min)
- ✅ Salidas de zona de cobertura
- ✅ Baja precisión GPS (<50m)
- ✅ Saltos temporales anómalos

## 🏗️ Arquitectura

```
┌─────────────────┐
│  App Móvil      │  ←──── Conductor reporta GPS cada 10s
│  (Conductor)    │
└────────┬────────┘
         │ POST /api/geofencing/tracking/gps
         ↓
┌────────────────────────────────────────────────┐
│  FastAPI Backend                                │
│  ┌──────────────────────────────────────────┐  │
│  │ GeofencingService                        │  │
│  │  • Valida calidad GPS                    │  │
│  │  • Verifica velocidad                    │  │
│  │  • Calcula desviación ruta (Shapely)    │  │
│  │  • Valida zonas (PostGIS)                │  │
│  │  • Detecta paradas prolongadas           │  │
│  │  • Genera alertas con severidad         │  │
│  └──────────────────────────────────────────┘  │
│          │                                      │
│          ├─→ PostgreSQL + PostGIS (alertas)    │
│          └─→ WebSocket Manager (broadcast)     │
└────────────────┬───────────────────────────────┘
                 │ WebSocket /api/geofencing/ws/alertas
                 ↓
        ┌────────────────┐
        │  Dashboard Web │  ←──── Operador ve alertas en tiempo real
        │  (Operador)    │
        └────────────────┘
```

## 🗂️ Estructura de Archivos

```
Backend-latacunga-clean/
├── app/
│   ├── models/
│   │   └── geofencing.py              # Modelos SQLAlchemy (5 tablas)
│   ├── schemas/
│   │   └── geofencing.py              # Esquemas Pydantic (12 schemas)
│   ├── services/
│   │   └── geofencing_service.py      # Lógica de negocio (600+ líneas)
│   └── routers/
│       └── geofencing.py              # Endpoints REST + WebSocket
│
├── features/
│   ├── geofencing.feature             # Especificación BDD (23 escenarios)
│   └── steps/
│       └── test_geofencing.py         # Implementación de steps
│
├── migrations/
│   └── 005_sistema_geofencing.sql     # Schema PostgreSQL + PostGIS
│
└── README_GEOFENCING.md               # Este archivo
```

## 🚀 Instalación y Configuración

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

**Dependencias clave:**
- `shapely>=2.0.0` - Geometría vectorial (Point, LineString, Polygon)
- `geoalchemy2>=0.15.0` - Integración PostGIS + SQLAlchemy
- `geopy>=2.4.0` - Cálculos geodésicos (distancias reales)
- `pytest-bdd>=6.1.0` - Testing BDD con Gherkin
- `websockets>=12.0` - Notificaciones en tiempo real

### 2. Configurar Base de Datos

**🌐 Usando Neon PostgreSQL (Recomendado):**

```bash
# 1. Crear cuenta en https://neon.tech
# 2. Crear proyecto y obtener connection string
# 3. Configurar .env
DATABASE_URL=postgresql://user:pass@ep-xxx.neon.tech/neondb?sslmode=require

# 4. Habilitar PostGIS desde Neon Console
CREATE EXTENSION IF NOT EXISTS postgis CASCADE;
```

Ver guía completa: [`GUIA_NEON_POSTGRESQL.md`](./GUIA_NEON_POSTGRESQL.md)

**🐘 Usando PostgreSQL Local:**

```bash
# Instalar PostgreSQL + PostGIS
sudo apt-get install postgresql postgis

# Conectar
psql -U postgres

# Crear BD
CREATE DATABASE epagal_db;
\c epagal_db
CREATE EXTENSION postgis;
```

### 3. Migrar Base de Datos

**Opción A: Script Python (Recomendado para Neon):**

```bash
python aplicar_migracion_geofencing.py
```

**Opción B: psql Manual:**

```bash
# PostgreSQL Local
psql -U postgres -d epagal_db -f migrations/005_sistema_geofencing.sql

# Neon PostgreSQL
psql "postgresql://user:pass@ep-xxx.neon.tech/neondb?sslmode=require" -f migrations/005_sistema_geofencing.sql
```

Esto crea:
- ✅ 5 tablas: `geofence_config`, `zonas_geograficas`, `historial_posiciones`, `geofence_alerts`, `estadisticas_geofencing`
- ✅ Índices espaciales GIST para consultas rápidas
- ✅ Configuración por defecto (velocidad_maxima_kmh: 80, distancia_desviacion_m: 500, etc.)
- ✅ Zonas geográficas (occidental, oriental, cobertura_epagal)
- ✅ Funciones PostGIS (`punto_en_zona`)
- ✅ Vistas (`alertas_activas_detalle`, `estadisticas_mensuales`)

### 4. Verificar Instalación

```bash
# Iniciar servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# En otro terminal, verificar salud
curl http://localhost:8000/api/geofencing/health
```

Respuesta esperada:
```json
{
  "status": "ok",
  "servicio": "geofencing",
  "alertas_activas": 0,
  "alertas_criticas": 0,
  "conductores_en_ruta": 0,
  "websocket_conexiones": 0,
  "timestamp": "2025-01-09T10:30:00"
}
```

### 5. Consideraciones para Neon PostgreSQL

⚠️ **Autosuspensión**: Neon suspende la BD después de 5 min de inactividad (plan gratuito)
- **Primera consulta** después de suspensión: ~1-2 segundos
- **Solución**: `pool_pre_ping=True` en SQLAlchemy maneja reconexión automática

⚠️ **Connection Pooling**: Configuración recomendada
```python
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # IMPORTANTE para Neon
    pool_recycle=3600
)
```

📖 Ver más en: [`GUIA_NEON_POSTGRESQL.md`](./GUIA_NEON_POSTGRESQL.md)

## 📡 API Endpoints

### Tracking GPS

#### POST `/api/geofencing/tracking/gps`
Procesar posición GPS del conductor.

**Request:**
```json
{
  "conductor_id": 1,
  "latitud": -0.9360,
  "longitud": -78.6216,
  "precision_m": 15.0,
  "velocidad_kmh": 45.0,
  "timestamp": "2025-01-09T10:30:00"
}
```

**Response:**
```json
{
  "valido": true,
  "calidad_gps": "excelente",
  "alertas_generadas": [],
  "distancia_a_ruta_m": 120.5,
  "en_zona_correcta": true,
  "estado_conductor": "en_ruta",
  "recomendaciones": []
}
```

### Alertas

#### GET `/api/geofencing/alertas`
Listar alertas con filtros.

**Query params:**
- `conductor_id` (int) - Filtrar por conductor
- `tipo` (str) - desviacion_ruta, velocidad_excesiva, parada_prolongada...
- `severidad` (str) - low, medium, high, critical
- `estado` (str) - activa, resuelta, ignorada, escalada
- `fecha_desde` (date) - YYYY-MM-DD
- `fecha_hasta` (date) - YYYY-MM-DD
- `limit` (int, default=100)
- `offset` (int, default=0)

#### GET `/api/geofencing/alertas/activas`
Solo alertas activas, ordenadas por severidad.

**Query params:**
- `severidad_minima` (str) - low, medium, high, critical

#### PUT `/api/geofencing/alertas/{alerta_id}/resolver`
Marcar alerta como resuelta.

**Request:**
```json
{
  "estado": "resuelta",
  "notas": "Conductor confirmó que estaba en incidencia",
  "resuelta_por": "operador@epagal.gob.ec"
}
```

### Configuración

#### GET `/api/geofencing/config`
Obtener parámetros de configuración.

**Response:**
```json
[
  {
    "id": 1,
    "parametro": "velocidad_maxima_kmh",
    "valor": 80.0,
    "unidad": "km/h",
    "descripcion": "Velocidad máxima permitida",
    "activo": true
  },
  ...
]
```

#### PUT `/api/geofencing/config/{parametro}`
Actualizar parámetro.

**Request:**
```json
{
  "valor": 90.0,
  "activo": true
}
```

### Estadísticas

#### GET `/api/geofencing/estadisticas/{conductor_id}`
Estadísticas de desempeño del conductor.

**Query params:**
- `fecha_desde` (date)
- `fecha_hasta` (date)

**Response:**
```json
{
  "conductor_id": 1,
  "periodo_inicio": "2025-01-01T00:00:00",
  "periodo_fin": "2025-01-31T23:59:59",
  "total_alertas": 12,
  "alertas_desviacion": 3,
  "alertas_velocidad": 5,
  "alertas_parada": 2,
  "alertas_zona": 1,
  "alertas_gps": 1,
  "distancia_total_km": 450.5,
  "velocidad_promedio_kmh": 42.3,
  "velocidad_maxima_kmh": 75.8,
  "tiempo_conduccion_horas": 18.5,
  "puntuacion_seguridad": 85.2
}
```

#### GET `/api/geofencing/reportes/seguridad-mensual`
Reporte mensual de todos los conductores.

**Query params:**
- `mes` (int, 1-12)
- `anio` (int)

### WebSocket

#### WS `/api/geofencing/ws/alertas`
Conexión WebSocket para alertas en tiempo real.

**Mensaje recibido:**
```json
{
  "id": 123,
  "conductor_id": 1,
  "conductor_nombre": "Juan Pérez",
  "tipo": "velocidad_excesiva",
  "severidad": "high",
  "descripcion": "Velocidad de 95 km/h excede límite de 80 km/h",
  "latitud": -0.9360,
  "longitud": -78.6216,
  "velocidad_kmh": 95.0,
  "timestamp": "2025-01-09T10:30:00"
}
```

## 🧪 Testing BDD

### Ejecutar Tests

```bash
# Todos los tests de geofencing
pytest features/steps/test_geofencing.py -v

# Test específico por nombre
pytest features/steps/test_geofencing.py -k "desviacion" -v

# Con coverage
pytest features/steps/test_geofencing.py --cov=app.services.geofencing_service --cov-report=html
```

### Escenarios Implementados

**Desviación de Ruta (4 escenarios):**
- ✅ Conductor dentro de ruta (200m) → Sin alerta
- ✅ Conductor desviado 600m → Alerta MEDIUM
- ✅ Desviación recurrente → Escalación a HIGH
- ✅ Conductor regresa a ruta → Alerta resuelta

**Velocidad (4 escenarios):**
- ✅ Velocidad 60 km/h (normal) → Sin alerta
- ✅ Velocidad 90 km/h → Alerta HIGH
- ✅ Velocidad 110 km/h → Alerta CRITICAL
- ✅ Velocidad recurrente → Escalación

**Paradas Prolongadas (4 escenarios):**
- ✅ Parada 10 min en incidencia → Sin alerta
- ✅ Parada 20 min fuera de ruta → Alerta MEDIUM
- ✅ Parada >30 min → Alerta HIGH
- ✅ Conductor reanuda movimiento → Alerta resuelta

**Zonas Geográficas (3 escenarios):**
- ✅ Conductor en zona asignada → Sin alerta
- ✅ Conductor en zona incorrecta → Alerta MEDIUM
- ✅ Conductor fuera de cobertura EPAGAL → Alerta HIGH

**Precisión GPS (4 escenarios):**
- ✅ GPS con 15m precisión → Procesado normal
- ✅ GPS con 80m precisión → Alerta LOW
- ✅ GPS con >100m precisión → Rechazado
- ✅ Salto temporal anómalo → Alerta HIGH

## 📊 Configuración por Defecto

| Parámetro | Valor | Unidad | Descripción |
|-----------|-------|--------|-------------|
| `velocidad_maxima_kmh` | 80 | km/h | Velocidad máxima para alerta |
| `velocidad_critica_kmh` | 100 | km/h | Velocidad para alerta crítica |
| `distancia_desviacion_m` | 500 | metros | Distancia máxima de ruta |
| `tiempo_parada_min` | 15 | minutos | Tiempo máximo de parada |
| `precision_minima_gps_m` | 50 | metros | Precisión mínima GPS |
| `ventana_recurrencia_min` | 30 | minutos | Ventana para contar recurrencias |
| `umbral_recurrencia` | 3 | veces | Recurrencias para escalar |
| `velocidad_salto_temporal_kmh` | 150 | km/h | Velocidad para detectar salto |
| `distancia_parada_m` | 50 | metros | Distancia para considerar parada |
| `velocidad_minima_movimiento_kmh` | 5 | km/h | Velocidad mínima movimiento |

## 🔧 Integración con App Móvil

### Ejemplo Cliente GPS (React Native)

```javascript
import { useEffect } from 'react';
import * as Location from 'expo-location';

const GPSTracker = ({ conductorId }) => {
  useEffect(() => {
    const watchId = Location.watchPositionAsync(
      {
        accuracy: Location.Accuracy.High,
        timeInterval: 10000, // 10 segundos
        distanceInterval: 50, // 50 metros
      },
      async (location) => {
        const { latitude, longitude, accuracy, speed } = location.coords;
        
        // Enviar a backend
        await fetch('https://api.epagal.gob.ec/api/geofencing/tracking/gps', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            conductor_id: conductorId,
            latitud: latitude,
            longitud: longitude,
            precision_m: accuracy,
            velocidad_kmh: speed ? speed * 3.6 : null,
            timestamp: new Date().toISOString(),
          }),
        });
      }
    );
    
    return () => watchId.then(w => w.remove());
  }, [conductorId]);
  
  return null;
};
```

### Ejemplo Cliente WebSocket (Dashboard)

```javascript
// dashboard/app.js
const ws = new WebSocket('ws://localhost:8000/api/geofencing/ws/alertas');

ws.onopen = () => {
  console.log('Conectado al sistema de alertas');
  // Enviar ping cada 30s para mantener conexión
  setInterval(() => ws.send('ping'), 30000);
};

ws.onmessage = (event) => {
  const alerta = JSON.parse(event.data);
  
  if (alerta === 'pong') return;
  
  // Mostrar alerta en UI
  mostrarAlerta({
    conductor: alerta.conductor_nombre,
    tipo: alerta.tipo,
    severidad: alerta.severidad,
    descripcion: alerta.descripcion,
    ubicacion: [alerta.latitud, alerta.longitud],
  });
  
  // Reproducir sonido si es crítica
  if (alerta.severidad === 'critical') {
    new Audio('/alert-critical.mp3').play();
  }
};

function mostrarAlerta(alerta) {
  // Agregar marcador en mapa
  L.marker([alerta.ubicacion[0], alerta.ubicacion[1]], {
    icon: iconoSegunSeveridad(alerta.severidad)
  }).addTo(map).bindPopup(`
    <strong>${alerta.conductor}</strong><br>
    ${alerta.tipo}<br>
    ${alerta.descripcion}
  `).openPopup();
  
  // Notificación browser
  new Notification(`Alerta ${alerta.severidad}: ${alerta.conductor}`, {
    body: alerta.descripcion,
    icon: '/alert-icon.png',
  });
}
```

## 📈 Monitoreo y Métricas

### Consultas SQL Útiles

```sql
-- Alertas activas ahora
SELECT * FROM alertas_activas_detalle 
ORDER BY severidad DESC, minutos_desde_alerta DESC;

-- Top 5 conductores con más alertas este mes
SELECT conductor_nombre, SUM(total_alertas) as total
FROM estadisticas_mensuales
WHERE mes = DATE_TRUNC('month', CURRENT_DATE)
GROUP BY conductor_nombre
ORDER BY total DESC LIMIT 5;

-- Distribución de alertas por tipo (últimos 7 días)
SELECT tipo, COUNT(*) as cantidad
FROM geofence_alerts
WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY tipo
ORDER BY cantidad DESC;

-- Conductores con mejor puntuación de seguridad
SELECT conductor_nombre, AVG(puntuacion_seguridad) as puntuacion_promedio
FROM estadisticas_mensuales
GROUP BY conductor_nombre
ORDER BY puntuacion_promedio DESC;
```

## 🐛 Debugging

### Logs del Servicio

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# En geofencing_service.py ya hay logs
# Para habilitar, configurar nivel DEBUG
```

### Verificar PostGIS

```sql
-- Verificar extensión PostGIS
SELECT PostGIS_Version();

-- Verificar zonas cargadas
SELECT nombre, ST_AsText(geometria) FROM zonas_geograficas;

-- Test de punto en zona
SELECT punto_en_zona(-0.9360, -78.6216, 'zona_occidental');
```

## 📚 Referencias

- **Shapely**: https://shapely.readthedocs.io/
- **PostGIS**: https://postgis.net/documentation/
- **GeoPy**: https://geopy.readthedocs.io/
- **pytest-bdd**: https://pytest-bdd.readthedocs.io/
- **FastAPI WebSockets**: https://fastapi.tiangolo.com/advanced/websockets/

## 🤝 Contribuir

Para agregar nuevos tipos de alertas:

1. Actualizar enum `TipoAlerta` en `models/geofencing.py`
2. Agregar método `_verificar_nueva_condicion()` en `GeofencingService`
3. Llamar método desde `procesar_posicion_gps()`
4. Agregar escenarios BDD en `features/geofencing.feature`
5. Implementar steps en `features/steps/test_geofencing.py`
6. Ejecutar tests: `pytest -v`

## 📝 Licencia

Sistema desarrollado para EPAGAL Latacunga - Tesis Ingeniería en Software 2025

---

**Autor:** Octavo Semestre - Ingeniería en Software  
**Fecha:** Enero 2025  
**Versión:** 1.0.0
