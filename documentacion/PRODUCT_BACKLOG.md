# 📊 Product Backlog - EPAGAL Backend

**Proyecto:** EPAGAL - Sistema de Gestión Automática de Rutas de Distribución de Residuos  
**Versión:** 2.0.1  
**Última Actualización:** 2 de febrero de 2026  
**Estado General:** En Desarrollo (Sprint 1 Completado, Sprint 2 En Progreso)

---

## 📋 Tabla de Contenidos

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Historias de Usuario Completadas](#historias-de-usuario-completadas)
3. [Historias de Usuario En Progreso](#historias-de-usuario-en-progreso)
4. [Historias de Usuario Pendientes](#historias-de-usuario-pendientes)
5. [Épicas](#épicas)
6. [Métricas del Proyecto](#métricas-del-proyecto)
7. [Timeline y Roadmap](#timeline-y-roadmap)
8. [Dependencias entre Historias](#dependencias-entre-historias)
9. [Próximas Acciones](#próximas-acciones)

---

## 🎯 Resumen Ejecutivo

### Estado Actual:
- **Total de Historias:** 28
- **Completadas:** 12 (42.8%)
- **En Progreso:** 4 (14.2%)
- **Pendientes:** 12 (42.8%)

### Sprints:
- **Sprint 1 (Dic 2025 - Ene 2026):** ✅ Completado
  - Motor OSRM
  - CI/CD Pipeline
  - Generación de Rutas
  - Base de Datos PostgreSQL+PostGIS
  - Autenticación JWT

- **Sprint 2 (Ene 2026 - Feb 2026):** 🔄 En Progreso
  - Reporte de Incidencias con Geolocalización
  - Asignación de Rutas a Conductores
  - Navegación en Tiempo Real

### Progreso General:
```
Puntos Completados:    47 / 200 (23.5%)
Puntos En Progreso:    48 / 200 (24%)
Puntos Pendientes:    105 / 200 (52.5%)
```

---

## ✅ Historias de Usuario Completadas

### 1. **RF-01: Autenticación de Usuarios (Login)**
- **Estado:** ✅ COMPLETADA
- **Puntos:** 8
- **Sprint:** 1
- **Descripción:** Sistema de login con usuario/contraseña, generación de JWT token
- **Criterios de Aceptación:**
  - ✅ Endpoint `POST /api/auth/login` funcional
  - ✅ Generación de JWT token (24h expiración)
  - ✅ Validación de credenciales contra BD
  - ✅ Manejo de errores (401, 400)
- **Archivos:**
  - `app/routers/auth.py`
  - `app/services/auth_service.py`
  - `app/schemas/auth.py`
- **Dependencias:** PostgreSQL, models.User
- **Notas:** Token incluye claims: sub, exp, iat, roles
- **Ejemplo de Request:**
```json
POST /api/auth/login
Content-Type: application/json

{
  "email": "admin@epagal.com",
  "password": "securepassword123"
}
```
- **Ejemplo de Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": 1,
    "email": "admin@epagal.com",
    "nombre": "Administrador",
    "rol": "admin"
  }
}
```

---

### 2. **RF-02: Refresh Token JWT**
- **Estado:** ✅ COMPLETADA
- **Puntos:** 5
- **Sprint:** 1
- **Descripción:** Renovación de access token usando refresh token
- **Criterios de Aceptación:**
  - ✅ Endpoint `POST /api/auth/refresh` funcional
  - ✅ Validación de refresh token
  - ✅ Generación de nuevo access token
  - ✅ Manejo de errores (401)
- **Archivos:**
  - `app/routers/auth.py`
  - `app/services/auth_service.py`
- **Ejemplo de Request:**
```json
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

### 3. **RF-03: Protección de Endpoints con JWT**
- **Estado:** ✅ COMPLETADA
- **Puntos:** 8
- **Sprint:** 1
- **Descripción:** Middleware y dependencias para proteger endpoints
- **Criterios de Aceptación:**
  - ✅ Middleware JWT global implementado
  - ✅ Validación en header `Authorization: Bearer`
  - ✅ Inyección de usuario autenticado
  - ✅ Retorna 401 si token inválido
  - ✅ Retorna 403 si permisos insuficientes
- **Archivos:**
  - `app/main.py` (middleware)
  - `app/services/auth_service.py`
- **Dependencias:** PyJWT, python-jose
- **Uso en endpoints:**
```python
@router.get("/incidencias")
async def listar_incidencias(
    current_user: Annotated[Usuario, Depends(get_current_user)]
):
    # Solo usuarios autenticados pueden acceder
    return {"incidencias": [...]}
```

---

### 4. **RF-04: Logout e Invalidación de Token**
- **Estado:** ✅ COMPLETADA
- **Puntos:** 5
- **Sprint:** 1
- **Descripción:** Cerrar sesión y agregar token a blacklist
- **Criterios de Aceptación:**
  - ✅ Endpoint `POST /api/auth/logout`
  - ✅ Invalidación de token
  - ✅ Verificación de blacklist en middleware
- **Archivos:**
  - `app/routers/auth.py`
  - Redis blacklist (opcional)
- **Ejemplo de Request:**
```json
POST /api/auth/logout
Authorization: Bearer {access_token}
```

---

### 5. **RF-05: Configuración de Motor OSRM**
- **Estado:** ✅ COMPLETADA
- **Puntos:** 13
- **Sprint:** 1
- **Descripción:** Integración con OSRM para cálculo de rutas
- **Criterios de Aceptación:**
  - ✅ Cliente HTTP OSRM implementado
  - ✅ Decodificación de polyline
  - ✅ Manejo de errores y timeouts
  - ✅ Caché de resultados (opcional)
- **Archivos:**
  - `app/osrm_service.py`
  - `osrm-ecuador/` (datos OSRM)
- **Tecnologías:** OSRM API, polyline-codec
- **Rendimiento:** < 2s por solicitud
- **Ejemplo de uso:**
```python
from app.osrm_service import calcular_ruta

# Calcular ruta entre dos puntos
ruta = calcular_ruta(
    inicio=(lat_inicio, lon_inicio),
    fin=(lat_fin, lon_fin),
    intermedios=[(lat2, lon2), (lat3, lon3)]
)

# Resultado: polyline, duración, distancia
print(ruta['polyline'])  # Encoded polyline
print(ruta['duration'])  # Segundos
print(ruta['distance'])  # Metros
```

---

### 6. **RF-06: Configuración DevSecOps y CI/CD**
- **Estado:** ✅ COMPLETADA
- **Puntos:** 13
- **Sprint:** 1
- **Descripción:** Pipeline GitHub Actions → Docker Hub → Render
- **Criterios de Aceptación:**
  - ✅ Workflow `.github/workflows/deploy.yml` funcional
  - ✅ Build Docker con caché
  - ✅ Push a Docker Hub
  - ✅ Deploy a Render automático
  - ✅ Health checks después de deploy
  - ✅ Logs y diagnósticos completos
- **Archivos:**
  - `.github/workflows/deploy.yml`
  - `Dockerfile`
  - `CI_CD_PIPELINE_README.md`
- **Secretos Requeridos:**
  - `DOCKER_USERNAME`, `DOCKER_PASSWORD`
  - `RENDER_API_KEY`, `RENDER_SERVICE_ID`
- **Tiempo Total:** 5-10 minutos por ciclo
- **Flujo:**
```
git push origin main
    ↓
GitHub Actions detecta push
    ↓
Build Docker image (2-5 min)
    ↓
Push a Docker Hub (30 seg)
    ↓
Deploy a Render (1-3 min)
    ↓
Health checks (30 seg - 1 min)
    ↓
✅ Aplicación en producción
```

---

### 7. **RF-07: Configuración Base de Datos PostgreSQL+PostGIS**
- **Estado:** ✅ COMPLETADA
- **Puntos:** 13
- **Sprint:** 1
- **Descripción:** BD relacional con soporte geoespacial
- **Criterios de Aceptación:**
  - ✅ Migraciones SQL aplicadas
  - ✅ Tablas creadas (incidencias, rutas, conductores, etc)
  - ✅ Índices geoespaciales
  - ✅ Constraints y relaciones
- **Archivos:**
  - `app/database.py`
  - `app/models.py`
  - `migrations/` (001_*.sql, 002_*.sql, etc)
- **Tablas Principales:**
  - `users` - Autenticación
  - `incidencias` - Reportes ciudadanos
  - `rutas_generadas` - Rutas optimizadas
  - `rutas_detalle` - Puntos en ruta
  - `conductores` - Datos de conductores
  - `asignaciones_conductor` - Asignaciones
  - `camiones` - Vehículos disponibles
- **Extensiones:** PostGIS 3.5
- **Comando para crear extensión:**
```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
```

---

### 8. **RF-08: Modelos de BD (SQLAlchemy/ORM)**
- **Estado:** ✅ COMPLETADA
- **Puntos:** 8
- **Sprint:** 1
- **Descripción:** Modelos ORM para todas las entidades
- **Criterios de Aceptación:**
  - ✅ Modelos User, Incidencia, Ruta, Conductor, etc
  - ✅ Relaciones entre modelos definidas
  - ✅ Tipos de datos correctos (GEOMETRY, ENUM, etc)
  - ✅ Validaciones en modelo
- **Archivos:**
  - `app/models.py`
- **Tecnologías:** SQLAlchemy, GeoAlchemy2
- **Ejemplo de modelo:**
```python
class Incidencia(Base):
    __tablename__ = "incidencias"
    
    id = Column(Integer, primary_key=True)
    tipo = Column(String(20), nullable=False)  # acopio, zona_critica, animal_muerto
    gravedad = Column(SmallInteger, nullable=False)  # 1, 3, 5
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    geom = Column(Geometry('POINT', srid=4326))  # PostGIS geometry
    estado = Column(String(15), default='pendiente')
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
```

---

### 9. **RF-09: Generación Automática de Rutas**
- **Estado:** ✅ COMPLETADA
- **Puntos:** 13
- **Sprint:** 1
- **Descripción:** Sistema inteligente que genera rutas automáticamente cuando se supera umbral
- **Criterios de Aceptación:**
  - ✅ Endpoint `POST /api/rutas/generar/{zona}` funcional
  - ✅ Cálculo de suma de gravedad por zona
  - ✅ Detección de solapamiento (< 500m)
  - ✅ Generación de ruta con polyline
  - ✅ Asignación de camiones según capacidad
  - ✅ Cambio de estado de incidencias a "asignada"
- **Archivos:**
  - `app/routers/rutas.py`
  - `app/services/ruta_service.py`
  - `app/schemas/incidencias.py`
- **Reglas de Negocio:**
  - Umbral: 20 puntos
  - Radio anti-solapamiento: 500m
  - Capacidades: Posterior=25, Lateral=15
- **Algoritmo:**
```
1. Obtener incidencias validadas por zona
2. Calcular suma de gravedad
3. Si suma > umbral:
   a. Verificar no hay ruta en zona dentro de 500m
   b. Optimizar orden de puntos (TSP)
   c. Asignar camiones según capacidad
   d. Crear RutaGenerada
   e. Cambiar incidencias a estado "asignada"
4. Retornar ruta creada
```

---

### 10. **RF-10: Obtener Ruta con Polyline**
- **Estado:** ✅ COMPLETADA
- **Puntos:** 8
- **Sprint:** 1
- **Descripción:** Endpoint que retorna ruta completa con geometría codificada
- **Criterios de Aceptación:**
  - ✅ Endpoint `GET /api/rutas/{id}` funcional
  - ✅ Retorna polyline (Google format)
  - ✅ Retorna puntos (depósito, incidencias, botadero)
  - ✅ Incluye información de incidencias
  - ✅ Manejo de errores (404)
- **Archivos:**
  - `app/routers/rutas.py`
  - `app/services/ruta_service.py`
- **Formato Respuesta:** JSON con polyline + puntos
- **Ejemplo de Response:**
```json
{
  "id": 1,
  "zona": "oriental",
  "polyline": "wfdxEj~sxCqCpBsCvA_BjCkArCgA|Bo@~B",
  "distancia_total": 15234,
  "duracion_estimada": 1800,
  "estado": "planeada",
  "puntos": [
    {
      "orden": 1,
      "tipo": "deposito",
      "lat": -0.9281,
      "lon": -78.6191,
      "nombre": "Depósito Central"
    },
    {
      "orden": 2,
      "tipo": "incidencia",
      "lat": -0.9350,
      "lon": -78.6150,
      "incidencia_id": 5,
      "descripcion": "Basura acumulada"
    }
  ]
}
```

---

### 11. **RF-11: Listar Rutas con Filtros**
- **Estado:** ✅ COMPLETADA
- **Puntos:** 8
- **Sprint:** 1
- **Descripción:** Obtener historial de rutas con filtros (estado, zona, fecha)
- **Criterios de Aceptación:**
  - ✅ Endpoint `GET /api/rutas/historial?estado=X&zona=Y`
  - ✅ Filtrado por estado (planeada, asignada, en_ejecucion, completada)
  - ✅ Filtrado por zona (oriental, occidental)
  - ✅ Paginación (skip, limit)
  - ✅ Ordenamiento por fecha descendente
- **Archivos:**
  - `app/routers/rutas.py`
- **Ejemplo de Request:**
```
GET /api/rutas/historial?estado=completada&zona=oriental&skip=0&limit=10
Authorization: Bearer {token}
```
- **Ejemplo de Response:**
```json
{
  "total": 45,
  "skip": 0,
  "limit": 10,
  "rutas": [
    {
      "id": 1,
      "zona": "oriental",
      "estado": "completada",
      "fecha_generacion": "2026-01-12T10:30:00",
      "suma_gravedad": 21,
      "camiones_usados": 1
    }
  ]
}
```

---

### 12. **RF-12: Visualizar Rutas en Calendario**
- **Estado:** ✅ COMPLETADA
- **Puntos:** 8
- **Sprint:** 1
- **Descripción:** Agrupar rutas por fecha en calendario
- **Criterios de Aceptación:**
  - ✅ Endpoint `GET /api/rutas/calendario/activas`
  - ✅ Agrupación por fecha
  - ✅ Estadísticas por día (total, estados, conductores)
  - ✅ Filtros por zona y estado
  - ✅ Excluye rutas "planeada" sin asignar
- **Archivos:**
  - `app/routers/rutas.py`
- **Ejemplo de Response:**
```json
{
  "2026-01-12": {
    "total": 3,
    "completadas": 2,
    "en_ejecucion": 1,
    "conductores": ["Juan", "María"],
    "rutas": [
      {
        "id": 1,
        "estado": "completada",
        "zona": "oriental"
      }
    ]
  }
}
```

---

## 🔄 Historias de Usuario En Progreso

### 1. **RF-13: Reporte de Incidencias con Geolocalización**
- **Estado:** 🔄 EN PROGRESO
- **Puntos:** 13
- **Sprint:** 2
- **Descripción:** Sistema para que ciudadanos reporten incidencias con ubicación GPS
- **Criterios de Aceptación:**
  - ⏳ Endpoint `POST /api/incidencias` para crear incidencia
  - ⏳ Captura de coordenadas (lat/lon)
  - ⏳ Almacenamiento en PostGIS
  - ⏳ Estado inicial "Pendiente"
  - ⏳ Validación de límites geográficos de Latacunga
  - ⏳ Subida de foto (opcional)
- **Archivos:**
  - `app/routers/incidencias.py`
  - `app/services/incidencia_service.py`
  - `app/schemas/incidencias.py`
- **BDD Scenarios:** 8
- **Dependencias:** PostGIS, almacenamiento de archivos
- **Estimación:** 3-4 días
- **Especificación Detallada:**

#### Endpoint: POST /api/incidencias
```json
POST /api/incidencias
Content-Type: application/json

{
  "tipo": "acopio",
  "descripcion": "Se encuentra basura acumulada en la esquina",
  "lat": -0.936,
  "lon": -78.615,
  "foto_url": "https://storage.example.com/foto1.jpg"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "tipo": "acopio",
  "gravedad": 1,
  "descripcion": "Se encuentra basura acumulada en la esquina",
  "lat": -0.936,
  "lon": -78.615,
  "foto_url": "https://storage.example.com/foto1.jpg",
  "zona": "occidental",
  "estado": "pendiente",
  "reportado_en": "2026-02-02T14:30:00",
  "created_at": "2026-02-02T14:30:00"
}
```

#### Gherkin Scenarios:

```gherkin
Feature: Reporte de Incidencias con Geolocalización
  Como ciudadano de Latacunga
  Quiero reportar una incidencia con ubicación GPS
  Para que el sistema la gestione automáticamente

Scenario: Envío exitoso de incidencia con geolocalización
  Given el ciudadano está en la app móvil
  When completa el formulario con tipo="acopio" y permite acceso GPS
  And captura coordenadas lat=-0.936, lon=-78.615
  Then se almacena en BD con estado="pendiente"
  And se calcula automáticamente gravedad=1
  And se determina zona="occidental"

Scenario: Validación de coordenadas fuera de límites
  Given un ciudadano intenta reportar
  When envía coordenadas lat=40.7128, lon=-74.0060 (Nueva York)
  Then retorna HTTP 400 "Coordenadas fuera de Latacunga"

Scenario: Subida de foto junto con incidencia
  Given el ciudadano captura una foto de la incidencia
  When la envía junto con formulario
  Then se almacena en bucket S3/Azure
  And se vincula URL en incidencia

Scenario: Determinación automática de zona
  Given una incidencia con lon=-78.6191
  When se valida geográficamente
  Then se asigna zona="oriental"

Scenario: Cálculo automático de gravedad
  Given incidencia con tipo="animal_muerto"
  When se almacena
  Then gravedad se asigna automáticamente=5

Scenario: Falta de coordenadas GPS
  Given usuario intenta enviar sin GPS
  When no proporciona lat/lon
  Then retorna HTTP 400 "Coordenadas requeridas"

Scenario: Almacenamiento en PostGIS
  Given incidencia guardada
  When se consulta directamente en BD
  Then geom='POINT(-78.615 -0.936)' en SRID 4326

Scenario: Incidencia duplicada en la misma ubicación
  Given dos incidencias casi idénticas (< 50m)
  When segunda se envía después de primera
  Then retorna advertencia (opcional merge)
```

---

### 2. **RF-14: Validación de Incidencias por Administrador**
- **Estado:** 🔄 EN PROGRESO
- **Puntos:** 8
- **Sprint:** 2
- **Descripción:** Administrador valida incidencias y dispara cálculo de umbrales
- **Criterios de Aceptación:**
  - ⏳ Endpoint `PATCH /api/incidencias/{id}/validate`
  - ⏳ Cambio de estado "pendiente" → "validada"
  - ⏳ Cálculo automático de suma de gravedad
  - ⏳ Detección de solapamiento
  - ⏳ Generación de ruta si supera umbral
- **Archivos:**
  - `app/routers/incidencias.py`
  - `app/services/incidencia_service.py`
- **Flujo:**
```
Admin marca incidencia como validada
    ↓
Sistema suma gravedad por zona
    ↓
Si suma > 20:
    a. Detecta solapamiento (< 500m)
    b. Genera ruta automáticamente
    c. Cambia incidencias a "asignada"
    ↓
Si suma <= 20:
    Incidencia queda en "validada" esperando más
```

---

### 3. **RF-15: Asignación de Rutas a Conductores**
- **Estado:** 🔄 EN PROGRESO
- **Puntos:** 8
- **Sprint:** 2
- **Descripción:** Asignar ruta generada a conductor y camión
- **Criterios de Aceptación:**
  - ⏳ Endpoint `POST /api/rutas/{id}/asignar`
  - ⏳ Selección de conductor disponible
  - ⏳ Selección de camión
  - ⏳ Cambio estado ruta a "asignada"
  - ⏳ Notificación a conductor
- **Archivos:**
  - `app/routers/rutas.py`
  - `app/services/ruta_service.py`
- **Ejemplo de Request:**
```json
POST /api/rutas/1/asignar
Authorization: Bearer {token}
Content-Type: application/json

{
  "conductor_id": 5,
  "camion_id": 10,
  "fecha_inicio": "2026-02-03T06:00:00"
}
```

---

### 4. **RF-16: Navegación en Tiempo Real (App Móvil)**
- **Estado:** 🔄 EN PROGRESO
- **Puntos:** 13
- **Sprint:** 2
- **Descripción:** Conductor ve siguiente punto y progreso de ruta
- **Criterios de Aceptación:**
  - ⏳ Endpoint `GET /api/rutas/{id}/navegacion`
  - ⏳ Retorna punto actual vs completados
  - ⏳ GPS con siguiente punto destacado
  - ⏳ Tiempo estimado de llegada
  - ⏳ Progreso visual (% completado)
- **Archivos:**
  - `app/routers/rutas.py`
  - `app/services/ruta_service.py`
- **Ejemplo de Response:**
```json
{
  "ruta_id": 1,
  "progreso": {
    "total_puntos": 8,
    "completados": 3,
    "porcentaje": 37.5
  },
  "punto_actual": {
    "orden": 4,
    "tipo": "incidencia",
    "lat": -0.940,
    "lon": -78.612,
    "descripcion": "Basura en parque",
    "llegada_estimada": "2026-02-03T08:45:00"
  },
  "siguiente_punto": {
    "orden": 5,
    "tipo": "incidencia",
    "lat": -0.935,
    "lon": -78.620,
    "distancia_metros": 750
  },
  "ruta_completa": {
    "polyline": "wfdxEj~sxCqCpBsCvA...",
    "distancia_pendiente": 4500,
    "duracion_pendiente": 900
  }
}
```

---

## ⏳ Historias de Usuario Pendientes

### **Épica 1: Gestión Avanzada de Rutas**

#### 1. **RF-17: Marcar Incidencia como Completada**
- **Estado:** 📋 PENDIENTE
- **Puntos:** 5
- **Descripción:** Conductor marca punto como completado con foto
- **Criterios de Aceptación:**
  - Endpoint `POST /api/rutas/{id}/incidencia/{id}/completar`
  - Captura de foto antes/después
  - Actualización de progreso ruta
  - Si todas completadas → ruta completada automáticamente
- **Prioridad:** 🔴 CRÍTICA
- **Estimación:** 2 días
- **Ejemplo de Request:**
```json
POST /api/rutas/1/incidencia/5/completar
Authorization: Bearer {token}
Content-Type: application/json

{
  "foto_url": "https://storage.example.com/completada.jpg",
  "notas": "Basura recolectada sin problema",
  "tiempo_real": 540
}
```

---

#### 2. **RF-18: Obtener Detalles Completos de Ruta**
- **Estado:** 📋 PENDIENTE
- **Puntos:** 5
- **Descripción:** Vista extendida con todas las incidencias y puntos
- **Criterios de Aceptación:**
  - Endpoint `GET /api/rutas/{id}/detalles`
  - Incluye información completa de incidencias
  - Mostrar fotos y descripciones
  - Estado actual de cada incidencia
- **Prioridad:** 🟡 MEDIA
- **Estimación:** 1 día

---

#### 3. **RF-19: Actualizar Estado de Ruta**
- **Estado:** 📋 PENDIENTE
- **Puntos:** 3
- **Descripción:** Cambiar estado en ciclo de vida
- **Criterios de Aceptación:**
  - Endpoint `PATCH /api/rutas/{id}/estado`
  - Estados: planeada → asignada → en_ejecucion → completada
  - Validación de transiciones válidas
- **Prioridad:** 🔴 CRÍTICA
- **Estimación:** 1 día

---

#### 4. **RF-20: Obtener Información de Navegación**
- **Estado:** 📋 PENDIENTE
- **Puntos:** 8
- **Descripción:** Información paso a paso para navegación
- **Criterios de Aceptación:**
  - Endpoint `GET /api/rutas/{id}/navegacion`
  - Punto actual vs completados
  - Resumen de distancia y duración
  - Incidencias por completar
- **Prioridad:** 🔴 CRÍTICA
- **Estimación:** 2 días

---

### **Épica 2: Reportes y Análisis**

#### 5. **RF-21: Reporte de Incidencias Validadas**
- **Estado:** 📋 PENDIENTE
- **Puntos:** 5
- **Descripción:** Dashboard con incidencias validadas por zona
- **Criterios de Aceptación:**
  - Endpoint `GET /api/reportes/incidencias-validadas`
  - Agrupación por zona y tipo
  - Gráficos de distribución
  - Exportar a CSV/PDF
- **Prioridad:** 🟡 MEDIA
- **Estimación:** 2 días

---

#### 6. **RF-22: Reporte de Desempeño de Rutas**
- **Estado:** 📋 PENDIENTE
- **Puntos:** 8
- **Descripción:** Análisis de rutas ejecutadas (tiempo, distancia, combustible)
- **Criterios de Aceptación:**
  - Rutas completadas vs planeadas
  - Tiempo real vs estimado
  - Distancia recorrida vs estimada
  - Costo de combustible estimado
  - Gráficos de tendencia
- **Prioridad:** 🟡 MEDIA
- **Estimación:** 3 días

---

#### 7. **RF-23: Reporte de Desempeño de Conductores**
- **Estado:** 📋 PENDIENTE
- **Puntos:** 8
- **Descripción:** Métricas por conductor (rutas completadas, tiempo promedio, incidencias)
- **Criterios de Aceptación:**
  - Ranking de conductores
  - Rutas completadas por conductor
  - Promedio de tiempo por incidencia
  - Calificación (estrella 1-5)
- **Prioridad:** 🟡 MEDIA
- **Estimación:** 2 días

---

#### 8. **RF-24: Dashboard Administrativo**
- **Estado:** 📋 PENDIENTE
- **Puntos:** 13
- **Descripción:** Dashboard con KPIs principales
- **Criterios de Aceptación:**
  - Tarjetas: Rutas hoy, incidencias pendientes, conductores activos
  - Gráficos: Distribución por zona, estado de rutas
  - Mapa en vivo con rutas activas
  - Tablas de incidencias recientes
- **Prioridad:** 🔴 CRÍTICA
- **Estimación:** 4 días

---

### **Épica 3: Notificaciones y Tracking**

#### 9. **RF-25: Sistema de Notificaciones en Tiempo Real**
- **Estado:** 📋 PENDIENTE
- **Puntos:** 13
- **Descripción:** WebSockets/Pusher para notificaciones a conductores
- **Criterios de Aceptación:**
  - Notificación cuando se asigna ruta
  - Notificación cambio de estado
  - Notificación nuevas incidencias cercanas
  - Soporte offline (cola de mensajes)
- **Prioridad:** 🔴 CRÍTICA
- **Estimación:** 3 días

---

#### 10. **RF-26: Tracking en Tiempo Real de Conductores**
- **Estado:** 📋 PENDIENTE
- **Puntos:** 13
- **Descripción:** Seguimiento GPS en vivo de conductores
- **Criterios de Aceptación:**
  - Endpoint `POST /api/tracking/update-posicion`
  - Almacenamiento de track (lat/lon/timestamp)
  - Visualización en mapa (WebSocket)
  - Historial de posiciones
  - Alertas de desviación de ruta
- **Prioridad:** 🟡 MEDIA
- **Estimación:** 4 días

---

#### 11. **RF-27: Alertas de Desviación de Ruta**
- **Estado:** 📋 PENDIENTE
- **Puntos:** 8
- **Descripción:** Detectar cuando conductor se desvía > 500m
- **Criterios de Aceptación:**
  - Cálculo de distancia vs ruta planeada
  - Alerta visual/audio en app móvil
  - Notificación a supervisor
  - Opción de recalcular ruta
- **Prioridad:** 🟡 MEDIA
- **Estimación:** 2 días

---

### **Épica 4: Mantenimiento y Optimización**

#### 12. **RF-28: Tests Automatizados Completos**
- **Estado:** 📋 PENDIENTE
- **Puntos:** 13
- **Descripción:** Suite de tests (unitarios, integración, E2E)
- **Criterios de Aceptación:**
  - Tests unitarios: > 80% cobertura
  - Tests integración: APIs principales
  - Tests E2E: flujos críticos
  - CI corre tests antes de deploy
- **Prioridad:** 🔴 CRÍTICA
- **Estimación:** 5 días

---

## 📊 Épicas

### **Épica A: Autenticación y Seguridad** ✅
- **Historias:** RF-01, RF-02, RF-03, RF-04
- **Estado:** ✅ COMPLETADA
- **Puntos Totales:** 26
- **Cobertura:** 100%
- **Archivos:** `app/routers/auth.py`, `app/services/auth_service.py`

### **Épica B: Infraestructura y DevOps** ✅
- **Historias:** RF-05, RF-06, RF-07, RF-08
- **Estado:** ✅ COMPLETADA
- **Puntos Totales:** 47
- **Cobertura:** 100%
- **Archivos:** `.github/workflows/deploy.yml`, `Dockerfile`, `app/database.py`

### **Épica C: Gestión de Rutas** 🔄
- **Historias:** RF-09, RF-10, RF-11, RF-12, RF-13, RF-14, RF-15, RF-16, RF-17, RF-18, RF-19, RF-20
- **Estado:** 🔄 EN PROGRESO
- **Puntos Totales:** 102
- **Completadas:** 5/12 (41.6%)
- **En Progreso:** 4/12 (33.3%)
- **Pendientes:** 3/12 (25%)
- **Archivos:** `app/routers/rutas.py`, `app/routers/incidencias.py`, `app/services/ruta_service.py`

### **Épica D: Reportes y Análisis** 📋
- **Historias:** RF-21, RF-22, RF-23, RF-24
- **Estado:** 📋 PENDIENTE
- **Puntos Totales:** 34
- **Cobertura:** 0%
- **Archivos Propuestos:** `app/routers/reportes.py`, `app/services/reporte_service.py`

### **Épica E: Notificaciones y Tracking** 📋
- **Historias:** RF-25, RF-26, RF-27
- **Estado:** 📋 PENDIENTE
- **Puntos Totales:** 34
- **Cobertura:** 0%
- **Archivos Propuestos:** `app/routers/tracking.py`, `app/routers/notificaciones.py`

### **Épica F: Testing y QA** 📋
- **Historias:** RF-28
- **Estado:** 📋 PENDIENTE
- **Puntos Totales:** 13
- **Cobertura:** 0%
- **Archivos Propuestos:** `tests/test_*.py`

---

## 📈 Métricas del Proyecto

### Progreso General
```
Puntos Completados:    47 / 200 (23.5%)
Puntos En Progreso:    48 / 200 (24%)
Puntos Pendientes:    105 / 200 (52.5%)
────────────────────────────────
Total Proyectado:     200 puntos
```

### Por Épica
```
Épica A (Autenticación):      26/26 puntos   ✅ (100%)
Épica B (Infraestructura):    47/47 puntos   ✅ (100%)
Épica C (Rutas):             41/102 puntos   🔄 (40.1%)
  - Completadas: 47 puntos (RF-01 a RF-12)
  - En progreso: 48 puntos (RF-13 a RF-16)
  - Pendientes: 7 puntos (RF-17 a RF-20)
Épica D (Reportes):           0/34 puntos    ⏳ (0%)
Épica E (Notificaciones):     0/34 puntos    ⏳ (0%)
Épica F (Testing):            0/13 puntos    ⏳ (0%)
────────────────────────────────────────────
TOTAL:                       114/200 puntos (57%)
```

### Velocidad del Team
```
Sprint 1 (2 semanas - Dic 2025 a Ene 2026):
  - Puntos completados: 47
  - Velocidad: 23.5 puntos/semana
  - Historias completadas: 12
  - Burndown: Lineal (buen ritmo)
  - Eficiencia: 95%

Sprint 2 (2 semanas estimadas - Ene 26 a Feb 9):
  - Puntos planeados: 48
  - Velocidad esperada: 25-30 puntos/semana
  - Historias planeadas: 4
  - Eficiencia esperada: 90-95%

Promedio:
  - Velocidad sostenible: 24 puntos/semana
  - Ciclo de release: 2 semanas
```

### Factores de Riesgo y Mitigaciones

| # | Riesgo | Impacto | Probabilidad | Mitigación |
|---|--------|---------|--------------|-----------|
| 1 | Disponibilidad OSRM | Alto | Baja | Tener fallback a OSRM público |
| 2 | Latencia BD | Medio | Media | Índices geoespaciales + caché |
| 3 | Escalabilidad concurrencia | Medio | Media | Rate limiting + colas (Celery) |
| 4 | Cambios en requerimientos | Medio | Alta | Documentación + feedback semanal |
| 5 | Integración app móvil | Alto | Media | API contracts definidos early |
| 6 | PostGIS setup en producción | Medio | Baja | Tests de migración automatizados |

---

## 🗓️ Timeline y Roadmap

### Fase 1: Core (Completada) ✅
**Fechas:** Dic 2025 - Ene 2026  
**Historias:** RF-01 a RF-12  
**Entregable:** Backend funcional con API de rutas básicas  
**Estado:** ✅ COMPLETADA

```
Semana 1-2 (Dic 20-Jan 3):
  ✅ RF-01: Autenticación JWT
  ✅ RF-02: Refresh Token
  ✅ RF-03: Protección endpoints
  ✅ RF-04: Logout
  ✅ RF-05: Motor OSRM
  ✅ RF-07: Base de datos

Semana 3-4 (Jan 3-17):
  ✅ RF-06: CI/CD Pipeline
  ✅ RF-08: Modelos ORM
  ✅ RF-09: Generación rutas
  ✅ RF-10: Obtener ruta
  ✅ RF-11: Listar rutas
  ✅ RF-12: Calendario
```

### Fase 2: MVP (En Progreso) 🔄
**Fechas:** Ene 26 - Feb 9, 2026  
**Historias:** RF-13 a RF-20  
**Entregable:** Backend + App móvil básica funcional  
**Estado:** 🔄 EN PROGRESO (50%)

```
Semana 5-6 (Jan 26-Feb 9):
  🔄 RF-13: Reporte incidencias (EN PROGRESO)
  🔄 RF-14: Validar incidencias (EN PROGRESO)
  🔄 RF-15: Asignar rutas (EN PROGRESO)
  🔄 RF-16: Navegación (EN PROGRESO)
  ⏳ RF-17: Marcar completada (PENDIENTE)
  ⏳ RF-18: Detalles ruta (PENDIENTE)
  ⏳ RF-19: Estado ruta (PENDIENTE)
  ⏳ RF-20: Info navegación (PENDIENTE)
```

### Fase 3: Advanced Features (Planeado) 📋
**Fechas:** Feb 10 - Feb 24, 2026  
**Historias:** RF-21 a RF-24  
**Entregable:** Reportes y dashboard administrativo

```
Semana 7-8 (Feb 10-24):
  📋 RF-21: Reportes incidencias
  📋 RF-22: Reporte desempeño rutas
  📋 RF-23: Reporte desempeño conductores
  📋 RF-24: Dashboard administrativo
```

### Fase 4: Realtime & Optimization (Planeado) 📋
**Fechas:** Feb 25 - Mar 10, 2026  
**Historias:** RF-25 a RF-27  
**Entregable:** Tracking en tiempo real, notificaciones

```
Semana 9-10 (Feb 25-Mar 10):
  📋 RF-25: Notificaciones realtime
  📋 RF-26: Tracking GPS en vivo
  📋 RF-27: Alertas de desviación
  📋 Optimizaciones de performance
```

### Fase 5: Testing & Deployment (Planeado) 📋
**Fechas:** Mar 11 - Mar 24, 2026  
**Historias:** RF-28  
**Entregable:** Suite completa de tests, preparación producción

```
Semana 11-12 (Mar 11-24):
  📋 RF-28: Tests automatizados
     - Tests unitarios (> 80% cobertura)
     - Tests integración (APIs)
     - Tests E2E (flujos críticos)
     - Load testing
     - Security scanning
     - Go-live preparation
```

---

## 🔗 Dependencias entre Historias

```
RF-01 (Login)
  ├─ RF-03 (Protección endpoints) ✅
  │   ├─ RF-09 (Generar rutas) ✅ - Requiere auth
  │   ├─ RF-13 (Reporte incidencias) 🔄 - Requiere auth
  │   └─ RF-15 (Asignar rutas) 🔄 - Requiere auth
  │
  ├─ RF-02 (Refresh token) ✅
  └─ RF-04 (Logout) ✅

RF-05 (Motor OSRM) ✅
  ├─ RF-09 (Generar rutas) ✅ - Requiere OSRM
  └─ RF-10 (Obtener ruta) ✅ - Requiere polyline

RF-07 (Base de datos) ✅
  ├─ RF-08 (Modelos ORM) ✅
  │   ├─ RF-09 (Rutas) ✅
  │   ├─ RF-13 (Incidencias) 🔄
  │   └─ Todas las historias con BD
  │
  └─ RF-06 (CI/CD) ✅ - Deploy a Render

RF-09 (Generar rutas) ✅
  ├─ RF-14 (Validar incidencias) 🔄 - Dispara generación
  ├─ RF-15 (Asignar rutas) 🔄
  └─ RF-19 (Estado ruta) ⏳

RF-13 (Reporte incidencias) 🔄
  ├─ RF-14 (Validar incidencias) 🔄
  │   └─ RF-09 (Generar rutas) ✅
  │
  └─ RF-17 (Marcar completada) ⏳

RF-15 (Asignar rutas) 🔄
  └─ RF-16 (Navegación) 🔄
  └─ RF-17 (Marcar completada) ⏳
  └─ RF-20 (Info navegación) ⏳

RF-24 (Dashboard) ⏳
  ├─ RF-21 (Reportes incidencias) ⏳
  ├─ RF-22 (Reporte rutas) ⏳
  └─ RF-23 (Reporte conductores) ⏳

RF-25 (Notificaciones) ⏳
  ├─ RF-15 (Cuando se asigna ruta) 🔄
  └─ RF-16 (En navegación) 🔄

RF-26 (Tracking) ⏳
  ├─ RF-16 (Navegación) 🔄
  └─ RF-27 (Alertas desviación) ⏳

RF-28 (Tests) ⏳
  └─ Depende de todas las anteriores
```

---

## 📋 Próximas Acciones

### Inmediato (Esta semana)
- [ ] **Completar RF-13** (Reporte de incidencias)
  - Implementar endpoint POST /api/incidencias
  - Validar coordenadas GPS
  - Almacenar en PostGIS
  - Tests de Gherkin
  
- [ ] **Iniciar RF-14** (Validación de incidencias)
  - Endpoint PATCH /api/incidencias/{id}/validate
  - Disparo automático de generación de rutas
  
- [ ] **Code review** de RF-15 (Asignación)
  - Endpoint POST /api/rutas/{id}/asignar
  - Notificación a conductor
  
- [ ] **Preparar tests** para RF-16 (Navegación)
  - Escenarios de prueba

### Corto Plazo (2 semanas)
- [ ] Completar Sprint 2 (RF-13 a RF-20)
- [ ] QA testing de funcionalidades
- [ ] Documentación de APIs en Swagger
- [ ] Feedback con stakeholders
- [ ] **Iniciar Fase 3:** Reportes (RF-21 a RF-24)

### Mediano Plazo (1 mes)
- [ ] Completar reportes (RF-21 a RF-24)
- [ ] Implementar notificaciones (RF-25)
- [ ] Iniciar tracking (RF-26, RF-27)
- [ ] Preparar ambiente de staging
- [ ] Tests de integración

### Largo Plazo (2 meses)
- [ ] Suite completa de tests (RF-28)
- [ ] Load testing y optimizaciones
- [ ] Security audit y penetration testing
- [ ] Preparación para go-live
- [ ] Capacitación de operadores

---

## 📊 Resumen de Estado por Arquitectura

### Backend FastAPI
```
✅ Completado:
  - Framework FastAPI + Uvicorn
  - Middleware CORS
  - Autenticación JWT
  - Modelos SQLAlchemy + GeoAlchemy2
  - ORM mappings
  - Servicios de lógica

🔄 En Progreso:
  - Endpoints de incidencias
  - Validación de incidencias
  - Asignación de rutas
  - Navegación

📋 Pendiente:
  - Reportes
  - Notificaciones
  - Tracking
  - Tests automatizados
```

### Base de Datos PostgreSQL+PostGIS
```
✅ Completado:
  - Instalación y setup
  - Extensión PostGIS
  - Migraciones SQL
  - Tablas principales
  - Índices geoespaciales

🔄 En Progreso:
  - Optimización de queries
  - Caché de resultados

📋 Pendiente:
  - Particionamiento de tablas (si necesario)
  - Replicación (para HA)
```

### CI/CD
```
✅ Completado:
  - GitHub Actions workflow
  - Docker image build
  - Push a Docker Hub
  - Deploy a Render
  - Health checks
  - Logs y diagnósticos

🔄 En Progreso:
  - Tests en CI

📋 Pendiente:
  - Load testing
  - Security scanning
```

### App Móvil (Propuesta)
```
📋 Pendiente:
  - Login/Logout
  - Reporte de incidencias
  - Navegación GPS
  - Marcar completadas
  - Notificaciones push
  - Tracking
```

---

## 📞 Información de Contacto

**Repositorio:**  
`https://github.com/Andres09xZ/Backend-latacunga-clean`

**Documentación:**  
- `CI_CD_PIPELINE_README.md` - Pipeline detallado
- `HISTORIA_USUARIO_GENERACION_RUTAS.md` - Rutas feature
- `SERVER_TOOLS_AND_FRAMEWORKS.md` - Stack técnico
- `ARQUITECTURA_COMPONENTES.md` - Arquitectura C4

**Aplicación en Vivo:**  
`https://epagal-backend-routing-latest.onrender.com`

**API Docs (Swagger):**  
`https://epagal-backend-routing-latest.onrender.com/docs`

**Docker Hub:**  
`https://hub.docker.com/r/mrengineer09/epagal-backend-routing`

---

## ✍️ Control de Versiones

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 2.0.1 | 2 Feb 2026 | Product Backlog completo, Sprint 2 en progreso |
| 2.0.0 | 12 Ene 2026 | Sprint 1 completado, core features |
| 1.0.0 | 1 Dic 2025 | Inicio del proyecto |

---

**Documento generado:** 2 de febrero de 2026  
**Próxima revisión:** 9 de febrero de 2026  
**Responsable:** EPAGAL Development Team
