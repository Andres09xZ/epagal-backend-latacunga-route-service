"""
Aplicación principal FastAPI
Sistema de Gestión de Incidencias - EPAGAL Latacunga
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.database import engine, Base
from app.routers import incidencias, rutas, auth, conductores

# Crear tablas
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sistema de Gestión de Incidencias - EPAGAL Latacunga",
    description="API para gestión de reportes ciudadanos y optimización de rutas de recolección",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuración CORS para aplicaciones móviles y frontend
# Orígenes permitidos - configurable por ambiente
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    # Valores por defecto para desarrollo
    "http://localhost:3000,http://localhost:8080,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:8080,capacitor://localhost,ionic://localhost,http://localhost"
).split(",")

# En desarrollo, permitir todos los orígenes
if os.getenv("ENV", "development") == "development":
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "User-Agent",
        "DNT",
        "Cache-Control",
        "X-Requested-With"
    ],
    expose_headers=["Content-Length", "X-Total-Count"],
    max_age=600,  # Cache preflight requests por 10 minutos
)

# Incluir routers
app.include_router(auth.router)
app.include_router(conductores.router)
app.include_router(incidencias.router, prefix="/api")
app.include_router(rutas.router, prefix="/api")


@app.get("/")
def root():
    """Endpoint raíz"""
    return {
        "message": "API Sistema de Gestión de Incidencias - EPAGAL Latacunga",
        "version": "2.0.0",
        "features": [
            "Gestión de incidencias",
            "Rutas optimizadas con OSRM",
            "Autenticación JWT",
            "Gestión de conductores",
            "Asignación automática"
        ],
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "incidencias-api"
    }
