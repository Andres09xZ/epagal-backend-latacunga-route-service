"""
Router de incidencias para FastAPI
"""
from fastapi import APIRouter, Depends, HTTPException, status  # type: ignore[import]
from sqlalchemy.orm import Session  # type: ignore[import]
from pydantic import BaseModel  # type: ignore[import]
from typing import Annotated, List, Optional
from datetime import datetime
from app.database import get_db
from app.models import Incidencia

router = APIRouter(prefix="/incidencias", tags=["incidencias"])


class IncidenciaResponse(BaseModel):
    id: int
    tipo: str
    gravedad: int
    descripcion: str
    foto_url: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    zona: str
    estado: str
    ventana_inicio: Optional[datetime] = None
    ventana_fin: Optional[datetime] = None
    reportado_en: datetime
    usuario_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class IncidenciaCreate(BaseModel):
    tipo: str
    gravedad: int = 1
    descripcion: str
    foto_url: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    zona: str
    usuario_id: int = 1  # Default para testing


@router.get("/stats")
async def estadisticas(db: Annotated[Session, Depends(get_db)]):
    """Estadísticas de incidencias"""
    total = db.query(Incidencia).count()
    
    # Contar por estado
    estados = db.query(Incidencia.estado).distinct().all()
    por_estado = {}
    for (estado_val,) in estados:
        if estado_val:
            count = db.query(Incidencia).filter(Incidencia.estado == estado_val).count()
            por_estado[estado_val] = count
    
    # Contar por zona
    zonas = db.query(Incidencia.zona).distinct().all()
    por_zona = {}
    for (zona_val,) in zonas:
        if zona_val:
            count = db.query(Incidencia).filter(Incidencia.zona == zona_val).count()
            por_zona[zona_val] = count

    return {
        "total": total,
        "por_estado": por_estado,
        "por_zona": por_zona,
    }


@router.get("/", response_model=List[IncidenciaResponse])
async def listar_incidencias(
    db: Annotated[Session, Depends(get_db)],
    estado: Optional[str] = None,
    zona: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
):
    """Listar todas las incidencias"""
    query = db.query(Incidencia)

    if estado:
        query = query.filter(Incidencia.estado == estado)
    if zona:
        query = query.filter(Incidencia.zona == zona)

    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=IncidenciaResponse, status_code=status.HTTP_201_CREATED)
async def crear_incidencia(
    incidencia: IncidenciaCreate,
    db: Annotated[Session, Depends(get_db)]
):
    """Crear nueva incidencia"""
    new_incident = Incidencia(
        tipo=incidencia.tipo,
        gravedad=incidencia.gravedad,
        descripcion=incidencia.descripcion,
        foto_url=incidencia.foto_url,
        lat=incidencia.lat,
        lon=incidencia.lon,
        zona=incidencia.zona,
        usuario_id=incidencia.usuario_id,
        estado="pendiente",
        reportado_en=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(new_incident)
    db.commit()
    db.refresh(new_incident)
    return new_incident


@router.get("/{incidencia_id}", response_model=IncidenciaResponse)
async def obtener_incidencia(incidencia_id: int, db: Annotated[Session, Depends(get_db)]):
    """Obtener una incidencia específica"""
    incidencia = db.query(Incidencia).filter(Incidencia.id == incidencia_id).first()
    if not incidencia:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")
    return incidencia


@router.patch("/{incidencia_id}", response_model=IncidenciaResponse)
async def actualizar_incidencia(
    incidencia_id: int,
    payload: dict,
    db: Annotated[Session, Depends(get_db)]
):
    """Actualizar una incidencia"""
    incidencia = db.query(Incidencia).filter(Incidencia.id == incidencia_id).first()
    if not incidencia:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")

    for key, value in payload.items():
        if hasattr(incidencia, key):
            setattr(incidencia, key, value)

    db.commit()
    db.refresh(incidencia)
    return incidencia


@router.delete("/{incidencia_id}")
async def eliminar_incidencia(incidencia_id: int, db: Annotated[Session, Depends(get_db)]):
    """Eliminar una incidencia"""
    incidencia = db.query(Incidencia).filter(Incidencia.id == incidencia_id).first()
    if not incidencia:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")

    db.delete(incidencia)
    db.commit()
    return {"mensaje": "Incidencia eliminada"}
