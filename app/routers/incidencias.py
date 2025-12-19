"""
Endpoints para gestión de incidencias ciudadanas
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models import Incidencia, Config, RutaGenerada
from app.schemas.incidencias import (
    IncidenciaCreate, 
    IncidenciaResponse, 
    IncidenciaUpdate,
    IncidenciaStats,
    EstadoIncidencia,
    ZonaIncidencia
)
from app.services.incidencia_service import IncidenciaService

router = APIRouter(
    prefix="/incidencias",
    tags=["Incidencias"]
)


@router.post("/", response_model=IncidenciaResponse, status_code=status.HTTP_201_CREATED)
def crear_incidencia(
    incidencia: IncidenciaCreate,
    auto_generar_ruta: bool = Query(False, description="Si True, genera ruta automáticamente al superar umbral (usar False para flujo con validación admin)"),
    db: Session = Depends(get_db)
):
    """
    Crear una nueva incidencia
    
    Reglas automáticas:
    - Asigna gravedad según tipo (acopio=1, zona_critica=3, animal_muerto=5)
    - Clasifica zona automáticamente (oriental/occidental)
    - Calcula ventana de atención según tipo
    - Convierte coordenadas a UTM
    - **Estado inicial: PENDIENTE** (requiere validación del admin)
    - La ruta se genera cuando el admin valida la incidencia (POST /api/incidencias/{id}/validate)
    
    Args:
        auto_generar_ruta: Si True, genera ruta automática (legacy). Por defecto False para flujo con validación
    
    Returns:
        Incidencia creada en estado PENDIENTE
    """
    try:
        nueva_incidencia, ruta_generada = IncidenciaService.crear_incidencia(
            db, 
            incidencia,
            generar_ruta_auto=auto_generar_ruta
        )
        
        # Si se generó ruta, agregar información en la respuesta
        if ruta_generada:
            # Se puede agregar a headers o a un campo extra
            # Por ahora solo retornamos la incidencia
            # El cliente puede verificar si el estado cambió a 'asignada'
            pass
        
        return nueva_incidencia
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al crear incidencia: {str(e)}"
        )


@router.get("/", response_model=List[IncidenciaResponse])
def listar_incidencias(
    estado: Optional[EstadoIncidencia] = None,
    zona: Optional[ZonaIncidencia] = None,
    tipo: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Listar incidencias con filtros opcionales
    """
    query = db.query(Incidencia)
    
    if estado:
        query = query.filter(Incidencia.estado == estado.value)
    if zona:
        query = query.filter(Incidencia.zona == zona.value)
    if tipo:
        query = query.filter(Incidencia.tipo == tipo)
    
    incidencias = query.order_by(Incidencia.reportado_en.desc()).offset(skip).limit(limit).all()
    return incidencias


@router.get("/stats", response_model=IncidenciaStats)
def obtener_estadisticas(db: Session = Depends(get_db)):
    """
    Obtener estadísticas generales de incidencias
    """
    stats = IncidenciaService.obtener_estadisticas(db)
    return stats


@router.get("/zona/{zona}/umbral")
def verificar_umbral_zona(
    zona: ZonaIncidencia,
    db: Session = Depends(get_db)
):
    """
    Verificar si una zona alcanzó el umbral para generar ruta
    
    Returns:
        - debe_generar_ruta: bool
        - suma_gravedad: int
        - umbral_configurado: int
    """
    debe_generar, suma = IncidenciaService.verificar_umbral_ruta(db, zona.value)
    
    config = db.query(Config).filter(Config.clave == 'umbral_gravedad').first()
    umbral = int(config.valor) if config else 20
    
    return {
        "zona": zona.value,
        "suma_gravedad": suma,
        "umbral_configurado": umbral,
        "debe_generar_ruta": debe_generar,
        # Ahora se muestran incidencias VALIDADAS (las que cuentan para rutas)
        "incidencias_validadas": db.query(Incidencia).filter(
            Incidencia.zona == zona.value,
            Incidencia.estado == 'validada'
        ).count()
    }



@router.post("/{incidencia_id}/validate")
def validar_incidencia(
    incidencia_id: int,
    generar_ruta_auto: bool = Query(True, description="Si True, tras validar verifica umbral y genera ruta automáticamente si corresponde"),
    db: Session = Depends(get_db)
):
    """
    Validar una incidencia como administrador. Solo incidencias validadas pueden
    ser consideradas para generación de rutas.
    """
    try:
        incidencia, ruta_generada = IncidenciaService.validar_incidencia(db, incidencia_id, generar_ruta_auto=generar_ruta_auto)

        response = {"incidencia_id": incidencia.id, "estado": incidencia.estado}
        if ruta_generada:
            response["ruta_generada_id"] = ruta_generada.id

        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{incidencia_id}", response_model=IncidenciaResponse)
def obtener_incidencia(
    incidencia_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtener una incidencia por ID
    """
    incidencia = db.query(Incidencia).filter(Incidencia.id == incidencia_id).first()
    
    if not incidencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incidencia {incidencia_id} no encontrada"
        )
    
    return incidencia


@router.patch("/{incidencia_id}", response_model=IncidenciaResponse)
def actualizar_incidencia(
    incidencia_id: int,
    incidencia_update: IncidenciaUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualizar una incidencia existente
    """
    incidencia = db.query(Incidencia).filter(Incidencia.id == incidencia_id).first()
    
    if not incidencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incidencia {incidencia_id} no encontrada"
        )
    
    # Actualizar campos
    update_data = incidencia_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(incidencia, key):
            setattr(incidencia, key, value.value if hasattr(value, 'value') else value)
    
    db.commit()
    db.refresh(incidencia)
    
    return incidencia


@router.delete("/{incidencia_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_incidencia(
    incidencia_id: int,
    db: Session = Depends(get_db)
):
    """
    Eliminar (soft delete) una incidencia
    """
    incidencia = db.query(Incidencia).filter(Incidencia.id == incidencia_id).first()
    
    if not incidencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incidencia {incidencia_id} no encontrada"
        )
    
    # Cancelar en lugar de eliminar
    incidencia.estado = 'cancelada'
    db.commit()
    
    return None
