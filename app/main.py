"""
Aplicación principal FastAPI
Sistema de Gestión de Incidencias - EPAGAL Latacunga
ENDPOINTS: /api/incidencias, /api/operadores, /api/horarios, /api/tracking
v2.0.2 - Rate limiting, security headers, DevSecOps hardening
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import logging
from datetime import datetime
import platform
import requests

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

from app.database import engine, Base
from app.routers import (
    incidencias, rutas, auth, conductores, tasks, notifications,
    reports, operadores, horarios, tracking, geofencing
)

logger.info("Iniciando aplicación FastAPI...")

# Crear tablas si no existen (no bloquear arranque)
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Tablas de base de datos verificadas")
except Exception as e:
    logger.warning("DB unavailable during startup: %s", e)

# ── Rate Limiter ──────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

app = FastAPI(
    title="Sistema de Gestión de Incidencias - EPAGAL Latacunga",
    description="API para gestión de reportes ciudadanos, rutas optimizadas y tracking GPS en tiempo real",
    version="2.0.2",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Registrar el rate limiter y su handler de error
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Lista base de orígenes confiables
allowed_origins = [
    "http://localhost:3000",       # Expo / React Native dev (muy común)
    "http://127.0.0.1:3000",
    "http://localhost:8080",       # Dashboard local alternativo
    "http://127.0.0.1:8080",
    # ¡AGREGA AQUÍ tu dominio real de Render cuando lo tengas!
    # "https://tu-nombre-de-proyecto.onrender.com",
    # "https://dashboard.epagal-latacunga.gob.ec",  # ejemplo futuro
]

# En desarrollo/local: más permisivo (pero sin wildcard fijo)
environment = os.getenv("ENVIRONMENT", "development").lower()

if environment in ["development", "local", "dev"]:
    # Opcional: si realmente necesitas * temporalmente en dev, descomenta:
    # allowed_origins.append("*")
    # Pero con el middleware custom abajo ya no debería ser necesario
    pass

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Length", "X-Total-Count", "Content-Disposition"],
    max_age=600,
)

# Middleware custom para soportar apps móviles (sin Origin header)
class MobileCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Si no hay header Origin → muy probable que sea la app móvil
        if "origin" not in request.headers or not request.headers["origin"]:
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            response.headers["Access-Control-Allow-Headers"] = "*"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Max-Age"] = "600"
        
        return response

# Agregar el middleware custom DESPUÉS del CORSMiddleware estándar
app.add_middleware(MobileCORSMiddleware)


# ── Middleware de Security Headers ────────────────────────────
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Agrega headers de seguridad a todas las respuestas (OWASP best practices)"""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(self), camera=(), microphone=()"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# Incluir todos los routers con prefijo /api
app.include_router(auth.router, prefix="/api")
app.include_router(conductores.router, prefix="/api")
app.include_router(incidencias.router, prefix="/api")
app.include_router(rutas.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(operadores.router, prefix="/api")
app.include_router(horarios.router, prefix="/api")
app.include_router(tracking.router, prefix="/api")
app.include_router(geofencing.router)  # Ya tiene su propio prefix

# Montar dashboard estático si existe
dashboard_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dashboard")
if os.path.exists(dashboard_path):
    app.mount("/dashboard", StaticFiles(directory=dashboard_path, html=True), name="dashboard")

# Montar directorio de fotos de incidencias (subidas vía /api/incidencias/foto)
fotos_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fotos_incidencias")
os.makedirs(fotos_path, exist_ok=True)
app.mount("/fotos_incidencias", StaticFiles(directory=fotos_path), name="fotos_incidencias")

@app.get("/")
def root():
    """Endpoint raíz - Información básica de la API"""
    return {
        "message": "API Sistema de Gestión de Incidencias - EPAGAL Latacunga",
        "version": "2.0.2",
        "docs": "/docs",
        "redoc": "/redoc",
        "dashboard": "/dashboard/" if os.path.exists(dashboard_path) else "No disponible",
        "environment": environment
    }

@app.get("/health")
def health_check():
    """
    Health check endpoint - Verifica el estado del servicio
    Útil para monitoreo y verificación de despliegue
    """
    db_status = "ok"
    try:
        from app.database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
    except Exception as e:
        db_status = f"error: {str(e)}"

    osrm_status = "ok"
    try:
        osrm_url = os.getenv("OSRM_URL", "http://osrm:5000")
        response = requests.get(
            f"{osrm_url}/route/v1/driving/-78.617,-0.933;-78.618,-0.934",  # nosemgrep: python.lang.security.audit.insecure-transport.requests.request-with-http.request-with-http
            timeout=2.0
        )
        if response.status_code != 200:
            osrm_status = f"warning: status {response.status_code}"
    except Exception as e:
        osrm_status = f"error: {str(e)}"

    overall_status = "healthy" if "error" not in [db_status, osrm_status] else "degraded"

    return {
        "status": overall_status,
        "service": "EPAGAL Backend - Sistema de Gestión de Incidencias",
        "version": "2.0.2",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": environment,
        "python_version": platform.python_version(),
        "checks": {
            "database": db_status,
            "osrm_service": osrm_status,
            "api": "ok"
        }
    }