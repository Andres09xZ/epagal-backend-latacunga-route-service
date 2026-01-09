# app/routers/geofencing.py
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date

from app.database import get_db
from app.schemas.geofencing import (
    PosicionGPS,
    ResultadoValidacionGPS,
    GeofenceAlertResponse,
    GeofenceAlertUpdate,
    GeofenceConfigResponse,
    GeofenceConfigUpdate,
    EstadisticasGeofencing,
    ReporteSeguridadMensual,
    AlertaWebSocket
)
from app.models.geofencing import (
    GeofenceAlert,
    GeofenceConfig,
    EstadisticaGeofencing,
    TipoAlerta,
    SeveridadAlerta,
    EstadoAlerta
)
from app.models import Conductor
from app.services.geofencing_service import GeofencingService


router = APIRouter(prefix="/api/geofencing", tags=["geofencing"])


# ===================================================================
# WebSocket Manager para notificaciones en tiempo real
# ===================================================================

class ConnectionManager:
    """Gestor de conexiones WebSocket para notificaciones en tiempo real"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        """Enviar mensaje a todos los clientes conectados"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        
        # Limpiar conexiones muertas
        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()


# ===================================================================
# WebSocket Endpoint
# ===================================================================

@router.websocket("/ws/alertas")
async def websocket_alertas(websocket: WebSocket):
    """
    WebSocket para recibir alertas de geofencing en tiempo real.
    
    Los operadores del dashboard se conectan a este endpoint
    para recibir notificaciones instantáneas cuando se generan alertas.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Mantener conexión activa (ping/pong)
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ===================================================================
# Endpoints de Tracking GPS
# ===================================================================

@router.post("/tracking/gps", response_model=ResultadoValidacionGPS)
async def procesar_posicion_gps(
    posicion: PosicionGPS,
    db: Session = Depends(get_db)
):
    """
    Procesar posición GPS reportada por la app móvil del conductor.
    
    Este endpoint:
    - Valida la calidad del GPS
    - Verifica velocidad, desviación de ruta, zonas, paradas
    - Genera alertas si detecta anomalías
    - Envía notificaciones en tiempo real vía WebSocket
    - Actualiza historial de posiciones
    
    Returns:
        ResultadoValidacionGPS con alertas generadas y estado del conductor
    """
    # Verificar que el conductor existe
    conductor = db.query(Conductor).filter(Conductor.id == posicion.conductor_id).first()
    if not conductor:
        raise HTTPException(status_code=404, detail=f"Conductor {posicion.conductor_id} no encontrado")
    
    # Procesar posición con el servicio
    service = GeofencingService(db)
    resultado = service.procesar_posicion_gps(posicion, conductor.id)
    
    # Enviar alertas por WebSocket si se generaron
    if resultado.alertas_generadas:
        for alerta in resultado.alertas_generadas:
            alerta_ws = AlertaWebSocket(
                id=alerta.id,
                conductor_id=alerta.conductor_id,
                conductor_nombre=conductor.nombre_completo,
                tipo=alerta.tipo,
                severidad=alerta.severidad,
                descripcion=alerta.descripcion,
                latitud=alerta.latitud,
                longitud=alerta.longitud,
                velocidad_kmh=alerta.velocidad_kmh,
                timestamp=alerta.timestamp
            )
            await manager.broadcast(alerta_ws.model_dump())
    
    return resultado


# ===================================================================
# Endpoints de Alertas
# ===================================================================

@router.get("/alertas", response_model=List[GeofenceAlertResponse])
def listar_alertas(
    conductor_id: Optional[int] = Query(None, description="Filtrar por conductor"),
    tipo: Optional[TipoAlerta] = Query(None, description="Filtrar por tipo de alerta"),
    severidad: Optional[SeveridadAlerta] = Query(None, description="Filtrar por severidad"),
    estado: Optional[EstadoAlerta] = Query(None, description="Filtrar por estado"),
    fecha_desde: Optional[date] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    limit: int = Query(100, le=500, description="Máximo de registros"),
    offset: int = Query(0, ge=0, description="Offset para paginación"),
    db: Session = Depends(get_db)
):
    """
    Listar alertas con filtros opcionales.
    
    Usado por el dashboard para mostrar:
    - Alertas activas
    - Historial de alertas
    - Alertas por conductor
    - Alertas críticas
    """
    query = db.query(GeofenceAlert)
    
    # Aplicar filtros
    if conductor_id:
        query = query.filter(GeofenceAlert.conductor_id == conductor_id)
    if tipo:
        query = query.filter(GeofenceAlert.tipo == tipo)
    if severidad:
        query = query.filter(GeofenceAlert.severidad == severidad)
    if estado:
        query = query.filter(GeofenceAlert.estado == estado)
    if fecha_desde:
        query = query.filter(GeofenceAlert.timestamp >= fecha_desde)
    if fecha_hasta:
        fecha_hasta_dt = datetime.combine(fecha_hasta, datetime.max.time())
        query = query.filter(GeofenceAlert.timestamp <= fecha_hasta_dt)
    
    # Ordenar por más reciente primero
    query = query.order_by(GeofenceAlert.timestamp.desc())
    
    # Paginación
    alertas = query.offset(offset).limit(limit).all()
    
    return alertas


@router.get("/alertas/activas", response_model=List[GeofenceAlertResponse])
def obtener_alertas_activas(
    severidad_minima: Optional[SeveridadAlerta] = Query(None, description="Severidad mínima"),
    db: Session = Depends(get_db)
):
    """
    Obtener solo alertas activas (no resueltas).
    
    Usado por el dashboard para mostrar alertas que requieren atención.
    """
    query = db.query(GeofenceAlert).filter(GeofenceAlert.estado == EstadoAlerta.ACTIVA)
    
    # Filtrar por severidad si se especifica
    if severidad_minima:
        severidades = {
            SeveridadAlerta.LOW: [SeveridadAlerta.LOW, SeveridadAlerta.MEDIUM, SeveridadAlerta.HIGH, SeveridadAlerta.CRITICAL],
            SeveridadAlerta.MEDIUM: [SeveridadAlerta.MEDIUM, SeveridadAlerta.HIGH, SeveridadAlerta.CRITICAL],
            SeveridadAlerta.HIGH: [SeveridadAlerta.HIGH, SeveridadAlerta.CRITICAL],
            SeveridadAlerta.CRITICAL: [SeveridadAlerta.CRITICAL]
        }
        query = query.filter(GeofenceAlert.severidad.in_(severidades[severidad_minima]))
    
    # Ordenar por severidad y tiempo
    orden_severidad = {
        SeveridadAlerta.CRITICAL: 4,
        SeveridadAlerta.HIGH: 3,
        SeveridadAlerta.MEDIUM: 2,
        SeveridadAlerta.LOW: 1
    }
    
    alertas = query.all()
    alertas_ordenadas = sorted(
        alertas,
        key=lambda a: (orden_severidad.get(a.severidad, 0), -a.timestamp.timestamp()),
        reverse=True
    )
    
    return alertas_ordenadas


@router.get("/alertas/{alerta_id}", response_model=GeofenceAlertResponse)
def obtener_alerta(
    alerta_id: int,
    db: Session = Depends(get_db)
):
    """Obtener detalle de una alerta específica"""
    alerta = db.query(GeofenceAlert).filter(GeofenceAlert.id == alerta_id).first()
    if not alerta:
        raise HTTPException(status_code=404, detail=f"Alerta {alerta_id} no encontrada")
    
    return alerta


@router.put("/alertas/{alerta_id}/resolver", response_model=GeofenceAlertResponse)
def resolver_alerta(
    alerta_id: int,
    update: GeofenceAlertUpdate,
    db: Session = Depends(get_db)
):
    """
    Marcar alerta como resuelta.
    
    Usado por operadores para:
    - Confirmar que se atendió la situación
    - Agregar notas sobre las acciones tomadas
    - Ignorar falsos positivos
    """
    alerta = db.query(GeofenceAlert).filter(GeofenceAlert.id == alerta_id).first()
    if not alerta:
        raise HTTPException(status_code=404, detail=f"Alerta {alerta_id} no encontrada")
    
    # Actualizar campos
    if update.estado:
        alerta.estado = update.estado
    if update.notas:
        alerta.notas = update.notas
    if update.resuelta_por:
        alerta.resuelta_por = update.resuelta_por
    
    if update.estado in [EstadoAlerta.RESUELTA, EstadoAlerta.IGNORADA]:
        alerta.resuelta_at = datetime.utcnow()
    
    db.commit()
    db.refresh(alerta)
    
    return alerta


# ===================================================================
# Endpoints de Configuración
# ===================================================================

@router.get("/config", response_model=List[GeofenceConfigResponse])
def obtener_configuracion(
    activos_solo: bool = Query(True, description="Solo parámetros activos"),
    db: Session = Depends(get_db)
):
    """
    Obtener configuración actual del sistema de geofencing.
    
    Usado por el dashboard para mostrar/editar parámetros:
    - Velocidad máxima
    - Distancia de desviación
    - Tiempo de parada
    - Precisión GPS, etc.
    """
    query = db.query(GeofenceConfig)
    
    if activos_solo:
        query = query.filter(GeofenceConfig.activo == True)
    
    configs = query.order_by(GeofenceConfig.parametro).all()
    return configs


@router.put("/config/{parametro}", response_model=GeofenceConfigResponse)
def actualizar_configuracion(
    parametro: str,
    update: GeofenceConfigUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualizar parámetro de configuración.
    
    Permite ajustar umbrales dinámicamente sin reiniciar el servicio.
    """
    config = db.query(GeofenceConfig).filter(GeofenceConfig.parametro == parametro).first()
    if not config:
        raise HTTPException(status_code=404, detail=f"Parámetro '{parametro}' no encontrado")
    
    if update.valor is not None:
        config.valor = update.valor
    if update.activo is not None:
        config.activo = update.activo
    
    db.commit()
    db.refresh(config)
    
    return config


# ===================================================================
# Endpoints de Estadísticas
# ===================================================================

@router.get("/estadisticas/{conductor_id}", response_model=EstadisticasGeofencing)
def obtener_estadisticas_conductor(
    conductor_id: int,
    fecha_desde: Optional[date] = Query(None, description="Fecha inicio"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha fin"),
    db: Session = Depends(get_db)
):
    """
    Obtener estadísticas de desempeño de un conductor.
    
    Usado para:
    - Evaluación de desempeño
    - Reportes mensuales
    - Identificación de patrones
    """
    conductor = db.query(Conductor).filter(Conductor.id == conductor_id).first()
    if not conductor:
        raise HTTPException(status_code=404, detail=f"Conductor {conductor_id} no encontrado")
    
    query = db.query(EstadisticaGeofencing).filter(
        EstadisticaGeofencing.conductor_id == conductor_id
    )
    
    if fecha_desde:
        query = query.filter(EstadisticaGeofencing.periodo_inicio >= fecha_desde)
    if fecha_hasta:
        query = query.filter(EstadisticaGeofencing.periodo_fin <= fecha_hasta)
    
    stats = query.first()
    
    if not stats:
        # Generar estadísticas si no existen
        service = GeofencingService(db)
        # TODO: Implementar generación de estadísticas
        raise HTTPException(status_code=404, detail="Estadísticas no disponibles para este período")
    
    return EstadisticasGeofencing(
        conductor_id=stats.conductor_id,
        periodo_inicio=stats.periodo_inicio,
        periodo_fin=stats.periodo_fin,
        total_alertas=stats.total_alertas,
        alertas_desviacion=stats.alertas_desviacion,
        alertas_velocidad=stats.alertas_velocidad,
        alertas_parada=stats.alertas_parada,
        alertas_zona=stats.alertas_zona,
        alertas_gps=stats.alertas_gps,
        distancia_total_km=stats.distancia_total_km,
        velocidad_promedio_kmh=stats.velocidad_promedio_kmh,
        velocidad_maxima_kmh=stats.velocidad_maxima_kmh,
        tiempo_conduccion_horas=stats.tiempo_conduccion_horas,
        puntuacion_seguridad=stats.puntuacion_seguridad
    )


@router.get("/reportes/seguridad-mensual", response_model=List[ReporteSeguridadMensual])
def obtener_reporte_seguridad(
    mes: int = Query(..., ge=1, le=12, description="Mes (1-12)"),
    anio: int = Query(..., ge=2024, description="Año"),
    db: Session = Depends(get_db)
):
    """
    Generar reporte de seguridad mensual para todos los conductores.
    
    Usado por administradores para:
    - Identificar conductores problemáticos
    - Evaluar desempeño general
    - Tomar decisiones sobre capacitación
    """
    from calendar import monthrange
    ultimo_dia = monthrange(anio, mes)[1]
    
    fecha_inicio = datetime(anio, mes, 1)
    fecha_fin = datetime(anio, mes, ultimo_dia, 23, 59, 59)
    
    # Obtener estadísticas de todos los conductores
    stats = db.query(EstadisticaGeofencing).filter(
        EstadisticaGeofencing.periodo_inicio >= fecha_inicio,
        EstadisticaGeofencing.periodo_fin <= fecha_fin
    ).all()
    
    # Transformar a reportes
    reportes = []
    for stat in stats:
        conductor = db.query(Conductor).filter(Conductor.id == stat.conductor_id).first()
        
        reportes.append(ReporteSeguridadMensual(
            conductor_id=stat.conductor_id,
            conductor_nombre=conductor.nombre_completo if conductor else "Desconocido",
            zona_asignada=conductor.zona_preferida if conductor else None,
            mes=mes,
            anio=anio,
            total_alertas=stat.total_alertas,
            alertas_criticas=db.query(GeofenceAlert).filter(
                GeofenceAlert.conductor_id == stat.conductor_id,
                GeofenceAlert.severidad == SeveridadAlerta.CRITICAL,
                GeofenceAlert.timestamp >= fecha_inicio,
                GeofenceAlert.timestamp <= fecha_fin
            ).count(),
            alertas_velocidad=stat.alertas_velocidad,
            alertas_desviacion=stat.alertas_desviacion,
            puntuacion_seguridad=stat.puntuacion_seguridad,
            velocidad_maxima_kmh=stat.velocidad_maxima_kmh
        ))
    
    # Ordenar por puntuación (peores primero)
    reportes.sort(key=lambda r: r.puntuacion_seguridad)
    
    return reportes


# ===================================================================
# Health Check
# ===================================================================

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Verificar estado del servicio de geofencing.
    
    Retorna información sobre:
    - Alertas activas
    - Conductores en ruta
    - Última posición procesada
    """
    alertas_activas = db.query(GeofenceAlert).filter(
        GeofenceAlert.estado == EstadoAlerta.ACTIVA
    ).count()
    
    alertas_criticas = db.query(GeofenceAlert).filter(
        GeofenceAlert.estado == EstadoAlerta.ACTIVA,
        GeofenceAlert.severidad == SeveridadAlerta.CRITICAL
    ).count()
    
    conductores_en_ruta = db.query(Conductor).filter(
        Conductor.estado == "en_ruta"
    ).count()
    
    return {
        "status": "ok",
        "servicio": "geofencing",
        "alertas_activas": alertas_activas,
        "alertas_criticas": alertas_criticas,
        "conductores_en_ruta": conductores_en_ruta,
        "websocket_conexiones": len(manager.active_connections),
        "timestamp": datetime.utcnow().isoformat()
    }
