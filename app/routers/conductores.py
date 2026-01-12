"""
Router de Conductores
Endpoints para gestión de conductores y sus asignaciones
Fecha: 2025-12-13
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from app.database import get_db
from app.schemas.conductores import (
    ConductorCreate, ConductorUpdate, ConductorResponse,
    ConductorDisponible, AsignacionCreate, AsignacionResponse,
    RutaConAsignaciones, MisRutasResponse, IniciarRutaRequest,
    FinalizarRutaRequest
)
from app.services.conductor_service import ConductorService, AsignacionService
from app.routers.auth import get_current_user, get_current_admin, get_current_conductor
from app.models import Usuario, Conductor, AsignacionConductor, RutaGenerada


router = APIRouter(prefix="/conductores", tags=["Conductores"])


# ==================== ENDPOINTS DE GESTIÓN (ADMIN) ====================

@router.post("/", response_model=ConductorResponse, summary="Registrar nuevo conductor")
async def crear_conductor(
    data: ConductorCreate,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_current_admin)
):
    """
    Registra un nuevo conductor en el sistema (solo administradores)
    
    Crea automáticamente un usuario asociado con tipo 'conductor'.
    """
    conductor = ConductorService.crear_conductor(db, data)
    
    # Cargar datos de usuario para la respuesta
    db.refresh(conductor)
    conductor_con_usuario = db.query(Conductor).options(
        joinedload(Conductor.usuario)
    ).filter(Conductor.id == conductor.id).first()
    
    return ConductorResponse(
        id=conductor_con_usuario.id,
        usuario_id=conductor_con_usuario.usuario_id,
        nombre_completo=conductor_con_usuario.nombre_completo,
        cedula=conductor_con_usuario.cedula,
        telefono=conductor_con_usuario.telefono,
        licencia_tipo=conductor_con_usuario.licencia_tipo,
        estado=conductor_con_usuario.estado,
        zona_preferida=conductor_con_usuario.zona_preferida,
        fecha_contratacion=conductor_con_usuario.fecha_contratacion,
        created_at=conductor_con_usuario.created_at,
        username=conductor_con_usuario.usuario.username,
        email=conductor_con_usuario.usuario.email
    )


@router.get("/", response_model=List[ConductorResponse], summary="Listar conductores")
async def listar_conductores(
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    zona: Optional[str] = Query(None, description="Filtrar por zona preferida"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lista todos los conductores del sistema
    
    Filtros opcionales:
    - **estado**: disponible, ocupado, inactivo
    - **zona**: oriental, occidental, ambas
    """
    conductores = ConductorService.listar_conductores(
        db, estado=estado, zona=zona, skip=skip, limit=limit
    )
    
    return [
        ConductorResponse(
            id=c.id,
            usuario_id=c.usuario_id,
            nombre_completo=c.nombre_completo,
            cedula=c.cedula,
            telefono=c.telefono,
            licencia_tipo=c.licencia_tipo,
            estado=c.estado,
            zona_preferida=c.zona_preferida,
            fecha_contratacion=c.fecha_contratacion,
            created_at=c.created_at,
            username=c.usuario.username if c.usuario else None,
            email=c.usuario.email if c.usuario else None
        )
        for c in conductores
    ]


@router.get("/disponibles", response_model=List[ConductorDisponible], summary="Conductores disponibles")
async def obtener_conductores_disponibles(
    zona: Optional[str] = Query(None, description="Filtrar por zona"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lista conductores disponibles para asignación
    
    Solo retorna conductores con estado 'disponible'.
    """
    return ConductorService.obtener_conductores_disponibles(db, zona=zona)


@router.get("/{conductor_id}", response_model=ConductorResponse, summary="Obtener conductor")
async def obtener_conductor(
    conductor_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene información detallada de un conductor específico
    """
    conductor = ConductorService.obtener_conductor(db, conductor_id)
    
    return ConductorResponse(
        id=conductor.id,
        usuario_id=conductor.usuario_id,
        nombre_completo=conductor.nombre_completo,
        cedula=conductor.cedula,
        telefono=conductor.telefono,
        licencia_tipo=conductor.licencia_tipo,
        estado=conductor.estado,
        zona_preferida=conductor.zona_preferida,
        fecha_contratacion=conductor.fecha_contratacion,
        created_at=conductor.created_at,
        username=conductor.usuario.username if conductor.usuario else None,
        email=conductor.usuario.email if conductor.usuario else None
    )


@router.patch("/{conductor_id}", response_model=ConductorResponse, summary="Actualizar conductor")
async def actualizar_conductor(
    conductor_id: int,
    data: ConductorUpdate,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_current_admin)
):
    """
    Actualiza información de un conductor (solo administradores)
    
    Campos actualizables:
    - nombre_completo
    - telefono
    - licencia_tipo
    - estado
    - zona_preferida
    """
    conductor = ConductorService.actualizar_conductor(db, conductor_id, data)
    
    return ConductorResponse(
        id=conductor.id,
        usuario_id=conductor.usuario_id,
        nombre_completo=conductor.nombre_completo,
        cedula=conductor.cedula,
        telefono=conductor.telefono,
        licencia_tipo=conductor.licencia_tipo,
        estado=conductor.estado,
        zona_preferida=conductor.zona_preferida,
        fecha_contratacion=conductor.fecha_contratacion,
        created_at=conductor.created_at,
        username=conductor.usuario.username if conductor.usuario else None,
        email=conductor.usuario.email if conductor.usuario else None
    )


# ==================== ENDPOINTS PARA CONDUCTORES ====================

@router.get("/mis-rutas/actual", summary="Obtener mi ruta actual")
async def obtener_mi_ruta_actual(
    conductor: Conductor = Depends(get_current_conductor),
    db: Session = Depends(get_db)
):
    """
    Obtiene la ruta actualmente en ejecución del conductor autenticado
    """
    asignacion = db.query(AsignacionConductor).options(
        joinedload(AsignacionConductor.ruta)
    ).filter(
        AsignacionConductor.conductor_id == conductor.id,
        AsignacionConductor.estado == 'iniciado'
    ).first()
    
    if not asignacion:
        return {
            "message": "No tienes una ruta en ejecución actualmente",
            "ruta_actual": None
        }
    
    return {
        "message": "Ruta en ejecución",
        "ruta_actual": {
            "asignacion_id": asignacion.id,
            "ruta_id": asignacion.ruta_id,
            "zona": asignacion.ruta.zona,
            "camion_tipo": asignacion.camion_tipo,
            "camion_id": asignacion.camion_id,
            "fecha_inicio": asignacion.fecha_inicio,
            "suma_gravedad": asignacion.ruta.suma_gravedad
        }
    }


@router.get("/mis-rutas/todas", response_model=MisRutasResponse, summary="Obtener todas mis rutas")
async def obtener_mis_rutas(
    estado: Optional[str] = Query(None, description="Filtrar por estado de asignación"),
    conductor: Conductor = Depends(get_current_conductor),
    db: Session = Depends(get_db)
):
    """
    Lista todas las rutas asignadas al conductor autenticado
    
    Incluye estadísticas por estado de asignación.
    """
    asignaciones = AsignacionService.obtener_asignaciones_conductor(
        db, conductor.id, estado=estado
    )
    
    # Contar por estado
    asignado = sum(1 for a in asignaciones if a.estado == 'asignado')
    iniciado = sum(1 for a in asignaciones if a.estado == 'iniciado')
    completado = sum(1 for a in asignaciones if a.estado == 'completado')
    
    # Construir respuesta con rutas únicas
    rutas_dict = {}
    for asig in asignaciones:
        ruta_id = asig.ruta_id
        if ruta_id not in rutas_dict:
            rutas_dict[ruta_id] = {
                "ruta": asig.ruta,
                "asignaciones": []
            }
        
        rutas_dict[ruta_id]["asignaciones"].append(asig)
    
    rutas_response = []
    for ruta_id, data in rutas_dict.items():
        ruta = data["ruta"]
        asigs = data["asignaciones"]
        
        rutas_response.append(RutaConAsignaciones(
            id=ruta.id,
            zona=ruta.zona,
            estado=ruta.estado,
            suma_gravedad=ruta.suma_gravedad,
            camiones_usados=ruta.camiones_usados,
            fecha_generacion=ruta.fecha_generacion,
            asignaciones=[
                AsignacionResponse(
                    id=a.id,
                    ruta_id=a.ruta_id,
                    conductor_id=a.conductor_id,
                    camion_tipo=a.camion_tipo,
                    camion_id=a.camion_id,
                    fecha_asignacion=a.fecha_asignacion,
                    fecha_inicio=a.fecha_inicio,
                    fecha_finalizacion=a.fecha_finalizacion,
                    estado=a.estado,
                    conductor_nombre=conductor.nombre_completo,
                    conductor_cedula=conductor.cedula,
                    conductor_telefono=conductor.telefono
                )
                for a in asigs
            ]
        ))
    
    return MisRutasResponse(
        total=len(asignaciones),
        asignado=asignado,
        iniciado=iniciado,
        completado=completado,
        rutas=rutas_response
    )


@router.post("/iniciar-ruta", summary="Iniciar mi ruta")
async def iniciar_mi_ruta(
    request: IniciarRutaRequest,
    conductor: Conductor = Depends(get_current_conductor),
    db: Session = Depends(get_db)
):
    """
    Inicia una ruta asignada al conductor autenticado
    
    Cambia el estado a 'iniciado' y actualiza el estado del conductor a 'ocupado'.
    """
    # Buscar asignación del conductor para esta ruta
    asignacion = db.query(AsignacionConductor).filter(
        AsignacionConductor.ruta_id == request.ruta_id,
        AsignacionConductor.conductor_id == conductor.id,
        AsignacionConductor.estado == 'asignado'
    ).first()
    
    if not asignacion:
        raise HTTPException(
            status_code=404,
            detail="No tienes una asignación pendiente para esta ruta"
        )
    
    asignacion_actualizada = AsignacionService.iniciar_ruta(db, asignacion.id)
    
    return {
        "message": "Ruta iniciada exitosamente",
        "asignacion_id": asignacion_actualizada.id,
        "ruta_id": asignacion_actualizada.ruta_id,
        "fecha_inicio": asignacion_actualizada.fecha_inicio,
        "estado": asignacion_actualizada.estado
    }


@router.post("/finalizar-ruta", summary="Finalizar mi ruta")
async def finalizar_mi_ruta(
    request: FinalizarRutaRequest,
    conductor: Conductor = Depends(get_current_conductor),
    db: Session = Depends(get_db)
):
    """
    Finaliza una ruta en ejecución del conductor autenticado
    
    Cambia el estado a 'completado' y actualiza el estado del conductor a 'disponible'.
    """
    # Buscar asignación del conductor para esta ruta
    asignacion = db.query(AsignacionConductor).filter(
        AsignacionConductor.ruta_id == request.ruta_id,
        AsignacionConductor.conductor_id == conductor.id,
        AsignacionConductor.estado == 'iniciado'
    ).first()
    
    if not asignacion:
        raise HTTPException(
            status_code=404,
            detail="No tienes una ruta en ejecución para finalizar"
        )
    
    asignacion_actualizada = AsignacionService.finalizar_ruta(db, asignacion.id)
    
    # Agregar notas si se proporcionaron
    if request.notas:
        ruta = db.query(RutaGenerada).filter(
            RutaGenerada.id == request.ruta_id
        ).first()
        if ruta:
            notas_actuales = ruta.notas or ""
            ruta.notas = f"{notas_actuales}\n[{conductor.nombre_completo}]: {request.notas}".strip()
            db.commit()
    
    return {
        "message": "Ruta finalizada exitosamente",
        "asignacion_id": asignacion_actualizada.id,
        "ruta_id": asignacion_actualizada.ruta_id,
        "fecha_finalizacion": asignacion_actualizada.fecha_finalizacion,
        "estado": asignacion_actualizada.estado
    }


# ==================== ENDPOINTS DE ASIGNACIONES (ADMIN) ====================

@router.get("/asignaciones/", response_model=List[AsignacionResponse], summary="Listar todas las asignaciones")
async def listar_asignaciones(
    estado: Optional[str] = None,
    zona: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_current_admin)
):
    """
    Lista todas las asignaciones de conductores a rutas (solo administradores)
    
    Puede filtrar por estado de asignación y zona de ruta.
    """
    query = db.query(AsignacionConductor).options(
        joinedload(AsignacionConductor.conductor),
        joinedload(AsignacionConductor.ruta)
    )
    
    if estado:
        query = query.filter(AsignacionConductor.estado == estado)
    
    if zona:
        query = query.join(RutaGenerada).filter(RutaGenerada.zona == zona)
    
    asignaciones = query.order_by(AsignacionConductor.fecha_inicio.desc()).all()
    
    return asignaciones


@router.post("/asignaciones/", response_model=AsignacionResponse, summary="Asignar conductor a ruta")
async def crear_asignacion(
    data: AsignacionCreate,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_current_admin)
):
    """
    Asigna un conductor a una ruta específica (solo administradores)
    
    El conductor debe estar disponible y la ruta debe existir.
    """
    asignacion = AsignacionService.asignar_conductor(db, data)
    
    # Cargar datos del conductor
    db.refresh(asignacion)
    asignacion_con_conductor = db.query(AsignacionConductor).options(
        joinedload(AsignacionConductor.conductor)
    ).filter(AsignacionConductor.id == asignacion.id).first()
    
    conductor = asignacion_con_conductor.conductor
    
    return AsignacionResponse(
        id=asignacion_con_conductor.id,
        ruta_id=asignacion_con_conductor.ruta_id,
        conductor_id=asignacion_con_conductor.conductor_id,
        camion_tipo=asignacion_con_conductor.camion_tipo,
        camion_id=asignacion_con_conductor.camion_id,
        fecha_asignacion=asignacion_con_conductor.fecha_asignacion,
        fecha_inicio=asignacion_con_conductor.fecha_inicio,
        fecha_finalizacion=asignacion_con_conductor.fecha_finalizacion,
        estado=asignacion_con_conductor.estado,
        conductor_nombre=conductor.nombre_completo if conductor else None,
        conductor_cedula=conductor.cedula if conductor else None,
        conductor_telefono=conductor.telefono if conductor else None
    )


@router.get("/asignaciones/ruta/{ruta_id}", response_model=List[AsignacionResponse], summary="Asignaciones de una ruta")
async def obtener_asignaciones_ruta(
    ruta_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene todas las asignaciones de conductores para una ruta específica
    """
    asignaciones = AsignacionService.obtener_asignaciones_ruta(db, ruta_id)
    
    return [
        AsignacionResponse(
            id=a.id,
            ruta_id=a.ruta_id,
            conductor_id=a.conductor_id,
            camion_tipo=a.camion_tipo,
            camion_id=a.camion_id,
            fecha_asignacion=a.fecha_asignacion,
            fecha_inicio=a.fecha_inicio,
            fecha_finalizacion=a.fecha_finalizacion,
            estado=a.estado,
            conductor_nombre=a.conductor.nombre_completo if a.conductor else None,
            conductor_cedula=a.conductor.cedula if a.conductor else None,
            conductor_telefono=a.conductor.telefono if a.conductor else None
        )
        for a in asignaciones
    ]


@router.get("/asignaciones/conductor/{conductor_id}", response_model=List[AsignacionResponse], summary="Asignaciones de un conductor")
async def obtener_asignaciones_conductor(
    conductor_id: int,
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene todas las asignaciones de un conductor específico
    """
    asignaciones = AsignacionService.obtener_asignaciones_conductor(
        db, conductor_id, estado=estado
    )
    
    conductor = ConductorService.obtener_conductor(db, conductor_id)
    
    return [
        AsignacionResponse(
            id=a.id,
            ruta_id=a.ruta_id,
            conductor_id=a.conductor_id,
            camion_tipo=a.camion_tipo,
            camion_id=a.camion_id,
            fecha_asignacion=a.fecha_asignacion,
            fecha_inicio=a.fecha_inicio,
            fecha_finalizacion=a.fecha_finalizacion,
            estado=a.estado,
            conductor_nombre=conductor.nombre_completo,
            conductor_cedula=conductor.cedula,
            conductor_telefono=conductor.telefono
        )
        for a in asignaciones
    ]


# ==================== NUEVOS ENDPOINTS ====================

@router.get("/{conductor_id}/rutas/activas", summary="Rutas activas de un conductor")
async def obtener_rutas_activas_conductor(
    conductor_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene todas las rutas activas (asignada, en_ejecucion) de un conductor específico
    con información detallada de incidencias y progreso
    """
    from app.models import RutaDetalle, Incidencia
    
    # Verificar que el conductor existe
    conductor = db.query(Conductor).filter(Conductor.id == conductor_id).first()
    if not conductor:
        raise HTTPException(status_code=404, detail=f"Conductor {conductor_id} no encontrado")
    
    # Buscar asignaciones activas del conductor
    asignaciones = db.query(AsignacionConductor).options(
        joinedload(AsignacionConductor.ruta)
    ).filter(
        AsignacionConductor.conductor_id == conductor_id,
        AsignacionConductor.estado.in_(['asignado', 'iniciado'])
    ).all()
    
    rutas_activas = []
    
    for asignacion in asignaciones:
        ruta = asignacion.ruta
        
        # Contar incidencias de la ruta
        incidencias_totales = db.query(RutaDetalle).filter(
            RutaDetalle.ruta_id == ruta.id,
            RutaDetalle.tipo_punto == 'incidencia'
        ).count()
        
        incidencias_completadas = db.query(RutaDetalle).join(
            Incidencia, RutaDetalle.incidencia_id == Incidencia.id
        ).filter(
            RutaDetalle.ruta_id == ruta.id,
            RutaDetalle.tipo_punto == 'incidencia',
            Incidencia.estado == 'completada'
        ).count()
        
        # Obtener detalles de la ruta (puntos)
        detalles = db.query(RutaDetalle).filter(
            RutaDetalle.ruta_id == ruta.id
        ).order_by(RutaDetalle.orden).all()
        
        puntos = []
        for d in detalles:
            punto = {
                "orden": d.orden,
                "tipo_punto": d.tipo_punto,
                "lat": d.lat,
                "lon": d.lon,
                "distancia_desde_anterior_m": d.distancia_desde_anterior,
                "tiempo_desde_anterior_seg": d.tiempo_desde_anterior
            }
            
            if d.tipo_punto == 'incidencia' and d.incidencia:
                punto["incidencia"] = {
                    "id": d.incidencia.id,
                    "tipo": d.incidencia.tipo,
                    "gravedad": d.incidencia.gravedad,
                    "descripcion": d.incidencia.descripcion,
                    "estado": d.incidencia.estado,
                    "foto_url": d.incidencia.foto_url
                }
            
            puntos.append(punto)
        
        rutas_activas.append({
            "ruta_id": ruta.id,
            "zona": ruta.zona,
            "estado_ruta": ruta.estado,
            "fecha_generacion": ruta.fecha_generacion.isoformat() if ruta.fecha_generacion else None,
            "duracion_estimada": str(ruta.duracion_estimada) if ruta.duracion_estimada else None,
            "costo_total_km": round(ruta.costo_total / 1000, 2) if ruta.costo_total else None,
            "asignacion": {
                "id": asignacion.id,
                "estado": asignacion.estado,
                "camion_tipo": asignacion.camion_tipo,
                "camion_id": asignacion.camion_id,
                "fecha_asignacion": asignacion.fecha_asignacion.isoformat() if asignacion.fecha_asignacion else None,
                "fecha_inicio": asignacion.fecha_inicio.isoformat() if asignacion.fecha_inicio else None
            },
            "progreso": {
                "incidencias_totales": incidencias_totales,
                "incidencias_completadas": incidencias_completadas,
                "porcentaje": round((incidencias_completadas / incidencias_totales * 100), 1) if incidencias_totales > 0 else 0
            },
            "puntos": puntos
        })
    
    return {
        "conductor": {
            "id": conductor.id,
            "nombre_completo": conductor.nombre_completo,
            "cedula": conductor.cedula,
            "estado": conductor.estado
        },
        "total_rutas_activas": len(rutas_activas),
        "rutas": rutas_activas
    }


@router.get("/me/estadisticas", summary="Mis estadísticas como conductor")
async def obtener_mis_estadisticas(
    conductor: Conductor = Depends(get_current_conductor),
    db: Session = Depends(get_db)
):
    """
    Obtiene estadísticas personales del conductor autenticado:
    - Total de rutas completadas
    - Incidencias atendidas
    - Tiempo promedio de ruta
    - Rendimiento por zona
    """
    from sqlalchemy import func
    from datetime import timedelta
    
    # Total de asignaciones completadas
    total_completadas = db.query(AsignacionConductor).filter(
        AsignacionConductor.conductor_id == conductor.id,
        AsignacionConductor.estado == 'completado'
    ).count()
    
    # Total de asignaciones activas
    total_activas = db.query(AsignacionConductor).filter(
        AsignacionConductor.conductor_id == conductor.id,
        AsignacionConductor.estado.in_(['asignado', 'iniciado'])
    ).count()
    
    # Calcular tiempo promedio de ruta
    asignaciones_con_tiempo = db.query(AsignacionConductor).filter(
        AsignacionConductor.conductor_id == conductor.id,
        AsignacionConductor.estado == 'completado',
        AsignacionConductor.fecha_inicio.isnot(None),
        AsignacionConductor.fecha_finalizacion.isnot(None)
    ).all()
    
    tiempos = []
    for a in asignaciones_con_tiempo:
        duracion = a.fecha_finalizacion - a.fecha_inicio
        tiempos.append(duracion.total_seconds())
    
    tiempo_promedio_seg = sum(tiempos) / len(tiempos) if tiempos else 0
    tiempo_promedio = str(timedelta(seconds=int(tiempo_promedio_seg)))
    
    # Contar incidencias atendidas
    from app.models import RutaDetalle, Incidencia
    
    incidencias_atendidas = db.query(func.count(RutaDetalle.id)).join(
        AsignacionConductor, RutaDetalle.ruta_id == AsignacionConductor.ruta_id
    ).join(
        Incidencia, RutaDetalle.incidencia_id == Incidencia.id
    ).filter(
        AsignacionConductor.conductor_id == conductor.id,
        AsignacionConductor.estado == 'completado',
        RutaDetalle.tipo_punto == 'incidencia',
        Incidencia.estado == 'completada'
    ).scalar()
    
    # Rendimiento por zona
    from sqlalchemy import case
    
    rutas_por_zona = db.query(
        RutaGenerada.zona,
        func.count(AsignacionConductor.id).label('total')
    ).join(
        AsignacionConductor, RutaGenerada.id == AsignacionConductor.ruta_id
    ).filter(
        AsignacionConductor.conductor_id == conductor.id,
        AsignacionConductor.estado == 'completado'
    ).group_by(RutaGenerada.zona).all()
    
    zonas = {zona: total for zona, total in rutas_por_zona}
    
    # Última ruta completada
    ultima_asignacion = db.query(AsignacionConductor).options(
        joinedload(AsignacionConductor.ruta)
    ).filter(
        AsignacionConductor.conductor_id == conductor.id,
        AsignacionConductor.estado == 'completado'
    ).order_by(AsignacionConductor.fecha_finalizacion.desc()).first()
    
    ultima_ruta = None
    if ultima_asignacion:
        ultima_ruta = {
            "ruta_id": ultima_asignacion.ruta_id,
            "zona": ultima_asignacion.ruta.zona,
            "fecha_finalizacion": ultima_asignacion.fecha_finalizacion.isoformat() if ultima_asignacion.fecha_finalizacion else None
        }
    
    return {
        "conductor": {
            "id": conductor.id,
            "nombre_completo": conductor.nombre_completo,
            "estado": conductor.estado
        },
        "estadisticas": {
            "rutas_completadas": total_completadas,
            "rutas_activas": total_activas,
            "incidencias_atendidas": incidencias_atendidas or 0,
            "tiempo_promedio_ruta": tiempo_promedio,
            "rendimiento_por_zona": {
                "oriental": zonas.get('oriental', 0),
                "occidental": zonas.get('occidental', 0)
            },
            "ultima_ruta_completada": ultima_ruta
        }
    }
