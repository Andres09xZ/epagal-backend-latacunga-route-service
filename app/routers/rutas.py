"""
Endpoints para gestión de rutas optimizadas
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta, date
from collections import defaultdict

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
    Listar rutas de una zona específica con información de asignaciones
    
    Args:
        zona: 'oriental' o 'occidental'
        estado: Filtrar por estado (planeada, en_ejecucion, completada)
    """
    if zona not in ['oriental', 'occidental']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Zona debe ser 'oriental' u 'occidental'"
        )
    
    from app.models import AsignacionConductor
    from sqlalchemy.orm import joinedload
    
    # Consultar rutas con sus asignaciones
    query = db.query(RutaGenerada).filter(RutaGenerada.zona == zona)
    
    if estado:
        query = query.filter(RutaGenerada.estado == estado)
    
    query = query.options(joinedload(RutaGenerada.asignaciones).joinedload(AsignacionConductor.conductor))
    rutas = query.order_by(RutaGenerada.fecha_generacion.desc()).all()
    
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
                "estado": r.estado,
                "asignaciones": [
                    {
                        "id": a.id,
                        "conductor_id": a.conductor_id,
                        "conductor_nombre": a.conductor.nombre_completo if a.conductor else None,
                        "camion_tipo": a.camion_tipo,
                        "camion_id": a.camion_id,
                        "estado": a.estado,
                        "fecha_inicio": a.fecha_inicio
                    }
                    for a in r.asignaciones
                ] if r.asignaciones else []
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
    
    Estados válidos: planeada, asignada, en_ejecucion, completada
    """
    if nuevo_estado not in ['planeada', 'asignada', 'en_ejecucion', 'completada']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Estado debe ser 'planeada', 'asignada', 'en_ejecucion' o 'completada'"
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


@router.get("/historial/estado")
def obtener_historial_rutas(
    estado: Optional[str] = Query(None, description="Estado: 'planeada', 'asignada', 'en_ejecucion', 'completada', 'pendiente' (planeada+asignada+en_ejecucion), o None para todas"),
    zona: Optional[str] = Query(None, description="Filtrar por zona: 'oriental' u 'occidental'"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Obtener historial de rutas filtrado por estado
    
    Args:
        estado: Estados válidos:
            - 'planeada': Solo rutas planeadas (sin conductor)
            - 'asignada': Conductor asignado pero no ha iniciado
            - 'en_ejecucion': Conductor inició el viaje
            - 'completada': Viaje finalizado
            - 'pendiente': Agrupa planeada, asignada y en_ejecucion
            - None: Todas las rutas
        zona: Filtrar por zona específica (opcional)
        skip: Número de registros a saltar (paginación)
        limit: Número máximo de registros a devolver
    
    Returns:
        Listado de rutas con sus asignaciones y estadísticas
    """
    from app.models import AsignacionConductor, Conductor
    from sqlalchemy.orm import joinedload
    
    # Construir query base
    query = db.query(RutaGenerada).options(
        joinedload(RutaGenerada.asignaciones).joinedload(AsignacionConductor.conductor)
    )
    
    # Aplicar filtros
    if zona:
        if zona not in ['oriental', 'occidental']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Zona debe ser 'oriental' u 'occidental'"
            )
        query = query.filter(RutaGenerada.zona == zona)
    
    if estado:
        estados_validos = ['planeada', 'asignada', 'en_ejecucion', 'completada', 'pendiente']
        if estado not in estados_validos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Estado debe ser uno de: {', '.join(estados_validos)} o None"
            )
        
        if estado == 'pendiente':
            # 'pendiente' agrupa planeada, asignada y en_ejecucion (todas las no completadas)
            query = query.filter(RutaGenerada.estado.in_(['planeada', 'asignada', 'en_ejecucion']))
        else:
            # Estados específicos: planeada, asignada, en_ejecucion, completada
            query = query.filter(RutaGenerada.estado == estado)
    
    # Ordenar por fecha (más recientes primero)
    total = query.count()
    rutas = query.order_by(RutaGenerada.fecha_generacion.desc()).offset(skip).limit(limit).all()
    
    # Formatear respuesta
    resultado = []
    for r in rutas:
        # Calcular incidencias completadas
        incidencias_asignadas = db.query(RutaDetalle).filter(
            RutaDetalle.ruta_id == r.id,
            RutaDetalle.tipo_punto == 'incidencia'
        ).count()
        
        incidencias_completadas = db.query(RutaDetalle).join(
            Incidencia, RutaDetalle.incidencia_id == Incidencia.id
        ).filter(
            RutaDetalle.ruta_id == r.id,
            RutaDetalle.tipo_punto == 'incidencia',
            Incidencia.estado == 'completada'
        ).count()
        
        resultado.append({
            "id": r.id,
            "zona": r.zona,
            "fecha_generacion": r.fecha_generacion.isoformat() if r.fecha_generacion else None,
            "estado": r.estado,
            "suma_gravedad": r.suma_gravedad,
            "camiones_usados": r.camiones_usados,
            "costo_total_km": round(r.costo_total / 1000, 2) if r.costo_total else None,
            "duracion_estimada": str(r.duracion_estimada) if r.duracion_estimada else None,
            "incidencias": {
                "asignadas": incidencias_asignadas,
                "completadas": incidencias_completadas,
                "porcentaje": round((incidencias_completadas / incidencias_asignadas * 100), 1) if incidencias_asignadas > 0 else 0
            },
            "asignaciones": [
                {
                    "id": a.id,
                    "conductor_id": a.conductor_id,
                    "conductor_nombre": a.conductor.nombre_completo if a.conductor else "Sin asignar",
                    "camion_tipo": a.camion_tipo,
                    "camion_id": a.camion_id,
                    "estado": a.estado,
                    "fecha_inicio": a.fecha_inicio.isoformat() if a.fecha_inicio else None,
                    "fecha_finalizacion": a.fecha_finalizacion.isoformat() if a.fecha_finalizacion else None
                }
                for a in (r.asignaciones or [])
            ]
        })
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "filtros": {
            "estado": estado or "todas",
            "zona": zona or "todas"
        },
        "rutas": resultado
    }


@router.get("/calendario/activas")
def obtener_rutas_calendario(
    zona: Optional[str] = Query(None, description="Filtrar por zona: 'oriental' u 'occidental'"),
    estado: Optional[str] = Query(None, description="Filtrar por estado: 'asignada', 'en_ejecucion', 'completada'. Por defecto: todas menos 'planeada'"),
    db: Session = Depends(get_db)
):
    """
    Obtener todas las rutas agrupadas por fecha para mostrar en calendario móvil
    
    Args:
        zona: Filtrar por zona específica (opcional)
        estado: Filtrar por estado específico (opcional, por defecto: asignada, en_ejecucion, completada)
    
    Returns:
        Rutas agrupadas por fecha con información de asignaciones y estado
    """
    from app.models import AsignacionConductor, Conductor
    from sqlalchemy.orm import joinedload
    
    # Construir query
    query = db.query(RutaGenerada).options(
        joinedload(RutaGenerada.asignaciones).joinedload(AsignacionConductor.conductor)
    )
    
    # Filtrar por estado (por defecto excluir solo 'planeada')
    if estado:
        if estado not in ['planeada', 'asignada', 'en_ejecucion', 'completada']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Estado debe ser 'planeada', 'asignada', 'en_ejecucion' o 'completada'"
            )
        query = query.filter(RutaGenerada.estado == estado)
    else:
        # Por defecto mostrar todas menos 'planeada' (sin conductor asignado)
        query = query.filter(RutaGenerada.estado.in_(['asignada', 'en_ejecucion', 'completada']))
    
    # Filtrar por zona si se especifica
    if zona:
        if zona not in ['oriental', 'occidental']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Zona debe ser 'oriental' u 'occidental'"
            )
        query = query.filter(RutaGenerada.zona == zona)
    
    rutas = query.order_by(RutaGenerada.fecha_generacion.desc()).all()
    
    # Agrupar por fecha
    rutas_por_fecha = defaultdict(list)
    
    for r in rutas:
        fecha_str = r.fecha_generacion.date().isoformat() if r.fecha_generacion else None
        
        if fecha_str:
            # Contar incidencias
            incidencias_totales = db.query(RutaDetalle).filter(
                RutaDetalle.ruta_id == r.id,
                RutaDetalle.tipo_punto == 'incidencia'
            ).count()
            
            incidencias_completadas = db.query(RutaDetalle).join(
                Incidencia, RutaDetalle.incidencia_id == Incidencia.id
            ).filter(
                RutaDetalle.ruta_id == r.id,
                RutaDetalle.tipo_punto == 'incidencia',
                Incidencia.estado == 'completada'
            ).count()
            
            rutas_por_fecha[fecha_str].append({
                "id": r.id,
                "zona": r.zona,
                "hora_generacion": r.fecha_generacion.strftime("%H:%M") if r.fecha_generacion else None,
                "estado": r.estado,
                "camiones_usados": r.camiones_usados,
                "incidencias_totales": incidencias_totales,
                "incidencias_completadas": incidencias_completadas,
                "progreso": round((incidencias_completadas / incidencias_totales * 100), 1) if incidencias_totales > 0 else 0,
                "conductores": [
                    {
                        "id": a.conductor_id,
                        "nombre": a.conductor.nombre_completo if a.conductor else "Sin asignar",
                        "camion_tipo": a.camion_tipo,
                        "estado": a.estado
                    }
                    for a in (r.asignaciones or [])
                ]
            })
    
    # Convertir a lista ordenada por fecha (más recientes primero)
    calendario = [
        {
            "fecha": fecha,
            "total_rutas": len(rutas_dia),
            "rutas": rutas_dia
        }
        for fecha, rutas_dia in sorted(rutas_por_fecha.items(), reverse=True)
    ]
    
    # Calcular estadísticas generales
    total_rutas = len(rutas)
    rutas_completadas = sum(1 for r in rutas if r.estado == 'completada')
    rutas_en_ejecucion = sum(1 for r in rutas if r.estado == 'en_ejecucion')
    rutas_asignadas = sum(1 for r in rutas if r.estado == 'asignada')
    
    # Obtener rango de fechas de las rutas
    fechas = [r.fecha_generacion.date() for r in rutas if r.fecha_generacion]
    fecha_min = min(fechas).isoformat() if fechas else None
    fecha_max = max(fechas).isoformat() if fechas else None
    
    return {
        "total_dias": len(rutas_por_fecha),
        "rango_fechas": {
            "fecha_inicio": fecha_min,
            "fecha_fin": fecha_max
        },
        "estadisticas": {
            "total_rutas": total_rutas,
            "asignadas": rutas_asignadas,
            "en_ejecucion": rutas_en_ejecucion,
            "completadas": rutas_completadas,
            "zona_filtrada": zona or "todas",
            "estado_filtrado": estado or "asignada, en_ejecucion, completada"
        },
        "calendario": calendario
    }


@router.get("/{ruta_id}/navegacion")
def obtener_navegacion_ruta(
    ruta_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene la información de navegación de una ruta:
    - Todos los puntos en orden (depósito → incidencias → botadero)
    - Siguiente punto a visitar
    - Puntos completados vs pendientes
    - Instrucciones de navegación
    
    Útil para la app móvil durante la ejecución de la ruta
    """
    from app.models import AsignacionConductor
    
    # Verificar que la ruta existe
    ruta = db.query(RutaGenerada).filter(RutaGenerada.id == ruta_id).first()
    if not ruta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ruta {ruta_id} no encontrada"
        )
    
    # Obtener todos los puntos de la ruta ordenados
    detalles = db.query(RutaDetalle).filter(
        RutaDetalle.ruta_id == ruta_id
    ).order_by(RutaDetalle.orden).all()
    
    if not detalles:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontraron detalles para la ruta {ruta_id}"
        )
    
    # Construir lista de puntos con información completa
    puntos = []
    punto_actual_index = None
    
    for idx, detalle in enumerate(detalles):
        punto = {
            "orden": detalle.orden,
            "tipo_punto": detalle.tipo_punto,
            "lat": detalle.lat,
            "lon": detalle.lon,
            "llegada_estimada": detalle.llegada_estimada.isoformat() if detalle.llegada_estimada else None,
            "tiempo_servicio": str(detalle.tiempo_servicio) if detalle.tiempo_servicio else None,
            "completado": False
        }
        
        # Agregar información específica según el tipo de punto
        if detalle.tipo_punto == 'incidencia' and detalle.incidencia:
            inc = detalle.incidencia
            punto["incidencia"] = {
                "id": inc.id,
                "tipo": inc.tipo,
                "gravedad": inc.gravedad,
                "descripcion": inc.descripcion,
                "estado": inc.estado,
                "foto_url": inc.foto_url
            }
            punto["completado"] = inc.estado == 'completada'
            
            # Si la incidencia no está completada y aún no hemos encontrado el punto actual
            if punto_actual_index is None and inc.estado != 'completada':
                punto_actual_index = idx
        
        elif detalle.tipo_punto == 'deposito':
            punto["nombre"] = "Depósito"
            punto["completado"] = True  # El depósito siempre se marca como visitado al inicio
        
        elif detalle.tipo_punto == 'botadero':
            punto["nombre"] = "Botadero"
            # El botadero se considera completado solo si todas las incidencias están completadas
            todas_incidencias_completadas = all(
                p.get("completado", False) 
                for p in puntos 
                if p.get("tipo_punto") == "incidencia"
            )
            punto["completado"] = todas_incidencias_completadas
        
        puntos.append(punto)
    
    # Si todas las incidencias están completadas, el siguiente punto es el botadero
    if punto_actual_index is None:
        # Buscar el botadero
        for idx, p in enumerate(puntos):
            if p["tipo_punto"] == "botadero":
                punto_actual_index = idx
                break
    
    # Punto actual (siguiente a visitar)
    punto_siguiente = puntos[punto_actual_index] if punto_actual_index is not None else None
    
    # Calcular progreso
    puntos_completados = sum(1 for p in puntos if p["completado"])
    total_puntos = len(puntos)
    progreso_porcentaje = round((puntos_completados / total_puntos * 100), 1) if total_puntos > 0 else 0
    
    # Obtener asignación activa para esta ruta
    asignacion = db.query(AsignacionConductor).filter(
        AsignacionConductor.ruta_id == ruta_id,
        AsignacionConductor.estado.in_(['asignado', 'iniciado'])
    ).first()
    
    conductor_info = None
    if asignacion and asignacion.conductor:
        conductor_info = {
            "id": asignacion.conductor.id,
            "nombre": asignacion.conductor.nombre_completo,
            "telefono": asignacion.conductor.telefono
        }
    
    return {
        "ruta_id": ruta.id,
        "zona": ruta.zona,
        "estado": ruta.estado,
        "conductor": conductor_info,
        "navegacion": {
            "punto_actual": punto_siguiente,
            "punto_actual_index": punto_actual_index,
            "total_puntos": total_puntos,
            "puntos_completados": puntos_completados,
            "progreso_porcentaje": progreso_porcentaje
        },
        "puntos": puntos,
        "resumen": {
            "distancia_total_km": round(ruta.costo_total / 1000, 2) if ruta.costo_total else None,
            "duracion_estimada": str(ruta.duracion_estimada) if ruta.duracion_estimada else None,
            "incidencias_totales": sum(1 for p in puntos if p["tipo_punto"] == "incidencia"),
            "incidencias_completadas": sum(1 for p in puntos if p["tipo_punto"] == "incidencia" and p["completado"])
        }
    }


@router.post("/{ruta_id}/incidencia/{incidencia_id}/completar")
def marcar_incidencia_completada(
    ruta_id: int,
    incidencia_id: int,
    db: Session = Depends(get_db)
):
    """
    Marca una incidencia específica como completada
    
    Args:
        ruta_id: ID de la ruta
        incidencia_id: ID de la incidencia a marcar como completada
    
    Returns:
        Estado actualizado de la incidencia y progreso de la ruta
    """
    # Verificar que la ruta existe
    ruta = db.query(RutaGenerada).filter(RutaGenerada.id == ruta_id).first()
    if not ruta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ruta {ruta_id} no encontrada"
        )
    
    # Verificar que la incidencia existe y pertenece a esta ruta
    detalle_ruta = db.query(RutaDetalle).filter(
        RutaDetalle.ruta_id == ruta_id,
        RutaDetalle.incidencia_id == incidencia_id,
        RutaDetalle.tipo_punto == 'incidencia'
    ).first()
    
    if not detalle_ruta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incidencia {incidencia_id} no encontrada en la ruta {ruta_id}"
        )
    
    # Obtener la incidencia
    incidencia = db.query(Incidencia).filter(Incidencia.id == incidencia_id).first()
    if not incidencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incidencia {incidencia_id} no encontrada"
        )
    
    # Actualizar estado de la incidencia
    estado_anterior = incidencia.estado
    incidencia.estado = 'completada'
    db.commit()
    db.refresh(incidencia)
    
    # Calcular progreso actualizado de la ruta
    incidencias_totales = db.query(RutaDetalle).filter(
        RutaDetalle.ruta_id == ruta_id,
        RutaDetalle.tipo_punto == 'incidencia'
    ).count()
    
    incidencias_completadas = db.query(RutaDetalle).join(
        Incidencia, RutaDetalle.incidencia_id == Incidencia.id
    ).filter(
        RutaDetalle.ruta_id == ruta_id,
        RutaDetalle.tipo_punto == 'incidencia',
        Incidencia.estado == 'completada'
    ).count()
    
    progreso = round((incidencias_completadas / incidencias_totales * 100), 1) if incidencias_totales > 0 else 0
    
    return {
        "message": "Incidencia marcada como completada",
        "incidencia": {
            "id": incidencia.id,
            "tipo": incidencia.tipo,
            "estado_anterior": estado_anterior,
            "estado_actual": incidencia.estado
        },
        "progreso_ruta": {
            "ruta_id": ruta_id,
            "incidencias_totales": incidencias_totales,
            "incidencias_completadas": incidencias_completadas,
            "porcentaje": progreso,
            "todas_completadas": incidencias_completadas == incidencias_totales
        }
    }
