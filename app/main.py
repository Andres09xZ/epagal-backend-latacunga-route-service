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

# Configuración CORS - Orígenes permitidos (hardcoded para producción)
allowed_origins = [
    "https://tesis-1-z78t.onrender.com",  # Frontend en producción
    "http://localhost:3000",               # React/Vue local
    "http://localhost:8080",               # Desarrollo local
    "http://localhost:5173",               # Vite local
    "http://127.0.0.1:3000",              # Localhost alternativo
    "http://127.0.0.1:8080",              # Localhost alternativo
    "capacitor://localhost",               # Capacitor iOS/Android
    "ionic://localhost",                   # Ionic
    "http://localhost",                    # Genérico local
]

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
    expose_headers=["Content-Length", "X-Total-Count", "Content-Disposition"],
    max_age=600,  # Cache preflight requests por 10 minutos
)

# Incluir routers - todos con prefijo /api para unificar
app.include_router(auth.router, prefix="/api")
app.include_router(conductores.router, prefix="/api")
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
