"""
Router de incidencias para FastAPI
"""
from fastapi import APIRouter, Depends, HTTPException, status  # type: ignore[import]
from sqlalchemy.orm import Session  # type: ignore[import]
from sqlalchemy import func  # type: ignore[import]
from pydantic import BaseModel  # type: ignore[import]
from typing import Annotated, List, Optional
from datetime import datetime
from geoalchemy2.elements import WKTElement  # type: ignore[import]
from app.database import get_db
from app.models import Incidencia, Config

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
    lat: float  # Obligatorio
    lon: float  # Obligatorio
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


@router.get("/umbrales")
async def obtener_umbrales(db: Annotated[Session, Depends(get_db)]):
    """
    Obtener información de umbrales de gravedad por zona
    Muestra el umbral configurado y la gravedad acumulada por zona
    """
    # Obtener umbral configurado
    config = db.query(Config).filter(Config.clave == "umbral_gravedad").first()
    umbral = int(config.valor) if config else 20
    
    # Calcular suma de gravedad por zona para incidencias validadas
    resultado_oriental = db.query(
        func.coalesce(func.sum(Incidencia.gravedad), 0)
    ).filter(
        Incidencia.zona == "oriental",
        Incidencia.estado == "validada"
    ).scalar()
    
    resultado_occidental = db.query(
        func.coalesce(func.sum(Incidencia.gravedad), 0)
    ).filter(
        Incidencia.zona == "occidental",
        Incidencia.estado == "validada"
    ).scalar()
    
    suma_oriental = int(resultado_oriental) if resultado_oriental else 0
    suma_occidental = int(resultado_occidental) if resultado_occidental else 0
    
    # Contar incidencias validadas por zona
    count_oriental = db.query(Incidencia).filter(
        Incidencia.zona == "oriental",
        Incidencia.estado == "validada"
    ).count()
    
    count_occidental = db.query(Incidencia).filter(
        Incidencia.zona == "occidental",
        Incidencia.estado == "validada"
    ).count()
    
    return {
        "umbral": umbral,
        "oriental": {
            "gravedad_acumulada": suma_oriental,
            "incidencias_validadas": count_oriental,
            "porcentaje": round((suma_oriental / umbral * 100), 2) if umbral > 0 else 0,
            "falta": max(0, umbral - suma_oriental),
            "supera_umbral": suma_oriental > umbral
        },
        "occidental": {
            "gravedad_acumulada": suma_occidental,
            "incidencias_validadas": count_occidental,
            "porcentaje": round((suma_occidental / umbral * 100), 2) if umbral > 0 else 0,
            "falta": max(0, umbral - suma_occidental),
            "supera_umbral": suma_occidental > umbral
        }
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
    # Validar que lat y lon no sean None
    if incidencia.lat is None or incidencia.lon is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Las coordenadas (lat, lon) son obligatorias"
        )
    
    # Crear el objeto de geometría a partir de lat/lon
    geom = WKTElement(f'POINT({incidencia.lon} {incidencia.lat})', srid=4326)
    
    new_incident = Incidencia(
        tipo=incidencia.tipo,
        gravedad=incidencia.gravedad,
        descripcion=incidencia.descripcion,
        foto_url=incidencia.foto_url,
        lat=incidencia.lat,
        lon=incidencia.lon,
        geom=geom,  # Agregar la geometría
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


@router.post("/{incidencia_id}/validate", response_model=IncidenciaResponse)
async def validar_incidencia(
    incidencia_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    """Validar una incidencia (cambiar estado de pendiente a validada)"""
    incidencia = db.query(Incidencia).filter(Incidencia.id == incidencia_id).first()
    if not incidencia:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")
    
    if incidencia.estado != "pendiente":
        raise HTTPException(
            status_code=400, 
            detail=f"No se puede validar una incidencia en estado '{incidencia.estado}'"
        )
    
    incidencia.estado = "validada"
    incidencia.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(incidencia)
    return incidencia
