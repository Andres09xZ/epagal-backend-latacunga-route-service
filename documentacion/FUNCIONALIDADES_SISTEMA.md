# 📋 Funcionalidades del Sistema de Gestión de Rutas de Recolección

## 🎯 Descripción General

Sistema integral de gestión de rutas de recolección de residuos que genera automáticamente rutas optimizadas cuando se supera un umbral de puntos establecido. El sistema detecta y clasifica incidencias, calcula rutas óptimas utilizando OSRM, y proporciona navegación en tiempo real para conductores.

---

## 🔑 Funcionalidades Principales

### 1. **Gestión de Incidencias** 🚨

#### Crear Incidencia
- **Endpoint:** `POST /api/incidencias/`
- **Descripción:** Registra una nueva incidencia en el sistema
- **Parámetros:**
  - `tipo`: Tipo de incidencia (animal_muerto, zona_critica, acopio)
  - `descripcion`: Descripción detallada de la incidencia
  - `lat`: Latitud de ubicación
  - `lon`: Longitud de ubicación
  - `usuario_id`: ID del usuario que reporta
  - `foto_url` (opcional): URL de foto de la incidencia

#### Tipos de Incidencias y Puntos
| Tipo | Puntos | Descripción |
|------|--------|-------------|
| `animal_muerto` | 5 | Animal muerto en vía pública |
| `zona_critica` | 3 | Acumulación de basura o zona con problemas |
| `acopio` | 1 | Punto de recolección adicional |

#### Estados de Incidencia
- **reportada**: Incidencia acaba de ser reportada
- **validada**: Incidencia fue validada y asignada a ruta
- **completada**: Incidencia fue atendida por el conductor
- **cancelada**: Incidencia fue cancelada

---

### 2. **Sistema de Validación y Generación de Rutas** ✅

#### Validar Incidencia
- **Endpoint:** `POST /api/incidencias/{id}/validate`
- **Descripción:** Valida una incidencia y la suma al contador de puntos de su zona
- **Comportamiento:**
  - Suma los puntos al total de la zona (oriental u occidental)
  - Si total de puntos **> 20**: Genera automáticamente una nueva ruta
  - Detección de anti-solapamiento: Si existe ruta cercana (<500m), NO genera nueva ruta

#### Lógica de Generación Automática de Rutas
```
┌─────────────────────────────────────────────┐
│ Incidencia Validada                         │
└────────────────┬────────────────────────────┘
                 │
                 ▼
    ┌────────────────────────────┐
    │ ¿Total puntos zona > 20?   │
    └────────┬───────────────────┘
             │
         Sí  │  No
             │  ↓ (fin, esperar más incidencias)
             ▼
    ┌────────────────────────────┐
    │ ¿Existe ruta cercana?      │
    │ (< 500m Haversine)         │
    └────────┬───────────────────┘
             │
      No     │  Sí
             │  ↓ (No genera, suma a ruta existente)
             ▼
    ┌────────────────────────────┐
    │ Generar Nueva Ruta         │
    │ - Usar OSRM                │
    │ - Optimizar orden puntos   │
    │ - Calcular polyline        │
    │ - Asignar camiones         │
    └────────────────────────────┘
```

---

### 3. **Generación y Optimización de Rutas** 🗺️

#### Generar Ruta
- **Proceso Automático:** Se dispara cuando se valida la incidencia que supera el umbral
- **Algoritmo:**
  1. Recopila todas las incidencias validadas sin asignar en la zona
  2. Obtiene coordenadas de depósito y botadero
  3. Ordena puntos de forma óptima utilizando OSRM
  4. Calcula distancia total y tiempo estimado
  5. Asigna camiones según capacidad y tipo de residuo

#### Información de Ruta Generada
```json
{
  "id": 1,
  "zona": "oriental",
  "estado": "asignada",
  "suma_gravedad": 22,
  "camiones_usados": 1,
  "duracion_estimada": "00:25:00",
  "costo_total_metros": 15200,
  "fecha_generacion": "2026-01-15T10:30:00",
  "polyline": "r~qkAx~{mH~@F...",
  "puntos": [
    {
      "orden": 1,
      "tipo_punto": "deposito",
      "lat": -0.936,
      "lon": -78.613
    },
    {
      "orden": 2,
      "tipo_punto": "incidencia",
      "lat": -0.925,
      "lon": -78.610,
      "incidencia_id": 1,
      "tipo_incidencia": "animal_muerto"
    }
  ]
}
```

#### Zonas Geográficas
- **Oriental:** longitud < -78.6191
- **Occidental:** longitud ≥ -78.6191

---

### 4. **Anti-Solapamiento de Rutas** 🚫

#### Detección de Proximidad
- **Radio de Detección:** 500 metros (Haversine distance)
- **Comportamiento:**
  - Si una incidencia validada está a menos de 500m de una ruta existente, NO genera nueva ruta
  - La incidencia se suma a la ruta más cercana existente
  - Evita crear múltiples rutas innecesarias en la misma área

#### Fórmula de Haversine
```
d = 2 * R * arcsin(sqrt(sin²((lat2-lat1)/2) + cos(lat1) * cos(lat2) * sin²((lon2-lon1)/2)))

Donde:
- R = 6371 km (radio de la Tierra)
- d = distancia en km
- Si d < 0.5 km → Considerada cercana
```

---

### 5. **Consulta de Rutas** 📍

#### Obtener Rutas por Zona
- **Endpoint:** `GET /api/rutas/zona/{zona}`
- **Parámetros:** `zona` (oriental o occidental)
- **Retorna:** Lista de todas las rutas de esa zona

#### Obtener Detalles Completos de Ruta
- **Endpoint:** `GET /api/rutas/{id}`
- **Retorna:** 
  - Información completa de la ruta
  - **Polyline:** String codificado con la forma de la ruta (Google Polyline Format)
  - Lista de puntos en orden
  - Información de incidencias

#### Obtener Información Extendida de Ruta
- **Endpoint:** `GET /api/rutas/{id}/detalles`
- **Retorna:** Detalles adicionales de la ruta

#### Obtener Información de Navegación
- **Endpoint:** `GET /api/rutas/{id}/navegacion`
- **Retorna:**
  - Siguiente punto a visitar
  - Progreso de la ruta (% completado)
  - Lista de puntos con estado de completación
  - Información del conductor asignado

---

### 6. **Gestión de Conductores** 👨‍✈️

#### Registro de Conductor
- **Endpoint:** `POST /api/conductores/`
- **Información:**
  - Nombre completo
  - Teléfono
  - Cedula
  - Placa del vehículo
  - Tipo de vehículo

#### Obtener Perfil de Conductor
- **Endpoint:** `GET /api/conductores/{id}`
- **Retorna:** Información completa del conductor

#### Listar Conductores
- **Endpoint:** `GET /api/conductores/`
- **Retorna:** Lista de todos los conductores registrados

#### Estados de Conductor
- **activo**: Conductor disponible para recibir rutas
- **inactivo**: Conductor no disponible
- **en_ruta**: Conductor actualmente ejecutando una ruta

---

### 7. **Asignación de Rutas** 📌

#### Asignar Ruta a Conductor
- **Endpoint:** `POST /api/rutas/{ruta_id}/asignar`
- **Parámetros:**
  - `conductor_id`: ID del conductor
  - `camion_id`: ID del camión
- **Cambios:**
  - Ruta cambia a estado "asignada"
  - Conductor recibe la información de la ruta
  - Se crea registro de asignación

#### Estados de Asignación
- **asignado**: Ruta asignada pero no iniciada
- **iniciado**: Conductor comenzó a ejecutar la ruta
- **completado**: Ruta completada exitosamente
- **cancelado**: Asignación cancelada

---

### 8. **Ejecución de Rutas en Tiempo Real** ⏱️

#### Iniciar Ruta
- **Endpoint:** `POST /api/rutas/{ruta_id}/iniciar`
- **Cambios:**
  - Ruta cambia a estado "en_ejecucion"
  - Se registra hora de inicio
  - Conductor comienza navegación

#### Completar Incidencia
- **Endpoint:** `POST /api/rutas/{ruta_id}/incidencia/{incidencia_id}/completar`
- **Cambios:**
  - Incidencia cambia a estado "completada"
  - Se registra hora de completación
  - Se actualiza progreso de la ruta

#### Completar Ruta
- **Endpoint:** `POST /api/rutas/{ruta_id}/completar`
- **Cambios:**
  - Ruta cambia a estado "completada"
  - Se registra hora de finalización
  - Se libera conductor para nueva ruta
  - Se calcula resumen final

#### Información de Navegación en Tiempo Real
```json
{
  "ruta_id": 1,
  "zona": "oriental",
  "conductor": {
    "id": 1,
    "nombre": "Juan Pérez",
    "telefono": "0987654321"
  },
  "navegacion": {
    "punto_actual": {
      "orden": 3,
      "tipo_punto": "incidencia",
      "lat": -0.935,
      "lon": -78.612,
      "descripcion": "Basura acumulada",
      "llegada_estimada": "2026-01-15T10:45:00"
    },
    "punto_actual_index": 2,
    "total_puntos": 8,
    "puntos_completados": 2,
    "progreso_porcentaje": 25.0
  },
  "resumen": {
    "distancia_total_km": 15.2,
    "duracion_estimada": "00:25:00",
    "incidencias_totales": 6,
    "incidencias_completadas": 2
  }
}
```

---

### 9. **Gestión de Camiones** 🚛

#### Tipos de Camiones Disponibles
| Tipo | Capacidad | Descripción |
|------|-----------|-------------|
| compactador | 8000 kg | Para residuos compactables |
| volteo | 6000 kg | Para residuos voluminosos |
| plataforma | 5000 kg | Para carga general |

#### Asignar Camión a Ruta
- Asignación automática según tipo de residuos
- Optimización de capacidad
- Registro de uso de camión

---

### 10. **Cálculo de Rutas con OSRM** 🗺️

#### Servicio OSRM (Open Source Routing Machine)
- **Puerto:** 5000 (Docker)
- **Funcionalidades:**
  - Cálculo de distancias optimizadas
  - Orden óptimo de puntos (TSP - Traveling Salesman Problem)
  - Generación de geometría/polyline
  - Cálculo de tiempos estimados

#### Formato de Polyline (Google Polyline Format)
```
Ejemplo: r~qkAx~{mH~@F...

Características:
- String alfanumérico codificado
- Representa secuencia de coordenadas (lat, lon)
- Muy comprimido (reduce tamaño 20x vs JSON)
- Formato estándar para aplicaciones móviles
```

#### Decodificación en App Móvil
```javascript
// JavaScript/React Native
import polyline from '@mapbox/polyline';

const coords = polyline.decode('r~qkAx~{mH~@F...');
// Retorna: [[lat1, lon1], [lat2, lon2], ...]
```

---

### 11. **Infraestructura Fija** 🏢

#### Puntos Fijos del Sistema
- **Depósito (Inicio):**
  - Coordenadas: -0.936, -78.613
  - Zona: Oriental
  - Punto de partida de todas las rutas
  
- **Botadero (Final):**
  - Coordenadas: -0.949, -78.663
  - Zona: Occidental
  - Punto final de todas las rutas

#### Importancia
- Todas las rutas inician en depósito y terminan en botadero
- Se incluyen automáticamente en los cálculos de distancia
- Son puntos obligatorios en cada ruta

---

### 12. **Sistema de Notificaciones** 📢

#### Notificaciones Generadas
1. **Ruta Generada:** Se notifica cuando se crea automáticamente
2. **Ruta Asignada:** Se notifica al conductor sobre su ruta
3. **Incidencia Completada:** Se registra en tiempo real
4. **Ruta Completada:** Se notifica finalización
5. **Alerta Anti-Solapamiento:** Se notifica si se evitó crear ruta duplicada

#### Canales de Notificación
- Webhooks (para sistemas externos)
- Mensajes en tiempo real (WebSocket)
- Email (opcional)

---

### 13. **Reportes y Estadísticas** 📊

#### Información Disponible
- Total de rutas generadas por zona
- Total de incidencias completadas
- Distancia recorrida por zona
- Tiempo promedio de ruta
- Eficiencia de rutas (puntos/km)
- Desempeño de conductores
- Utilización de camiones

#### Métricas por Ruta
```json
{
  "ruta_id": 1,
  "eficiencia": {
    "puntos_por_km": 1.45,
    "tiempo_promedio_por_punto": 2.5,
    "distancia_optimizada": true
  },
  "desempeño": {
    "tiempo_ejecucion": "00:23:15",
    "tiempo_estimado": "00:25:00",
    "diferencia": -1.75
  }
}
```

---

### 14. **Autenticación y Seguridad** 🔐

#### Autenticación
- **Tipo:** JWT (JSON Web Tokens)
- **Duración:** Token expira según configuración
- **Roles:** 
  - `admin`: Acceso total al sistema
  - `conductor`: Acceso a rutas asignadas
  - `usuario`: Puede reportar incidencias

#### Endpoints Protegidos
- Todos los endpoints de rutas requieren autenticación
- Los conductores solo ven sus rutas
- Los usuarios solo pueden reportar (sin autenticación requerida)

#### Seguridad
- HTTPS en producción
- CORS configurado
- Rate limiting en desarrollo
- Validación de entrada en todos los endpoints

---

### 15. **Integraciones Externas** 🔗

#### Google Maps (Opcional)
- Visualización de rutas en mapa web
- Decodificación de polylines

#### React Native Maps
- Visualización en app móvil
- Tracking en tiempo real
- Mostrar polyline de ruta optimizada

#### OSRM (Obligatorio)
- Cálculo de rutas optimizadas
- Geometría y distancias
- Motor de routing principal

---

## 📱 **API Endpoints Principales**

### Incidencias
```
POST   /api/incidencias/                    # Crear incidencia
GET    /api/incidencias/                    # Listar incidencias
GET    /api/incidencias/{id}                # Obtener detalle
POST   /api/incidencias/{id}/validate       # Validar incidencia
PUT    /api/incidencias/{id}                # Actualizar incidencia
```

### Rutas
```
GET    /api/rutas/                          # Listar todas las rutas
GET    /api/rutas/{id}                      # Obtener ruta con polyline
GET    /api/rutas/{id}/detalles             # Detalles extendidos
GET    /api/rutas/{id}/navegacion           # Navegación en tiempo real
GET    /api/rutas/zona/{zona}               # Rutas por zona
POST   /api/rutas/{id}/iniciar              # Iniciar ejecución
POST   /api/rutas/{id}/completar            # Marcar como completada
POST   /api/rutas/{id}/asignar              # Asignar a conductor
POST   /api/rutas/{id}/incidencia/{inc_id}/completar  # Marcar incidencia completa
```

### Conductores
```
POST   /api/conductores/                    # Registrar conductor
GET    /api/conductores/                    # Listar conductores
GET    /api/conductores/{id}                # Obtener detalle
PUT    /api/conductores/{id}                # Actualizar perfil
```

### Sistema
```
GET    /api/health                          # Verificar salud del sistema
GET    /docs                                # Documentación Swagger
```

---

## 🔄 **Flujo Completo de Funcionamiento**

```
1. REPORTE DE INCIDENCIA
   ↓
   Usuario reporta incidencia (lat, lon, tipo)
   ↓
   Sistema crea registro con estado "reportada"

2. VALIDACIÓN
   ↓
   Usuario/Admin valida incidencia
   ↓
   Sistema suma puntos a la zona
   ↓
   ¿Puntos > 20? NO → Esperar más incidencias
                    ↓
                    FIN (por ahora)

3. GENERACIÓN (Solo si Puntos > 20)
   ↓
   Sistema recopila incidencias sin asignar
   ↓
   ¿Existe ruta cercana? SÍ → Agregar a ruta existente → FIN
                         NO → Continuar
   ↓
   Sistema llama a OSRM para optimizar orden
   ↓
   Sistema calcula polyline y distancia
   ↓
   Sistema crea Ruta con estado "generada"

4. ASIGNACIÓN
   ↓
   Admin asigna ruta a conductor y camión
   ↓
   Sistema notifica conductor
   ↓
   Ruta cambia a estado "asignada"

5. EJECUCIÓN
   ↓
   Conductor inicia ruta en app móvil
   ↓
   Ruta cambia a "en_ejecucion"
   ↓
   Conductor navega a cada punto
   ↓
   Al llegar, completa cada incidencia
   ↓
   Progreso se actualiza en tiempo real

6. FINALIZACIÓN
   ↓
   Conductor completa todas las incidencias
   ↓
   Conductor llega a botadero
   ↓
   Conductor marca ruta como completada
   ↓
   Sistema registra tiempo final y estadísticas
   ↓
   Ruta cambia a estado "completada"
   ↓
   Conductor liberado para nueva ruta
```

---

## 🎯 **Casos de Uso Principales**

### Caso 1: Generación Automática de Ruta
```
Evento: 6ta incidencia validada = 22 puntos total
Resultado: 
- ✅ Nueva ruta generada automáticamente
- ✅ Polyline calculado
- ✅ Camión asignado automáticamente
- ✅ Notificación enviada
```

### Caso 2: Anti-Solapamiento Efectivo
```
Evento: Incidencia validada a 300m de ruta existente
Resultado:
- ✅ NO genera nueva ruta
- ✅ Se suma a ruta existente
- ✅ Previene fragmentación de rutas
```

### Caso 3: Navegación en Tiempo Real
```
Evento: Conductor con ruta asignada abre app móvil
Datos Mostrados:
- ✅ Mapa con polyline de la ruta completa
- ✅ Siguiente punto a visitar
- ✅ Progreso de la ruta (% completado)
- ✅ Tiempo estimado restante
```

### Caso 4: Completación de Ruta
```
Evento: Conductor completa todas las incidencias
Resultado:
- ✅ Incidencias marcadas como "completadas"
- ✅ Ruta genera reporte final
- ✅ Estadísticas registradas
- ✅ Conductor disponible para nueva ruta
```

---

## 🚀 **Características Avanzadas**

### Optimización Inteligente
- Uso de OSRM para TSP (Problema del Vendedor Viajero)
- Minimización de distancia total
- Consideración de restricciones de tiempo
- Optimización de carga de camiones

### Detección Geográfica Automática
- Asignación automática a zona (Oriental/Occidental)
- Cálculo automático de distancia a depósito/botadero
- Verificación automática de proximidad a rutas

### Escalabilidad
- Soporta múltiples zonas simultáneamente
- Múltiples conductores y camiones
- Múltiples rutas en paralelo
- Base de datos PostgreSQL con PostGIS

### Confiabilidad
- Logging completo de todas las operaciones
- Manejo de errores robusto
- Transacciones de base de datos
- Recuperación ante fallos

---

## 📈 **Métricas de Desempeño**

### Tiempos Típicos
- Generación de ruta: < 2 segundos
- Cálculo de polyline: < 1 segundo
- Detección de anti-solapamiento: < 500ms
- Consulta de navegación: < 200ms

### Precisión
- Distancias OSRM: ±5% de distancia real
- Tiempos estimados: ±10% del tiempo real
- Polyline: Exacto con margen de error cartográfico

---

## 🔧 **Configuración del Sistema**

### Parámetros Ajustables
```python
# Umbral de generación de rutas
THRESHOLD_PUNTOS = 20  # Debe ser > 20

# Radio de anti-solapamiento
RADIO_ANTI_SOLAPAMIENTO = 0.5  # km

# Divisor geográfico de zonas
DIVISOR_ZONA = -78.6191  # longitud

# Capacidades de camiones
CAMION_COMPACTADOR = 8000  # kg
CAMION_VOLTEO = 6000      # kg
CAMION_PLATAFORMA = 5000  # kg
```

### Servicios Requeridos
- FastAPI (Backend)
- PostgreSQL (Base de datos)
- PostGIS (Extensión geoespacial)
- OSRM (Motor de routing)
- Redis (Cache opcional)

---

## 🎓 **Ejemplos de Uso**

### Ejemplo 1: Crear y Validar Incidencias
```bash
# Crear 5 incidencias
curl -X POST "http://localhost:8000/api/incidencias/" \
  -H "Content-Type: application/json" \
  -d '{"tipo":"animal_muerto","descripcion":"Animal muerto","lat":-0.925,"lon":-78.610,"usuario_id":1}'

# Validar las primeras 5 (total = 5+3+1+5+3 = 17 puntos)
curl -X POST "http://localhost:8000/api/incidencias/1/validate"

# Crear 6ta incidencia
curl -X POST "http://localhost:8000/api/incidencias/" \
  -H "Content-Type: application/json" \
  -d '{"tipo":"animal_muerto","descripcion":"Otro animal","lat":-0.930,"lon":-78.615,"usuario_id":1}'

# Validar 6ta (total = 22 puntos) → ¡GENERA RUTA AUTOMÁTICAMENTE!
curl -X POST "http://localhost:8000/api/incidencias/6/validate"
```

### Ejemplo 2: Obtener Ruta con Polyline
```bash
curl -X GET "http://localhost:8000/api/rutas/1" \
  -H "Authorization: Bearer TOKEN"
```

### Ejemplo 3: Iniciar Navegación
```bash
# Asignar ruta a conductor
curl -X POST "http://localhost:8000/api/rutas/1/asignar" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"conductor_id":1,"camion_id":1}'

# Iniciar ruta
curl -X POST "http://localhost:8000/api/rutas/1/iniciar" \
  -H "Authorization: Bearer TOKEN"

# Obtener navegación en tiempo real
curl -X GET "http://localhost:8000/api/rutas/1/navegacion" \
  -H "Authorization: Bearer TOKEN"
```

---

## 📞 **Soporte y Contacto**

**Sistema desarrollado para:** EPAGAL (Empresa Pública de Aseo de Latacunga)

**Tecnologías utilizadas:**
- Backend: FastAPI (Python 3.13)
- Base de datos: PostgreSQL + PostGIS
- Routing: OSRM (Docker)
- App Móvil: React Native + Expo
- Autenticación: JWT

**Documentación interactiva:** `http://localhost:8000/docs` (Swagger UI)

---

**Última actualización:** Enero 16, 2026
**Versión:** 1.0.0
