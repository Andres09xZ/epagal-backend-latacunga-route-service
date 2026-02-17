# Herramientas y Frameworks usados para el servidor

Este documento lista y describe las herramientas, frameworks y utilidades usadas para desarrollar el servidor de la aplicación (backend). Incluye por qué se usan, dónde se encuentran en el repositorio, comandos útiles y recomendaciones de configuración.

> Nota: He inferido algunas dependencias comunes basadas en la estructura del proyecto (FastAPI, SQLAlchemy, JWT). Si quieres, puedo abrir archivos específicos y poner versiones exactas.

---

## Resumen rápido
- Lenguaje: Python 3.13
- Framework web: FastAPI
- Servidor ASGI: Uvicorn
- ORM: SQLAlchemy
- Validación/serialización: Pydantic (schemas)
- Base de datos: PostgreSQL + PostGIS
- Motor de ruteo: OSRM (Open Source Routing Machine)
- Contenerización: Docker, Docker Compose
- CI/CD: GitHub Actions (workflow en `.github/workflows/deploy.yml`), Docker Hub, Render
- Pruebas: pytest (tests/)
- Otros: JWT para autenticación, logging (módulo logging), scripts de utilidades y migraciones SQL en `migrations/`

---

## Detalle por herramienta / framework

### 1) Python
- Rol: Lenguaje principal del backend.
- Por qué: Ecosistema maduro, buenas librerías para web y geoespacial.
- Archivos relevantes: todo el directorio `app/`.
- Comando rápido (Windows PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Recomendación: usar la versión 3.11+ o 3.13 (la repo indica 3.13). Ver `requirements.txt` para paquetes exactos.

---

### 2) FastAPI
- Rol: Framework web/REST API.
- Por qué: Rápido, asíncrono, documentación automática (Swagger) y validación con Pydantic.
- Archivos relevantes:
  - `app/main.py` (arranque, logging, inclusión de routers)
  - `app/routers/` (endpoints: `incidencias.py`, `rutas.py`, etc.)
  - `app/schemas.py` (Pydantic models)
- Documentación automática: `http://<host>:<port>/docs`

Ejecutar localmente:
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

### 3) Uvicorn (ASGI server)
- Rol: Servidor ASGI para ejecutar FastAPI en producción/desarrollo.
- Archivos relevantes: `run.py` (utiliza `uvicorn.run(...)`).
- Por qué: Rendimiento, es la opción recomendada para FastAPI.

Ejemplo:
```powershell
# arranque directo (dev)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

### 4) SQLAlchemy (ORM)
- Rol: Acceso a base de datos relacional usando ORM.
- Archivos relevantes:
  - `app/database.py` (engine, SessionLocal)
  - `app/models.py` (definición de tablas y relaciones)
- Por qué: Flexibilidad con consultas y compatibilidad con Postgres/PostGIS.

Notas: Las migraciones en este proyecto aparecen como archivos SQL dentro de `migrations/`.

---

### 5) Pydantic (Schemas / Validación)
- Rol: Validación y serialización de datos (requests/responses).
- Archivos relevantes: `app/schemas.py` y uso dentro de routers para request bodies.
- Por qué: Integración nativa con FastAPI y tipos Python.

---

### 6) PostgreSQL + PostGIS
- Rol: Base de datos principal y soporte geoespacial (distancias, geometrías)
- Por qué: PostGIS proporciona funciones geoespaciales necesarias para cálculos (por ejemplo, proximidad y almacenamiento de geometrías).
- Archivos relevantes:
  - `migrations/` (scripts SQL de cambios de esquema)
  - Conexiones: configuradas en `app/database.py` o en variables de entorno

Comando de ejemplo para ejecutar localmente con Docker Compose (si config disponible):
```powershell
docker-compose up -d db
# o si usas el compose completo
docker-compose up -d
```

---

### 7) OSRM (Open Source Routing Machine)
- Rol: Motor de ruteo para calcular rutas optimas, overview y geometría (polyline).
- Por qué: Ruteo offline y control total sobre las peticiones; la app usa OSRM para calcular `polyline`, distancia y duración.
- Archivos relevantes: `app/osrm_service.py` (servicio que realiza llamadas a OSRM)
- Notas: OSRM corre en Docker por lo general (puerto 5000). Ver carpeta `osrm-ecuador/` con datos y archivos generados.

Ejemplo de uso local con Docker:
```powershell
docker run -p 5000:5000 osrm/osrm-backend osrm-routed --algorithm mld /data/your-osrm-file.osrm
```

---

### 8) Docker & Docker Compose
- Rol: Contenerización para desarrollo y producción.
- Archivos relevantes:
  - `Dockerfile`
  - `docker-compose.yml`, `docker-compose.prod.yml`
  - `start-docker.sh`, `start-docker.ps1`
- Por qué: Facilita despliegues coherentes y pruebas locales que replican producción.

Comandos útiles:
```powershell
# Build & run (local)
docker build -t epagal-backend:local .
docker run -p 8000:8000 -e PORT=8000 epagal-backend:local

# Con docker-compose
docker-compose up --build
```

---

### 9) CI/CD (GitHub Actions, Docker Hub, Render)
- Rol: Automatizar build, push y deploy.
- Archivos relevantes:
  - `.github/workflows/deploy.yml` (workflow que construye imagen, push a Docker Hub y despliega en Render)
- Pipeline: Build image -> Push to Docker Hub -> Deploy en Render (workflow configura llamadas a la API de Render)

Notas: El workflow usa secrets (`DOCKER_USERNAME`, `DOCKER_PASSWORD`, `RENDER_API_KEY`, `RENDER_SERVICE_ID`).

---

### 10) Autenticación (JWT)
- Rol: Autenticación y autorización de endpoints mediante tokens JWT.
- Por qué: Sencillo y eficiente para APIs REST.
- Cómo se usa: ejemplos de requests/headers en las pruebas y scripts (Bearer token en llamados a `/api/rutas/...`).
- Librerías típicas: `PyJWT` o uso de utilidades de `fastapi.security`.

---

### 11) Testing (pytest)
- Rol: Ejecutar pruebas automáticas de endpoints y lógica de negocio.
- Archivos relevantes: directorio `tests/`
- Comando:
```powershell
pytest -q
```

---

### 12) Logging y observabilidad
- Rol: Registrar eventos, errores y pasos críticos (por ejemplo validación de incidencias y generación de rutas).
- Archivos relevantes: `app/main.py` (configuración de logging), servicios importantes que usan `logging.getLogger(__name__)`.
- Recomendación: En producción agregar un handler que envíe logs a un sistema central (Papertrail, LogDNA, Datadog) o usar stdout (Render recoge stdout).

---

### 13) Scripts y utilidades varias
- `run.py`: script helper para ejecutar uvicorn programáticamente
- Scripts de mantenimiento: `insertar_puntos_fijos.py`, `preparar_datos_app.py`, `limpiar_datos.py`
- PowerShell helpers: `start-dashboard.ps1`, `start-docker.ps1`, `wait-and-test.ps1`

---

## Comandos útiles (desarrollo local)
- Crear y activar entorno virtual (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

- Ejecutar servidor (dev):
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# o, si usas run.py
python run.py
```

- Ejecutar tests:
```powershell
pytest -q
```

- Levantar servicios con Docker Compose (si quieres Postgres + OSRM):
```powershell
docker-compose up --build
```

---

## Puntos de integración / dónde buscar en el repo
- Rutas y endpoints: `app/routers/rutas.py`
- Incidencias: `app/routers/incidencias.py`
- Modelos: `app/models.py`
- DB engine / sessions: `app/database.py`
- OSRM integration: `app/osrm_service.py`
- Migrations SQL: `migrations/` (archivos `.sql`)
- CI/CD workflow: `.github/workflows/deploy.yml`
- Dockerfiles & compose: `Dockerfile`, `docker-compose.yml`, `docker-compose.prod.yml`
- Tests: `tests/`
- Scripts y utilidades: raíz del proyecto (`run.py`, `start-*.ps1`, `*.py` utilitarios)

---

## Recomendaciones y buenas prácticas
1. Mantener `requirements.txt` actualizado y fijar versiones (ej. FastAPI==0.95.x, uvicorn==0.22.x, SQLAlchemy==1.4/2.x según compatibilidad).
2. Usar variables de entorno para credenciales y URIs (DB, OSRM, JWT secret).
3. Añadir healthchecks (`/health`) y métricas si vas a producción.
4. Hacer backup de la base de datos PostGIS antes de migraciones manuales.
5. Considerar pruebas automatizadas en el workflow (pytest) para que el despliegue falle si hay regresiones.
6. Documentar versiones de OSRM y los datos `.osrm` usados (la carpeta `osrm-ecuador/` almacenó esos artefactos).

---

## ¿Quieres que haga algo más?
- Puedo: 
  - Extraer versiones exactas desde `requirements.txt` y colocarlas en este documento.
  - Añadir pasos para ejecutar OSRM localmente con los archivos en `osrm-ecuador/`.
  - Crear un `README` corto para desarrolladores con los comandos mínimos.
  - Commit y push del archivo `SERVER_TOOLS_AND_FRAMEWORKS.md` por ti.

---

**Archivo creado:** `SERVER_TOOLS_AND_FRAMEWORKS.md` (en la raíz del repo)

*Última actualización: Enero 19, 2026*
