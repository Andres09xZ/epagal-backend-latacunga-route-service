# 🔄 Flujo de Trabajo del Sistema - EPAGAL Latacunga

## 📋 Tabla de Contenidos

1. [Arquitectura General](#arquitectura-general)
2. [Flujo de Autenticación](#flujo-de-autenticación)
3. [Flujo de Gestión de Rutas](#flujo-de-gestión-de-rutas)
4. [Flujo de Incidencias](#flujo-de-incidencias)
5. [Flujo de Conductores](#flujo-de-conductores)
6. [Integración OSRM](#integración-osrm)
7. [Optimización y Rendimiento](#optimización-y-rendimiento)

---

## 🏗️ Arquitectura General

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CAPA DE PRESENTACIÓN                        │
├─────────────────────────────────────────────────────────────────────┤
│  📱 App Móvil (Ionic/Capacitor)  │  🌐 Frontend Web (React/Vue)    │
│  - Conductores                    │  - Administradores              │
│  - Reporte de incidencias         │  - Dashboard                    │
│  - Visualización de rutas         │  - Gestión completa             │
└────────────────┬────────────────────────────────┬───────────────────┘
                 │                                │
                 ▼                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          CAPA DE API (FastAPI)                      │
├─────────────────────────────────────────────────────────────────────┤
│  🔐 Auth Router        │  🚛 Conductores Router                     │
│  - Login/JWT           │  - Gestión de conductores                  │
│  - Validación tokens   │  - Asignación de rutas                     │
├────────────────────────┼────────────────────────────────────────────┤
│  📍 Incidencias Router │  🗺️ Rutas Router                          │
│  - CRUD incidencias    │  - Optimización con OSRM                   │
│  - Estadísticas        │  - Generación de polylines                 │
│  - Geolocalización     │  - Puntos de interés                       │
└────────────────┬───────────────────────────────┬───────────────────┘
                 │                               │
                 ▼                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       CAPA DE SERVICIOS                             │
├─────────────────────────────────────────────────────────────────────┤
│  🔧 Auth Service       │  🚗 Conductor Service                      │
│  🔧 Incidencia Service │  🔧 Ruta Service                          │
│  🔧 Notificación Service (RabbitMQ - Futuro)                       │
└────────────────┬────────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    SERVICIOS EXTERNOS & BASE DE DATOS               │
├─────────────────────────────────────────────────────────────────────┤
│  🗄️ PostgreSQL (Neon)  │  🗺️ OSRM (Ecuador Maps)                  │
│  - PostGIS enabled     │  - Routing optimization                    │
│  - SSL required        │  - Polyline generation                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔐 Flujo de Autenticación

### 1. Login del Usuario

```mermaid
sequenceDiagram
    participant App as 📱 App Móvil/Web
    participant API as 🔐 Auth Router
    participant Service as Auth Service
    participant DB as 🗄️ PostgreSQL
    
    App->>API: POST /api/auth/login
    Note over App,API: {nombre_usuario, password}
    
    API->>Service: validate_credentials()
    Service->>DB: SELECT * FROM usuarios WHERE nombre_usuario = ?
    DB-->>Service: Usuario encontrado
    
    Service->>Service: verify_password(hash, password)
    Note over Service: bcrypt validation
    
    Service->>Service: create_access_token()
    Note over Service: JWT con exp: 30 días
    
    Service-->>API: {access_token, token_type, user_info}
    API-->>App: 200 OK + Token JWT
    
    App->>App: Guardar token en storage local
```

**Código Clave:**
```python
# app/services/auth_service.py
def authenticate_user(db: Session, nombre_usuario: str, password: str):
    user = db.query(Usuario).filter(Usuario.nombre_usuario == nombre_usuario).first()
    if not user or not verify_password(password, user.password):
        return None
    return user

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

### 2. Validación de Requests Protegidos

```mermaid
sequenceDiagram
    participant App as 📱 App
    participant API as 🔒 Protected Endpoint
    participant Dep as get_current_user()
    participant DB as 🗄️ Database
    
    App->>API: GET /api/conductores/mis-rutas
    Note over App,API: Header: Authorization: Bearer {token}
    
    API->>Dep: Dependency injection
    Dep->>Dep: Decode JWT token
    
    alt Token válido
        Dep->>DB: SELECT usuario WHERE id = token.sub
        DB-->>Dep: Usuario encontrado
        Dep-->>API: current_user
        API->>API: Process request
        API-->>App: 200 OK + Data
    else Token inválido/expirado
        Dep-->>API: HTTPException 401
        API-->>App: 401 Unauthorized
    end
```

---

## 🗺️ Flujo de Gestión de Rutas

### 1. Creación de Ruta Optimizada

```mermaid
sequenceDiagram
    participant Admin as 👨‍💼 Administrador
    participant API as 🗺️ Rutas Router
    participant Service as Ruta Service
    participant OSRM as 🌍 OSRM Service
    participant DB as 🗄️ PostgreSQL
    
    Admin->>API: POST /api/rutas
    Note over Admin,API: {nombre, conductor_id, puntos[]}
    
    API->>Service: create_ruta()
    Service->>DB: INSERT INTO rutas
    DB-->>Service: ruta_id
    
    loop Para cada punto
        Service->>DB: INSERT INTO puntos_ruta
        Note over Service,DB: {coordenadas, orden, incidencia_id}
    end
    
    Service->>OSRM: Calcular ruta óptima
    Note over Service,OSRM: POST /route/v1/driving/{coords}
    
    OSRM-->>Service: {distance, duration, geometry}
    
    Service->>Service: Decodificar polyline
    Service->>DB: UPDATE ruta SET polyline, distance, duration
    
    Service-->>API: Ruta creada con optimización
    API-->>Admin: 201 Created + Ruta completa
```

**Código Clave:**
```python
# app/services/ruta_service.py
async def optimize_route(puntos: List[dict]) -> dict:
    # Ordenar puntos desde depósito → incidencias → botadero
    coords = ";".join([f"{p['longitud']},{p['latitud']}" for p in puntos])
    
    osrm_response = await osrm_client.get(
        f"/route/v1/driving/{coords}",
        params={"overview": "full", "geometries": "polyline"}
    )
    
    route = osrm_response["routes"][0]
    return {
        "polyline": route["geometry"],
        "distance": route["distance"],  # metros
        "duration": route["duration"]   # segundos
    }
```

### 2. Obtención de Ruta con Polyline

```mermaid
sequenceDiagram
    participant App as 📱 Conductor App
    participant API as 🗺️ GET /rutas/{id}
    participant Service as Ruta Service
    participant OSRM as 🌍 OSRM Service
    participant DB as 🗄️ Database
    
    App->>API: GET /api/rutas/123
    API->>Service: get_ruta_by_id(123)
    
    Service->>DB: SELECT ruta + puntos + incidencias
    DB-->>Service: Ruta con todos los datos
    
    alt Polyline no existe
        Service->>Service: Extraer coordenadas de puntos
        Service->>OSRM: POST /route/v1/driving/{coords}
        OSRM-->>Service: Polyline geometry
        Service->>DB: UPDATE ruta.polyline
    end
    
    Service->>Service: Formatear respuesta
    Note over Service: Incluir incidencia details en puntos
    
    Service-->>API: Ruta completa con polyline
    API-->>App: 200 OK
    
    App->>App: Renderizar mapa con polyline
    Note over App: Google Maps / Leaflet
```

### 3. Estructura de Datos de Ruta

```json
{
  "id": 1,
  "nombre": "Ruta Centro - Zona Norte",
  "conductor_id": 5,
  "conductor": {
    "id": 5,
    "nombre": "Juan Pérez",
    "telefono": "0987654321",
    "placa_vehiculo": "ABC-1234"
  },
  "fecha": "2024-12-15T08:00:00",
  "estado": "en_progreso",
  "distancia_total": 15.2,
  "tiempo_estimado": 3600,
  "polyline": "encoded_polyline_string_here",
  "puntos": [
    {
      "id": 1,
      "nombre": "Depósito EPAGAL",
      "latitud": -0.936,
      "longitud": -78.613,
      "orden": 1,
      "tipo": "deposito",
      "incidencia": null
    },
    {
      "id": 2,
      "nombre": "Incidencia - Calle García Moreno",
      "latitud": -0.925,
      "longitud": -78.615,
      "orden": 2,
      "tipo": "incidencia",
      "incidencia": {
        "id": 45,
        "tipo": "basura_acumulada",
        "descripcion": "Acumulación de residuos",
        "foto_url": "https://...",
        "estado": "pendiente"
      }
    },
    {
      "id": 3,
      "nombre": "Botadero Inchapo",
      "latitud": -0.949,
      "longitud": -78.663,
      "orden": 3,
      "tipo": "botadero",
      "incidencia": null
    }
  ]
}
```

---

## 📍 Flujo de Incidencias

### 1. Reporte Ciudadano de Incidencia

```mermaid
sequenceDiagram
    participant Citizen as 👤 Ciudadano
    participant App as 📱 App Móvil
    participant API as 📍 Incidencias Router
    participant Service as Incidencia Service
    participant DB as 🗄️ PostgreSQL
    participant Notify as 🔔 Notification Service
    
    Citizen->>App: Tomar foto del problema
    App->>App: Obtener geolocalización
    Note over App: GPS coordinates
    
    App->>API: POST /api/incidencias
    Note over App,API: {tipo, descripcion, foto, lat, lon}
    
    API->>Service: create_incidencia()
    Service->>Service: Validar coordenadas
    Note over Service: PostGIS: ST_Point(lon, lat)
    
    Service->>DB: INSERT INTO incidencias
    Note over Service,DB: Geometry + Metadata
    
    DB-->>Service: incidencia_id
    
    Service->>Notify: Notificar administradores
    Note over Service,Notify: RabbitMQ message (futuro)
    
    Service-->>API: Incidencia creada
    API-->>App: 201 Created
    App-->>Citizen: "Reporte enviado exitosamente"
```

### 2. Gestión Administrativa

```mermaid
sequenceDiagram
    participant Admin as 👨‍💼 Admin Dashboard
    participant API as 📍 Incidencias API
    participant Service as Incidencia Service
    participant DB as 🗄️ Database
    
    Admin->>API: GET /api/incidencias?estado=pendiente
    API->>Service: get_incidencias(filters)
    Service->>DB: SELECT con filtros + ORDER BY fecha
    DB-->>Service: Lista de incidencias
    Service-->>API: Incidencias paginadas
    API-->>Admin: 200 OK + Data
    
    Admin->>Admin: Revisar incidencia #45
    Admin->>API: PATCH /api/incidencias/45
    Note over Admin,API: {estado: "en_revision"}
    
    API->>Service: update_incidencia(45, data)
    Service->>DB: UPDATE incidencias SET estado = ...
    DB-->>Service: Updated
    Service-->>API: Incidencia actualizada
    API-->>Admin: 200 OK
    
    Admin->>Admin: Asignar a ruta
    Admin->>API: POST /api/rutas
    Note over Admin,API: Incluir incidencia_id en puntos
```

### 3. Estados de Incidencia

```python
# Estados del ciclo de vida
estados = [
    "pendiente",      # Recién reportada
    "en_revision",    # Administrador revisando
    "asignada",       # Incluida en una ruta
    "en_proceso",     # Conductor llegó al lugar
    "resuelta",       # Problema solucionado
    "rechazada"       # No procede (duplicada, inválida)
]
```

### 4. Estadísticas y Analytics

```mermaid
sequenceDiagram
    participant Admin as 👨‍💼 Admin
    participant API as 📊 Stats Endpoint
    participant Service as Incidencia Service
    participant DB as 🗄️ PostgreSQL
    
    Admin->>API: GET /api/incidencias/stats
    API->>Service: get_statistics()
    
    Service->>DB: Query con agregaciones
    Note over Service,DB: GROUP BY tipo, estado<br/>COUNT, AVG resolution time
    
    DB-->>Service: Resultados agregados
    
    Service->>Service: Calcular métricas
    Note over Service: - Total por tipo<br/>- Tiempo promedio resolución<br/>- Distribución geográfica
    
    Service-->>API: Estadísticas completas
    API-->>Admin: Dashboard metrics
```

---

## 🚛 Flujo de Conductores

### 1. Asignación de Conductor a Ruta

```mermaid
sequenceDiagram
    participant Admin as 👨‍💼 Admin
    participant API as 🚗 Conductores API
    participant Service as Conductor Service
    participant DB as 🗄️ Database
    
    Admin->>API: GET /api/conductores?estado=disponible
    API->>Service: get_conductores(disponible)
    Service->>DB: SELECT * FROM conductores WHERE estado = 'disponible'
    DB-->>Service: Lista de conductores
    Service-->>API: Conductores disponibles
    API-->>Admin: 200 OK
    
    Admin->>API: POST /api/rutas
    Note over Admin,API: {conductor_id: 5, puntos: [...]}
    
    API->>Service: create_ruta_with_conductor()
    Service->>DB: INSERT INTO rutas
    Service->>DB: UPDATE conductores SET estado = 'asignado'
    
    DB-->>Service: Ruta y conductor actualizados
    Service-->>API: Ruta asignada
    API-->>Admin: 201 Created
```

### 2. Flujo del Conductor en la App Móvil

```mermaid
sequenceDiagram
    participant Conductor as 👨‍🔧 Conductor
    participant App as 📱 App Móvil
    participant API as 🚗 Conductores API
    participant DB as 🗄️ Database
    
    Conductor->>App: Login
    App->>API: POST /api/auth/login
    API-->>App: JWT Token
    
    Conductor->>App: Ver mis rutas
    App->>API: GET /api/conductores/mis-rutas/todas
    Note over App,API: Header: Bearer {token}
    
    API->>DB: SELECT rutas WHERE conductor_id = user.id
    DB-->>API: Lista de rutas asignadas
    API-->>App: Rutas del conductor
    
    Conductor->>App: Iniciar ruta #123
    App->>API: PATCH /api/rutas/123
    Note over App,API: {estado: "en_progreso"}
    API->>DB: UPDATE ruta
    
    loop Para cada punto de la ruta
        App->>App: Mostrar navegación GPS
        Note over App: Google Maps Navigation
        
        Conductor->>App: Llegó al punto
        Conductor->>App: Marcar incidencia como atendida
        
        App->>API: PATCH /api/incidencias/{id}
        Note over App,API: {estado: "en_proceso"}
        API->>DB: UPDATE incidencia
        
        Conductor->>App: Tomar foto de evidencia
        App->>API: POST /api/incidencias/{id}/evidencia
        API->>DB: UPDATE foto_resolucion
    end
    
    Conductor->>App: Finalizar ruta
    App->>API: PATCH /api/rutas/123
    Note over App,API: {estado: "completada"}
    API->>DB: UPDATE ruta + conductor.estado = 'disponible'
```

### 3. Gestión de Conductores

```python
# Estados del conductor
estados_conductor = [
    "disponible",    # Listo para asignación
    "asignado",      # Tiene ruta pero no empezó
    "en_ruta",       # Ejecutando ruta actualmente
    "descanso",      # Pausa temporal
    "inactivo"       # No disponible (día libre, enfermo)
]

# Endpoints principales
GET    /api/conductores              # Listar todos
GET    /api/conductores/{id}         # Ver detalle
POST   /api/conductores              # Crear nuevo
PUT    /api/conductores/{id}         # Actualizar
DELETE /api/conductores/{id}         # Eliminar
PATCH  /api/conductores/{id}/estado  # Cambiar estado
GET    /api/conductores/mis-rutas    # Rutas asignadas (autenticado)
```

---

## 🌍 Integración OSRM (Open Source Routing Machine)

### 1. Arquitectura OSRM

```
┌──────────────────────────────────────────────────────┐
│                  OSRM Backend                        │
├──────────────────────────────────────────────────────┤
│  📦 Datos Pre-procesados                             │
│  - ecuador-latest.osm.pbf (OpenStreetMap)           │
│  - ecuador-latest.osrm.* (indices optimizados)      │
├──────────────────────────────────────────────────────┤
│  🔧 Algoritmos                                       │
│  - MLD (Multi-Level Dijkstra)                       │
│  - Contraction Hierarchies                          │
├──────────────────────────────────────────────────────┤
│  🌐 API REST                                         │
│  - /route/v1/driving/{coordinates}                  │
│  - /nearest/v1/driving/{coordinate}                 │
│  - /table/v1/driving/{coordinates}                  │
└──────────────────────────────────────────────────────┘
```

### 2. Generación de Polyline

```python
# app/osrm_service.py
async def get_route_polyline(puntos: List[dict]) -> str:
    """
    Genera polyline optimizada usando OSRM
    
    Args:
        puntos: Lista de {latitud, longitud, orden}
    
    Returns:
        Polyline encoded string (Google format)
    """
    # Ordenar puntos por orden
    sorted_puntos = sorted(puntos, key=lambda x: x['orden'])
    
    # Formato: longitud,latitud (OSRM usa lon,lat)
    coords = ";".join([
        f"{p['longitud']},{p['latitud']}" 
        for p in sorted_puntos
    ])
    
    # Llamada a OSRM
    url = f"{OSRM_URL}/route/v1/driving/{coords}"
    params = {
        "overview": "full",
        "geometries": "polyline",  # Google polyline format
        "steps": "true"
    }
    
    response = await http_client.get(url, params=params)
    data = response.json()
    
    if data["code"] != "Ok":
        raise OSRMError("No se pudo calcular la ruta")
    
    route = data["routes"][0]
    
    return {
        "polyline": route["geometry"],
        "distance": route["distance"],  # metros
        "duration": route["duration"],  # segundos
        "steps": route["legs"][0]["steps"]
    }
```

### 3. Decodificación de Polyline (Opcional)

```python
# Para visualización o debugging
def decode_polyline(polyline_str: str) -> List[dict]:
    """
    Decodifica polyline a lista de coordenadas
    """
    import polyline  # pip install polyline
    
    coords = polyline.decode(polyline_str)
    return [
        {"latitud": lat, "longitud": lon}
        for lat, lon in coords
    ]
```

### 4. Uso en Frontend

```javascript
// React/Vue - Renderizar polyline en mapa
import { Polyline } from '@react-google-maps/api';

function RutaMapa({ ruta }) {
  const decodedPath = google.maps.geometry.encoding.decodePath(
    ruta.polyline
  );
  
  return (
    <Polyline
      path={decodedPath}
      options={{
        strokeColor: "#2196F3",
        strokeWeight: 4,
        strokeOpacity: 0.8
      }}
    />
  );
}
```

---

## ⚡ Optimización y Rendimiento

### 1. Caching de Rutas

```python
# Implementación futura con Redis
from redis import Redis
import json

redis_client = Redis(host='localhost', port=6379, decode_responses=True)

async def get_ruta_with_cache(ruta_id: int):
    # Intentar obtener de cache
    cache_key = f"ruta:{ruta_id}"
    cached = redis_client.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    # Si no está en cache, obtener de DB
    ruta = await get_ruta_from_db(ruta_id)
    
    # Guardar en cache por 1 hora
    redis_client.setex(
        cache_key,
        3600,
        json.dumps(ruta, default=str)
    )
    
    return ruta
```

### 2. Paginación Eficiente

```python
# app/routers/incidencias.py
@router.get("/incidencias")
async def list_incidencias(
    skip: int = 0,
    limit: int = 20,
    estado: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Incidencia)
    
    if estado:
        query = query.filter(Incidencia.estado == estado)
    
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "items": items,
        "page": skip // limit + 1,
        "pages": (total + limit - 1) // limit
    }
```

### 3. Índices de Base de Datos

```sql
-- Indices para optimizar queries frecuentes

-- Incidencias por estado y fecha
CREATE INDEX idx_incidencias_estado ON incidencias(estado);
CREATE INDEX idx_incidencias_fecha ON incidencias(fecha_reporte DESC);
CREATE INDEX idx_incidencias_estado_fecha ON incidencias(estado, fecha_reporte DESC);

-- Búsquedas geoespaciales (PostGIS)
CREATE INDEX idx_incidencias_ubicacion ON incidencias USING GIST(ubicacion);

-- Rutas por conductor
CREATE INDEX idx_rutas_conductor ON rutas(conductor_id);
CREATE INDEX idx_rutas_fecha ON rutas(fecha_asignacion DESC);

-- Puntos de ruta
CREATE INDEX idx_puntos_ruta ON puntos_ruta(ruta_id, orden);
```

### 4. Compresión de Respuestas

```python
# app/main.py
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

---

## 🔄 Ciclo Completo: De Reporte a Resolución

```mermaid
graph TB
    A[👤 Ciudadano reporta incidencia] --> B[📍 Incidencia creada: PENDIENTE]
    B --> C[👨‍💼 Admin revisa: EN_REVISION]
    C --> D{¿Válida?}
    D -->|No| E[❌ RECHAZADA]
    D -->|Sí| F[📋 Admin crea ruta]
    F --> G[🚗 Asigna conductor: ASIGNADA]
    G --> H[👨‍🔧 Conductor inicia ruta: EN_PROCESO]
    H --> I[📱 Conductor llega al punto]
    I --> J[📸 Toma foto de evidencia]
    J --> K[✅ Marca como: RESUELTA]
    K --> L[🏁 Finaliza ruta]
    L --> M[📊 Estadísticas actualizadas]
```

---

## 🔧 Configuración de Ambiente

### Variables de Entorno Clave

```bash
# Base de datos
DB_URL=postgresql://user:pass@host/db?sslmode=require

# Autenticación
JWT_SECRET=tu_secreto_super_seguro_aqui
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_DAYS=30

# OSRM
OSRM_URL=http://localhost:5000          # Local
# OSRM_URL=http://router.project-osrm.org  # Público
# OSRM_URL=http://osrm:5000              # Docker

# CORS (hardcoded en main.py para producción)
# Frontend production, localhost, mobile apps

# Notificaciones (futuro)
RABBITMQ_URL=amqp://user:pass@host:5672/

# Ambiente
ENV=production  # o development
PORT=8081
```

---

## 📊 Métricas y Monitoreo

### KPIs del Sistema

```python
# Métricas importantes a trackear

1. Incidencias
   - Total reportadas por día/semana/mes
   - Tiempo promedio de resolución
   - Distribución por tipo
   - Tasa de resolución (resueltas/totales)

2. Rutas
   - Rutas completadas vs asignadas
   - Distancia total recorrida
   - Tiempo promedio por ruta
   - Eficiencia (incidencias/ruta)

3. Conductores
   - Tasa de disponibilidad
   - Rutas por conductor
   - Tiempo activo vs inactivo

4. Sistema
   - Requests por minuto
   - Tiempo de respuesta API
   - Errores 4xx/5xx
   - Cache hit rate
```

---

## 🚀 Escalabilidad Futura

### Mejoras Planeadas

1. **Notificaciones en Tiempo Real**
   - WebSockets para updates live
   - Push notifications móviles
   - RabbitMQ para mensajería asíncrona

2. **Machine Learning**
   - Predicción de zonas con más incidencias
   - Optimización de rutas con ML
   - Clustering automático de incidencias

3. **Analytics Avanzado**
   - Dashboard con gráficos interactivos
   - Heatmaps de incidencias
   - Reportes exportables (PDF/Excel)

4. **Microservicios**
   - Separar Auth, Rutas, Incidencias
   - API Gateway (Kong/Traefik)
   - Service mesh (Istio)

---

## 📞 Soporte y Mantenimiento

### Logs y Debugging

```python
# Configuración de logging
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Uso en código
logger.info(f"Ruta {ruta_id} creada exitosamente")
logger.error(f"Error en OSRM: {error}")
logger.warning(f"Incidencia {inc_id} sin coordenadas válidas")
```

### Health Checks

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.utcnow(),
        "services": {
            "database": check_db_connection(),
            "osrm": check_osrm_connection()
        }
    }
```

---

**Documentación actualizada:** Diciembre 2024  
**Versión del Sistema:** 2.0.0  
**Contacto:** [Tu información de contacto]
