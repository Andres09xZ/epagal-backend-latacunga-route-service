"""
Router de incidencias para FastAPI
"""
import os
import shutil
import uuid as uuid_lib
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status  # type: ignore[import]
from sqlalchemy.orm import Session  # type: ignore[import]
from sqlalchemy import func  # type: ignore[import]
from typing import Annotated, List, Optional
from datetime import datetime
from geoalchemy2.elements import WKTElement  # type: ignore[import]
from app.database import get_db
from app.models import Incidencia, Config
from app.schemas.incidencias import (
    IncidenciaCreate, 
    IncidenciaResponse, 
    IncidenciaUpdate,
    TipoIncidencia
)
from app.services.incidencia_service import IncidenciaService

router = APIRouter(prefix="/incidencias", tags=["incidencias"])

# Tiempo estimado de respuesta municipal por tipo (en horas)
TIEMPO_ESTIMADO_HORAS = {
    TipoIncidencia.ACOPIO: 24,
    TipoIncidencia.ZONA_CRITICA: 4,
    TipoIncidencia.ANIMAL_MUERTO: 8,
}

# Directorio para almacenar fotos subidas localmente
FOTOS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "fotos_incidencias")


@router.get("/stats")
async def estadisticas(db: Annotated[Session, Depends(get_db)]):
    """Estadísticas de incidencias completas"""
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
    
    # Contar por tipo
    tipos = db.query(Incidencia.tipo).distinct().all()
    por_tipo = {}
    for (tipo_val,) in tipos:
        if tipo_val:
            count = db.query(Incidencia).filter(Incidencia.tipo == tipo_val).count()
            por_tipo[tipo_val] = count

    return {
        "total": total,
        "por_estado": por_estado,
        "por_zona": por_zona,
        "por_tipo": por_tipo,
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


@router.post("/", status_code=status.HTTP_201_CREATED)
async def crear_incidencia(
    incidencia: IncidenciaCreate,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Crear nueva incidencia con autodetección de zona y gravedad.
    - La zona se determina automáticamente según las coordenadas
    - La gravedad se asigna según el tipo de incidencia
    - El estado inicial es 'emitido'
    - Se retorna el número único de reporte y el tiempo estimado de respuesta
    """
    # Validar que lat y lon no sean None
    if incidencia.lat is None or incidencia.lon is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Las coordenadas (lat, lon) son obligatorias"
        )
    
    # Autodetectar zona basándose en coordenadas
    zona = incidencia.determinar_zona()
    
    # Determinar gravedad según tipo de incidencia
    gravedad_map = {
        TipoIncidencia.ACOPIO: 1,
        TipoIncidencia.ZONA_CRITICA: 3,
        TipoIncidencia.ANIMAL_MUERTO: 5
    }
    gravedad = gravedad_map.get(incidencia.tipo, 1)
    
    # Crear el objeto de geometría a partir de lat/lon
    geom = WKTElement(f'POINT({incidencia.lon} {incidencia.lat})', srid=4326)
    
    new_incident = Incidencia(
        tipo=incidencia.tipo.value,
        gravedad=gravedad,
        descripcion=incidencia.descripcion,
        foto_url=incidencia.foto_url,
        lat=incidencia.lat,
        lon=incidencia.lon,
        geom=geom,
        zona=zona,
        usuario_id=incidencia.usuario_id,
        estado="emitido",
        reportado_en=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(new_incident)
    db.commit()
    db.refresh(new_incident)

    tiempo_horas = TIEMPO_ESTIMADO_HORAS.get(incidencia.tipo, 24)

    return {
        "numero_reporte": new_incident.id,
        "estado": new_incident.estado,
        "tipo": new_incident.tipo,
        "gravedad": new_incident.gravedad,
        "zona": new_incident.zona,
        "descripcion": new_incident.descripcion,
        "foto_url": new_incident.foto_url,
        "lat": new_incident.lat,
        "lon": new_incident.lon,
        "usuario_id": new_incident.usuario_id,
        "reportado_en": new_incident.reportado_en,
        "tiempo_estimado_horas": tiempo_horas,
        "mensaje_confirmacion": (
            f"Reporte #{new_incident.id} recibido exitosamente. "
            f"El municipio atenderá su solicitud en aproximadamente {tiempo_horas} horas."
        )
    }


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
    """
    Validar una incidencia (cambiar estado de pendiente a validada)
    
    Si al validar se supera el umbral de gravedad de la zona,
    se genera automáticamente una ruta optimizada.
    """
    # Buscar incidencia
    incidencia = db.query(Incidencia).filter(Incidencia.id == incidencia_id).first()
    if not incidencia:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")
    
    if incidencia.estado not in ("pendiente", "emitido"):
        raise HTTPException(
            status_code=400, 
            detail=f"No se puede validar una incidencia en estado '{incidencia.estado}'"
        )
    
    try:
        # Usar el servicio que incluye la lógica de generación automática
        incidencia_validada, ruta_generada = IncidenciaService.validar_incidencia(
            db, 
            incidencia_id,
            generar_ruta_auto=True
        )
        
        # Log si se generó ruta
        if ruta_generada:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(
                f"✅ Incidencia {incidencia_id} validada. "
                f"Se generó automáticamente ruta ID {ruta_generada.id} para zona {ruta_generada.zona}"
            )
        
        return incidencia_validada
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al validar incidencia: {str(e)}"
        )


@router.post("/foto", status_code=status.HTTP_201_CREATED)
async def subir_foto_incidencia(file: UploadFile = File(...)):
    """
    Subir una foto para adjuntar a una incidencia.
    
    - Acepta imágenes JPEG, PNG o WEBP desde la cámara o galería del móvil.
    - Retorna la URL pública que debe enviarse en el campo `foto_url` al crear la incidencia.
    - Tamaño máximo recomendado: 5 MB.
    """
    TIPOS_PERMITIDOS = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in TIPOS_PERMITIDOS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Tipo de archivo no soportado: '{file.content_type}'. Use JPEG, PNG o WEBP."
        )

    # Leer contenido y verificar tamaño (máx 5 MB)
    contenido = await file.read()
    MAX_BYTES = 5 * 1024 * 1024  # 5 MB
    if len(contenido) > MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="La foto supera el tamaño máximo permitido de 5 MB."
        )

    # Generar nombre único y guardar en disco
    extension = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "jpg"
    nombre_archivo = f"{uuid_lib.uuid4().hex}.{extension}"
    os.makedirs(FOTOS_DIR, exist_ok=True)
    ruta_archivo = os.path.join(FOTOS_DIR, nombre_archivo)

    with open(ruta_archivo, "wb") as f:
        f.write(contenido)

    # Retornar la URL relativa que se almacenará en foto_url
    foto_url = f"/fotos_incidencias/{nombre_archivo}"
    return {
        "foto_url": foto_url,
        "nombre_archivo": nombre_archivo,
        "tamanio_bytes": len(contenido),
        "tipo_contenido": file.content_type,
        "mensaje": "Foto subida correctamente. Use 'foto_url' al registrar la incidencia."
    }
