"""
Router para tracking GPS en tiempo real de camiones recolectores
Usa WebSocket para streaming de posiciones
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Annotated, List, Dict
from datetime import datetime
import json
import asyncio

from app.database import get_db
from app.models import EjecucionHorario, PuntoTrackingHorario, HorarioRecoleccion, Conductor
from pydantic import BaseModel

router = APIRouter(prefix="/tracking", tags=["tracking"])


# ============================================
# MODELOS PYDANTIC
# ============================================

class TrackingUpdate(BaseModel):
    """Update de posición GPS del camión"""
    ejecucion_id: int
    lat: float
    lon: float
    velocidad: float | None = None
    timestamp: datetime | None = None


class TrackingResponse(BaseModel):
    """Respuesta de tracking activo"""
    ejecucion_id: int
    conductor_nombre: str
    camion_placa: str
    sector: str
    lat: float
    lon: float
    velocidad: float | None
    timestamp: datetime
    estado: str


# ============================================
# GESTOR DE CONEXIONES WEBSOCKET
# ============================================

class ConnectionManager:
    """Administra conexiones WebSocket activas"""
    
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, ejecucion_id: int):
        """Conectar cliente a una ejecución específica"""
        await websocket.accept()
        if ejecucion_id not in self.active_connections:
            self.active_connections[ejecucion_id] = []
        self.active_connections[ejecucion_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, ejecucion_id: int):
        """Desconectar cliente"""
        if ejecucion_id in self.active_connections:
            self.active_connections[ejecucion_id].remove(websocket)
            if not self.active_connections[ejecucion_id]:
                del self.active_connections[ejecucion_id]
    
    async def broadcast(self, ejecucion_id: int, message: dict):
        """Enviar mensaje a todos los clientes conectados a una ejecución"""
        if ejecucion_id in self.active_connections:
            for connection in self.active_connections[ejecucion_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass


manager = ConnectionManager()


# ============================================
# ENDPOINTS REST
# ============================================

@router.get("/activos", response_model=List[TrackingResponse])
async def obtener_trackings_activos(db: Annotated[Session, Depends(get_db)]):
    """
    Obtener todas las ejecuciones actualmente en curso con última posición GPS
    """
    ejecuciones = db.query(EjecucionHorario).filter(
        EjecucionHorario.estado == 'en_curso'
    ).all()
    
    resultado = []
    for ej in ejecuciones:
        # Obtener último punto de tracking
        ultimo_punto = db.query(PuntoTrackingHorario)\
            .filter(PuntoTrackingHorario.ejecucion_id == ej.id)\
            .order_by(PuntoTrackingHorario.timestamp.desc())\
            .first()
        
        if ultimo_punto:
            from geoalchemy2.shape import to_shape
            shape = to_shape(ultimo_punto.punto)
            
            resultado.append(TrackingResponse(
                ejecucion_id=ej.id,
                conductor_nombre=ej.conductor.nombre_completo,
                camion_placa=ej.camion_placa,
                sector=ej.horario.sector.nombre,
                lat=shape.y,
                lon=shape.x,
                velocidad=ultimo_punto.velocidad,
                timestamp=ultimo_punto.timestamp,
                estado=ej.estado
            ))
    
    return resultado


@router.post("/actualizar")
async def actualizar_posicion(
    update: TrackingUpdate,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Endpoint REST para actualizar posición GPS (alternativa a WebSocket)
    Usado por app móvil del conductor
    """
    # Verificar que la ejecución existe y está activa
    ejecucion = db.query(EjecucionHorario).filter(
        EjecucionHorario.id == update.ejecucion_id,
        EjecucionHorario.estado == 'en_curso'
    ).first()
    
    if not ejecucion:
        raise HTTPException(status_code=404, detail="Ejecución no encontrada o no está activa")
    
    # Guardar punto de tracking
    nuevo_punto = PuntoTrackingHorario(
        ejecucion_id=update.ejecucion_id,
        punto=func.ST_SetSRID(func.ST_MakePoint(update.lon, update.lat), 4326),
        velocidad=update.velocidad,
        timestamp=update.timestamp or datetime.utcnow()
    )
    
    db.add(nuevo_punto)
    db.commit()
    
    # Broadcast a clientes conectados vía WebSocket
    await manager.broadcast(update.ejecucion_id, {
        "type": "position_update",
        "ejecucion_id": update.ejecucion_id,
        "lat": update.lat,
        "lon": update.lon,
        "velocidad": update.velocidad,
        "timestamp": (update.timestamp or datetime.utcnow()).isoformat()
    })
    
    return {"status": "ok", "message": "Posición actualizada"}


@router.get("/ruta/{ejecucion_id}")
async def obtener_ruta_recorrida(
    ejecucion_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Obtener todos los puntos GPS de una ejecución (ruta completa recorrida)
    """
    puntos = db.query(PuntoTrackingHorario).filter(
        PuntoTrackingHorario.ejecucion_id == ejecucion_id
    ).order_by(PuntoTrackingHorario.timestamp).all()
    
    from geoalchemy2.shape import to_shape
    
    ruta = []
    for punto in puntos:
        shape = to_shape(punto.punto)
        ruta.append({
            "lat": shape.y,
            "lon": shape.x,
            "velocidad": punto.velocidad,
            "timestamp": punto.timestamp.isoformat()
        })
    
    return {"ejecucion_id": ejecucion_id, "puntos": ruta}


# ============================================
# WEBSOCKET ENDPOINTS
# ============================================

@router.websocket("/ws/{ejecucion_id}")
async def websocket_tracking(
    websocket: WebSocket,
    ejecucion_id: int
):
    """
    WebSocket para streaming en tiempo real de posiciones GPS
    
    Conectarse: ws://localhost:8000/api/tracking/ws/{ejecucion_id}
    
    Mensajes enviados por el servidor:
    {
        "type": "position_update",
        "ejecucion_id": 123,
        "lat": -0.933,
        "lon": -78.617,
        "velocidad": 25.5,
        "timestamp": "2026-01-04T10:30:00"
    }
    """
    await manager.connect(websocket, ejecucion_id)
    
    try:
        # Enviar última posición conocida al conectarse
        db = next(get_db())
        ultimo_punto = db.query(PuntoTrackingHorario)\
            .filter(PuntoTrackingHorario.ejecucion_id == ejecucion_id)\
            .order_by(PuntoTrackingHorario.timestamp.desc())\
            .first()
        
        if ultimo_punto:
            from geoalchemy2.shape import to_shape
            shape = to_shape(ultimo_punto.punto)
            await websocket.send_json({
                "type": "position_update",
                "ejecucion_id": ejecucion_id,
                "lat": shape.y,
                "lon": shape.x,
                "velocidad": ultimo_punto.velocidad,
                "timestamp": ultimo_punto.timestamp.isoformat()
            })
        
        # Mantener conexión abierta y escuchar
        while True:
            data = await websocket.receive_text()
            # Cliente puede enviar "ping" para mantener viva la conexión
            if data == "ping":
                await websocket.send_text("pong")
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, ejecucion_id)
    except Exception as e:
        manager.disconnect(websocket, ejecucion_id)
        print(f"Error WebSocket: {e}")
