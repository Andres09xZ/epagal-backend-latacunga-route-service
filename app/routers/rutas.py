"""
Endpoints para gestión de rutas optimizadas
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models import RutaGenerada, RutaDetalle, Incidencia
from app.services.ruta_service import RutaService
from app.osrm_service import OSRMService

router = APIRouter(
    prefix="/rutas",
    tags=["Rutas"]
)


@router.post("/generar/{zona}", status_code=status.HTTP_201_CREATED)
def generar_ruta_manual(
    zona: str,
    db: Session = Depends(get_db)
):
    """
    Generar manualmente una ruta para una zona específica
    
    Args:
        zona: 'oriental' o 'occidental'
    
    Returns:
        Información de la ruta generada
    """
    if zona not in ['oriental', 'occidental']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Zona debe ser 'oriental' u 'occidental'"
        )
    
    try:
        ruta_service = RutaService()
        ruta = ruta_service.generar_ruta_automatica(db, zona)
        
        if not ruta:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No se pudo generar ruta para zona {zona}. Verifique que haya incidencias pendientes."
            )
        
        return {
            "id": ruta.id,
            "zona": ruta.zona,
            "fecha_generacion": ruta.fecha_generacion,
            "suma_gravedad": ruta.suma_gravedad,
            "camiones_usados": ruta.camiones_usados,
            "costo_total_metros": ruta.costo_total,
            "duracion_estimada": str(ruta.duracion_estimada),
            "estado": ruta.estado,
            "notas": ruta.notas
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar ruta: {str(e)}"
        )


@router.get("/{ruta_id}")
def obtener_ruta(
    ruta_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtener ruta con puntos para navegación
    Incluye información detallada de cada punto con sus incidencias asociadas
    """
    ruta = db.query(RutaGenerada).filter(RutaGenerada.id == ruta_id).first()
    
    if not ruta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ruta {ruta_id} no encontrada"
        )
    
    # Obtener detalles de la ruta con incidencias
    detalles = db.query(RutaDetalle).filter(
        RutaDetalle.ruta_id == ruta_id
    ).order_by(RutaDetalle.orden).all()
    
    # Construir lista de puntos con información de incidencias
    puntos = []
    for detalle in detalles:
        punto = {
            "id": detalle.id,
            "secuencia": detalle.orden,
            "tipo_punto": detalle.tipo_punto,
            "lat": detalle.lat,
            "lon": detalle.lon,
            "tipo_camion": detalle.camion_tipo,
            "camion_id": detalle.camion_id,
            "llegada_estimada": detalle.llegada_estimada,
            "tiempo_servicio": str(detalle.tiempo_servicio) if detalle.tiempo_servicio else None,
            "carga_acumulada": detalle.carga_acumulada
        }
        
        # Si es una incidencia, agregar información adicional
        if detalle.tipo_punto == "incidencia" and detalle.incidencia_id:
            incidencia = db.query(Incidencia).filter(
                Incidencia.id == detalle.incidencia_id
            ).first()
            if incidencia:
                punto["incidencia_id"] = incidencia.id
                punto["tipo_incidencia"] = incidencia.tipo
                punto["gravedad"] = incidencia.gravedad
                punto["descripcion"] = incidencia.descripcion
                punto["foto_url"] = incidencia.foto_url
                punto["estado_incidencia"] = incidencia.estado
        
        puntos.append(punto)
    
    # Generar polyline desde OSRM
    polyline = ""
    if len(puntos) >= 2:
        try:
            # Extraer coordenadas (lon, lat) de los puntos
            coordinates = [(p["lon"], p["lat"]) for p in puntos if p["lat"] and p["lon"]]
            
            if len(coordinates) >= 2:
                osrm = OSRMService()
                route_data = osrm.calculate_route(
                    coordinates=coordinates,
                    overview="full",
                    geometries="polyline"  # Usar formato polyline de Google
                )
                
                if route_data and route_data.get("geometry"):
                    polyline = route_data["geometry"]
        except Exception as e:
            # Si falla, seguir con polyline vacío
            pass
    
    return {
        "id": ruta.id,
        "zona": ruta.zona,
        "estado": ruta.estado,
        "suma_gravedad": ruta.suma_gravedad,
        "camiones_usados": ruta.camiones_usados,
        "duracion_estimada": str(ruta.duracion_estimada),
        "costo_total_metros": ruta.costo_total,
        "fecha_generacion": ruta.fecha_generacion,
        "puntos": puntos,
        "polyline": polyline
    }


@router.get("/{ruta_id}/detalles")
def obtener_detalles_ruta(
    ruta_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtener detalles completos de una ruta con incidencias
    Estructura: {ruta, incidencias, puntos}
    """
    ruta = db.query(RutaGenerada).filter(RutaGenerada.id == ruta_id).first()
    
    if not ruta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ruta {ruta_id} no encontrada"
        )
    
    # Obtener detalles de la ruta
    detalles = db.query(RutaDetalle).filter(
        RutaDetalle.ruta_id == ruta_id
    ).order_by(RutaDetalle.orden).all()
    
    # Extraer IDs de incidencias únicas
    incidencia_ids = [d.incidencia_id for d in detalles if d.incidencia_id]
    
    # Obtener información completa de incidencias
    incidencias = []
    if incidencia_ids:
        incidencias_db = db.query(Incidencia).filter(
            Incidencia.id.in_(incidencia_ids)
        ).all()
        
        incidencias = [
            {
                "id": inc.id,
                "tipo": inc.tipo,
                "gravedad": inc.gravedad,
                "lat": inc.lat,
                "lon": inc.lon,
                "descripcion": inc.descripcion,
                "foto_url": inc.foto_url,
                "estado": inc.estado,
                "reportado_en": inc.reportado_en
            }
            for inc in incidencias_db
        ]
    
    # Construir lista de puntos
    puntos = [
        {
            "id": d.id,
            "orden": d.orden,
            "camion_tipo": d.camion_tipo,
            "camion_id": d.camion_id,
            "tipo_punto": d.tipo_punto,
            "incidencia_id": d.incidencia_id,
            "lat": d.lat,
            "lon": d.lon,
            "llegada_estimada": d.llegada_estimada,
            "tiempo_servicio": str(d.tiempo_servicio) if d.tiempo_servicio else None,
            "carga_acumulada": d.carga_acumulada
        }
        for d in detalles
    ]
    
    return {
        "ruta": {
            "id": ruta.id,
            "zona": ruta.zona,
            "estado": ruta.estado,
            "suma_gravedad": ruta.suma_gravedad,
            "camiones_usados": ruta.camiones_usados,
            "duracion_estimada": str(ruta.duracion_estimada),
            "costo_total_metros": ruta.costo_total,
            "fecha_generacion": ruta.fecha_generacion
        },
        "incidencias": incidencias,
        "puntos": puntos
    }


@router.get("/zona/{zona}")
def listar_rutas_por_zona(
    zona: str,
    estado: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Listar rutas de una zona específica
    
    Args:
        zona: 'oriental' o 'occidental'
        estado: Filtrar por estado (planeada, en_ejecucion, completada)
    """
    if zona not in ['oriental', 'occidental']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Zona debe ser 'oriental' u 'occidental'"
        )
    
    rutas = RutaService.obtener_rutas_por_zona(db, zona, estado)
    
    return {
        "zona": zona,
        "total": len(rutas),
        "rutas": [
            {
                "id": r.id,
                "fecha_generacion": r.fecha_generacion,
                "suma_gravedad": r.suma_gravedad,
                "camiones_usados": r.camiones_usados,
                "costo_total_metros": r.costo_total,
                "duracion_estimada": str(r.duracion_estimada),
                "estado": r.estado
            }
            for r in rutas[skip:skip+limit]
        ]
    }


@router.patch("/{ruta_id}/estado")
def actualizar_estado_ruta(
    ruta_id: int,
    nuevo_estado: str,
    db: Session = Depends(get_db)
):
    """
    Actualizar el estado de una ruta
    
    Estados válidos: planeada, en_ejecucion, completada
    """
    if nuevo_estado not in ['planeada', 'en_ejecucion', 'completada']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Estado debe ser 'planeada', 'en_ejecucion' o 'completada'"
        )
    
    ruta = db.query(RutaGenerada).filter(RutaGenerada.id == ruta_id).first()
    
    if not ruta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ruta {ruta_id} no encontrada"
        )
    
    ruta.estado = nuevo_estado
    db.commit()
    db.refresh(ruta)
    
    return {
        "id": ruta.id,
        "zona": ruta.zona,
        "estado": ruta.estado,
        "actualizado_en": ruta.updated_at
    }
