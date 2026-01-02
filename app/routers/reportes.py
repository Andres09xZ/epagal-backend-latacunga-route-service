"""
Router para reportes desde APK
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated, List
from pydantic import BaseModel
from datetime import datetime
from app.database import get_db
from app.models import Report
import uuid

router = APIRouter(prefix="/reportes", tags=["reportes"])


class ReporteCreate(BaseModel):
    description: str
    type: str  # "acopio" o "critico"
    location_lat: float
    location_lon: float
    photo_url: str | None = None
    user_id: str | None = None  # UUID del usuario que reporta (opcional, se asigna uno por defecto)


class ReporteUpdate(BaseModel):
    description: str | None = None
    type: str | None = None
    status: str | None = None  # ENVIADO, EN_PROCESO, COMPLETADO


class ReporteResponse(BaseModel):
    id: str
    description: str | None
    type: str
    status: str | None
    location_lat: float | None = None
    location_lon: float | None = None
    photo_url: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=List[ReporteResponse])
async def listar_reportes(db: Annotated[Session, Depends(get_db)], status: str | None = None):
    """Listar reportes (incidencias de APK)"""
    query = db.query(Report)
    if status:
        query = query.filter(Report.status == status)
    
    reportes = query.all()
    result = []
    for r in reportes:
        reporte_dict = {
            "id": str(r.id),
            "description": r.description,
            "type": r.type,
            "status": r.status,
            "location_lat": r.lat,
            "location_lon": r.lon,
            "photo_url": r.photo_url,
            "created_at": r.created_at,
            "updated_at": r.updated_at,
        }
        result.append(ReporteResponse(**reporte_dict))
    
    return result


@router.post("/", response_model=ReporteResponse)
async def crear_reporte(reporte: ReporteCreate, db: Annotated[Session, Depends(get_db)]):
    """Crear nuevo reporte desde APK"""
    # Validar tipo de reporte según constraint de BD: 'acopio' o 'critico'
    if reporte.type not in ["acopio", "critico"]:
        raise HTTPException(status_code=400, detail="Tipo de reporte inválido. Use 'acopio' o 'critico'")
    
    # Obtener user_id: usar el proporcionado, o asignar uno por defecto
    if reporte.user_id:
        user_id = uuid.UUID(reporte.user_id)
    else:
        # Obtener cualquier usuario existente como default
        from app.models import User
        first_user = db.query(User).first()
        if not first_user:
            raise HTTPException(status_code=400, detail="No hay usuarios disponibles. Proporcione un user_id.")
        user_id = first_user.id
    
    nuevo_reporte = Report(
        id=uuid.uuid4(),
        user_id=user_id,
        description=reporte.description,
        type=reporte.type,
        lat=reporte.location_lat,
        lon=reporte.location_lon,
        photo_url=reporte.photo_url,
        status="ENVIADO",
        synced=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(nuevo_reporte)
    db.commit()
    db.refresh(nuevo_reporte)
    
    # Convertir para respuesta
    response_dict = {
        "id": str(nuevo_reporte.id),
        "description": nuevo_reporte.description,
        "type": nuevo_reporte.type,
        "status": nuevo_reporte.status,
        "location_lat": nuevo_reporte.lat,
        "location_lon": nuevo_reporte.lon,
        "photo_url": nuevo_reporte.photo_url,
        "created_at": nuevo_reporte.created_at,
        "updated_at": nuevo_reporte.updated_at
    }
    
    return ReporteResponse(**response_dict)


@router.get("/{reporte_id}", response_model=ReporteResponse)
async def obtener_reporte(reporte_id: str, db: Annotated[Session, Depends(get_db)]):
    """Obtener reporte por ID"""
    reporte = db.query(Report).filter(Report.id == reporte_id).first()
    if not reporte:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    
    response_dict = {
        "id": str(reporte.id),
        "description": reporte.description,
        "type": reporte.type,
        "status": reporte.status,
        "location_lat": reporte.lat,
        "location_lon": reporte.lon,
        "photo_url": reporte.photo_url,
        "created_at": reporte.created_at,
        "updated_at": reporte.updated_at
    }
    
    return ReporteResponse(**response_dict)


@router.put("/{reporte_id}", response_model=ReporteResponse)
async def actualizar_reporte(reporte_id: str, reporte: ReporteUpdate, db: Annotated[Session, Depends(get_db)]):
    """Actualizar reporte"""
    reporte_actual = db.query(Report).filter(Report.id == reporte_id).first()
    if not reporte_actual:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    
    if reporte.description:
        reporte_actual.description = reporte.description
    if reporte.type:
        if reporte.type not in ["acopio", "critico"]:
            raise HTTPException(status_code=400, detail="Tipo de reporte inválido. Use 'acopio' o 'critico'")
        reporte_actual.type = reporte.type
    if reporte.status:
        reporte_actual.status = reporte.status
    
    reporte_actual.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(reporte_actual)
    
    response_dict = {
        "id": str(reporte_actual.id),
        "description": reporte_actual.description,
        "type": reporte_actual.type,
        "status": reporte_actual.status,
        "location_lat": reporte_actual.lat,
        "location_lon": reporte_actual.lon,
        "photo_url": reporte_actual.photo_url,
        "created_at": reporte_actual.created_at,
        "updated_at": reporte_actual.updated_at
    }
    
    return ReporteResponse(**response_dict)


@router.delete("/{reporte_id}")
async def eliminar_reporte(reporte_id: str, db: Annotated[Session, Depends(get_db)]):
    """Eliminar reporte"""
    reporte = db.query(Report).filter(Report.id == reporte_id).first()
    if not reporte:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    
    db.delete(reporte)
    db.commit()
    return {"message": "Reporte eliminado"}


@router.post("/{reporte_id}/asignar-operador")
async def asignar_operador(reporte_id: str, operador_id: str, db: Annotated[Session, Depends(get_db)]):
    """Asignar operador a un reporte"""
    reporte = db.query(Report).filter(Report.id == reporte_id).first()
    if not reporte:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    
    # Actualizar el user_id con el operador asignado
    reporte.user_id = uuid.UUID(operador_id)
    reporte.status = "EN_PROCESO"
    reporte.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Operador asignado", "reporte_id": reporte_id, "operador_id": operador_id}
