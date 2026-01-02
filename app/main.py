"""
Aplicación principal FastAPI
Sistema de Gestión de Incidencias - EPAGAL Latacunga
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.database import engine, Base
from app.routers import incidencias, rutas, auth, conductores, tasks, notifications, reports, reportes

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
    "https://epagal-backend-routing-latest.onrender.com",  # Backend en producción
    "https://tesis-1-z78t.onrender.com",  # Frontend en producción (si existe)
    "http://localhost:3000",               # React/Vue local
    "http://localhost:8000",               # Dashboard local
    "http://localhost:8080",               # Desarrollo local
    "http://localhost:5173",               # Vite local
    "http://127.0.0.1:3000",              # Localhost alternativo
    "http://127.0.0.1:8000",              # Dashboard alternativo
    "http://127.0.0.1:8080",              # Localhost alternativo
    "capacitor://localhost",               # Capacitor iOS/Android
    "ionic://localhost",                   # Ionic
    "http://localhost",                    # Genérico local
    "null",                                # Archivos HTML locales (file://)
    "http://10.52.239.59:7000",           # App operador Expo/React Native
    "http://10.52.239.59:9000",           # Acceso directo desde la red local
    "http://10.52.239.59:8000",           # Dashboard desde la red local
    "http://10.52.239.59",                 # IP base sin puerto
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
app.include_router(tasks.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(reportes.router, prefix="/api")


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
    """
    Health check endpoint - Verifica el estado del servicio
    Útil para monitoreo y verificación de despliegue
    """
    from datetime import datetime
    import platform
    
    # Verificar conexión a base de datos
    db_status = "ok"
    try:
        from app.database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Verificar conexión a OSRM
    osrm_status = "ok"
    try:
        import requests
        osrm_url = os.getenv("OSRM_URL", "http://osrm:5000")
        response = requests.get(f"{osrm_url}/route/v1/driving/-78.617,-0.933;-78.618,-0.934", timeout=2.0)
        if response.status_code != 200:
            osrm_status = f"warning: status {response.status_code}"
    except Exception as e:
        osrm_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "service": "EPAGAL Backend - Sistema de Gestión de Incidencias",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "production"),
        "python_version": platform.python_version(),
        "checks": {
            "database": db_status,
            "osrm_service": osrm_status,
            "api": "ok"
        },
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "api_base": "/api"
        }
    }
