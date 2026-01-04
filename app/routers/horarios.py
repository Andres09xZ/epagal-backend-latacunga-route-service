"""
Router para gestión de horarios de recolección
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Annotated, List, Optional
from datetime import datetime, date, timedelta
from geoalchemy2.shape import to_shape, from_shape
from shapely.geometry import Point, LineString, Polygon
import json

from app.database import get_db
from app.models import (
    Sector, HorarioRecoleccion, EjecucionHorario, 
    PuntoTrackingHorario, SuspensionHorario, Conductor, Usuario
)
from app.schemas.horarios import (
    # Sectores
    SectorCreate, SectorResponse, SectorDetalle,
    # Horarios
    HorarioCreate, HorarioUpdate, HorarioResponse,
    # Ejecuciones
    EjecucionResponse, EjecucionDetalle, EjecucionIniciar, 
    EjecucionFinalizar, TrackingGPS,
    # Suspensiones
    SuspensionCreate, SuspensionResponse,
    # Estadísticas
    CalendarioSemana, EstadisticasHorario, EstadisticasConductor, ResumenDiario
)

router = APIRouter(prefix="/horarios", tags=["horarios"])


# ============================================
# UTILIDADES
# ============================================

DIAS_SEMANA = {
    1: "Lunes", 2: "Martes", 3: "Miércoles", 
    4: "Jueves", 5: "Viernes", 6: "Sábado", 7: "Domingo"
}

def geojson_to_wkt(geojson: dict) -> str:
    """Convierte GeoJSON a WKT para PostGIS"""
    if geojson['type'] == 'Point':
        coords = geojson['coordinates']
        return f"POINT({coords[0]} {coords[1]})"
    elif geojson['type'] == 'Polygon':
        coords = geojson['coordinates'][0]
        points = ', '.join([f"{lon} {lat}" for lon, lat in coords])
        return f"POLYGON(({points}))"
    elif geojson['type'] == 'LineString':
        coords = geojson['coordinates']
        points = ', '.join([f"{lon} {lat}" for lon, lat in coords])
        return f"LINESTRING({points})"
    raise ValueError(f"Tipo de geometría no soportado: {geojson['type']}")


def wkt_to_geojson(wkt_geom) -> Optional[dict]:
    """Convierte geometría PostGIS a GeoJSON"""
    if not wkt_geom:
        return None
    shape = to_shape(wkt_geom)
    return json.loads(json.dumps(shape.__geo_interface__))


# ============================================
# ENDPOINTS: SECTORES
# ============================================

@router.post("/sectores", response_model=SectorResponse, status_code=201)
async def crear_sector(
    sector: SectorCreate,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Crear un nuevo sector geográfico
    
    El sector se usa para organizar horarios de recolección por zonas
    """
    # Verificar que no exista un sector con el mismo nombre
    existe = db.query(Sector).filter(Sector.nombre == sector.nombre).first()
    if existe:
        raise HTTPException(status_code=400, detail=f"Ya existe un sector con el nombre '{sector.nombre}'")
    
    # Convertir GeoJSON a WKT
    poligono_wkt = geojson_to_wkt(sector.poligono)
    centro_wkt = geojson_to_wkt(sector.coordenadas_centro)
    
    nuevo_sector = Sector(
        nombre=sector.nombre,
        zona=sector.zona.value,
        poligono=func.ST_GeomFromText(poligono_wkt, 4326),
        coordenadas_centro=func.ST_GeomFromText(centro_wkt, 4326),
        poblacion_estimada=sector.poblacion_estimada,
        cantidad_viviendas=sector.cantidad_viviendas
    )
    
    db.add(nuevo_sector)
    db.commit()
    db.refresh(nuevo_sector)
    
    return nuevo_sector


@router.get("/sectores", response_model=List[SectorResponse])
async def listar_sectores(
    db: Annotated[Session, Depends(get_db)],
    zona: Optional[str] = None,
    activo: Optional[bool] = None
):
    """
    Listar todos los sectores
    
    Filtros opcionales:
    - zona: 'oriental' u 'occidental'
    - activo: true o false
    """
    query = db.query(Sector)
    
    if zona:
        query = query.filter(Sector.zona == zona)
    if activo is not None:
        query = query.filter(Sector.activo == activo)
    
    sectores = query.order_by(Sector.nombre).all()
    return sectores


@router.get("/sectores/{sector_id}", response_model=SectorDetalle)
async def obtener_sector(
    sector_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    """Obtener detalle de un sector específico"""
    sector = db.query(Sector).filter(Sector.id == sector_id).first()
    if not sector:
        raise HTTPException(status_code=404, detail="Sector no encontrado")
    
    # Convertir geometrías a GeoJSON
    sector_dict = {
        "id": sector.id,
        "nombre": sector.nombre,
        "zona": sector.zona,
        "poblacion_estimada": sector.poblacion_estimada,
        "cantidad_viviendas": sector.cantidad_viviendas,
        "activo": sector.activo,
        "created_at": sector.created_at,
        "poligono": wkt_to_geojson(sector.poligono),
        "coordenadas_centro": wkt_to_geojson(sector.coordenadas_centro),
        "cantidad_horarios": len(sector.horarios)
    }
    
    return sector_dict


@router.patch("/sectores/{sector_id}")
async def actualizar_sector(
    sector_id: int,
    activo: bool,
    db: Annotated[Session, Depends(get_db)]
):
    """Activar o desactivar un sector"""
    sector = db.query(Sector).filter(Sector.id == sector_id).first()
    if not sector:
        raise HTTPException(status_code=404, detail="Sector no encontrado")
    
    sector.activo = activo
    sector.updated_at = datetime.utcnow()
    
    db.commit()
    return {"message": f"Sector {'activado' if activo else 'desactivado'} correctamente"}


# ============================================
# ENDPOINTS: HORARIOS
# ============================================

@router.post("/", response_model=HorarioResponse, status_code=201)
async def crear_horario(
    horario: HorarioCreate,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Crear un nuevo horario de recolección
    
    Define días de la semana y horas de operación para un sector
    """
    # Verificar que el sector existe
    sector = db.query(Sector).filter(Sector.id == horario.sector_id).first()
    if not sector:
        raise HTTPException(status_code=404, detail="Sector no encontrado")
    
    # Verificar que el conductor existe si se proporciona
    if horario.conductor_id:
        conductor = db.query(Conductor).filter(Conductor.id == horario.conductor_id).first()
        if not conductor:
            raise HTTPException(status_code=404, detail="Conductor no encontrado")
    
    # Convertir lista de días a string
    dias_str = ','.join(map(str, horario.dias_semana))
    
    nuevo_horario = HorarioRecoleccion(
        sector_id=horario.sector_id,
        dias_semana=dias_str,
        hora_inicio=horario.hora_inicio,
        hora_fin=horario.hora_fin,
        tipo=horario.tipo.value,
        descripcion=horario.descripcion,
        camion_tipo=horario.camion_tipo.value if horario.camion_tipo else None,
        conductor_id=horario.conductor_id,
        camion_placa=horario.camion_placa,
        fecha_inicio_vigencia=horario.fecha_inicio_vigencia
    )
    
    db.add(nuevo_horario)
    db.commit()
    db.refresh(nuevo_horario)
    
    # Preparar respuesta
    return _preparar_horario_response(nuevo_horario, db)


@router.post("/rutas", response_model=dict, status_code=201)
async def crear_horario_desde_ruta(
    ruta_id: int,
    dias_semana: str,
    hora_inicio: str,
    hora_fin: str,
    tipo_recoleccion: str,
    conductor_id: int,
    camion_tipo: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Crear un nuevo horario basado en una ruta generada existente
    
    Este endpoint permite programar horarios usando las rutas que ya fueron
    generadas por el sistema OR-Tools
    """
    from app.models import RutaGenerada
    
    # Verificar que la ruta existe
    ruta = db.query(RutaGenerada).filter(RutaGenerada.id == ruta_id).first()
    if not ruta:
        raise HTTPException(status_code=404, detail="Ruta no encontrada")
    
    # Verificar que el conductor existe
    conductor = db.query(Conductor).filter(Conductor.id == conductor_id).first()
    if not conductor:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")
    
    # Crear un "sector virtual" para esta ruta si no existe
    # O usar un sistema simplificado que no requiere sectores
    sector_nombre = f"Ruta #{ruta_id} - {ruta.zona}"
    sector = db.query(Sector).filter(Sector.nombre == sector_nombre).first()
    
    if not sector:
        # Crear sector temporal para esta ruta
        from geoalchemy2 import WKTElement
        # Punto central por defecto (Latacunga)
        punto_centro = WKTElement('POINT(-78.6167 -0.9333)', srid=4326)
        # Polígono simple por defecto
        poligono = WKTElement('POLYGON((-78.62 -0.93, -78.61 -0.93, -78.61 -0.94, -78.62 -0.94, -78.62 -0.93))', srid=4326)
        
        sector = Sector(
            nombre=sector_nombre,
            zona=ruta.zona,
            poligono=poligono,
            coordenadas_centro=punto_centro,
            descripcion=f"Sector generado automáticamente para ruta #{ruta_id}"
        )
        db.add(sector)
        db.commit()
        db.refresh(sector)
    
    # Crear el horario
    nuevo_horario = HorarioRecoleccion(
        sector_id=sector.id,
        dias_semana=dias_semana,
        hora_inicio=hora_inicio,
        hora_fin=hora_fin,
        tipo=tipo_recoleccion,
        camion_tipo=camion_tipo,
        conductor_id=conductor_id,
        fecha_inicio_vigencia=datetime.now(),
        activo=True
    )
    
    db.add(nuevo_horario)
    db.commit()
    db.refresh(nuevo_horario)
    
    return {
        "message": "Horario creado exitosamente",
        "horario_id": nuevo_horario.id,
        "ruta_id": ruta_id,
        "sector_id": sector.id,
        "conductor": conductor.nombre_completo
    }


@router.get("/", response_model=List[HorarioResponse])
async def listar_horarios(
    db: Annotated[Session, Depends(get_db)],
    sector_id: Optional[int] = None,
    zona: Optional[str] = None,
    activo: Optional[bool] = None
):
    """
    Listar horarios de recolección
    
    Filtros opcionales:
    - sector_id: filtrar por sector específico
    - zona: 'oriental' u 'occidental'
    - activo: true o false
    """
    query = db.query(HorarioRecoleccion).join(Sector)
    
    if sector_id:
        query = query.filter(HorarioRecoleccion.sector_id == sector_id)
    if zona:
        query = query.filter(Sector.zona == zona)
    if activo is not None:
        query = query.filter(HorarioRecoleccion.activo == activo)
    
    horarios = query.order_by(Sector.nombre, HorarioRecoleccion.hora_inicio).all()
    
    return [_preparar_horario_response(h, db) for h in horarios]


@router.get("/{horario_id}", response_model=HorarioResponse)
async def obtener_horario(
    horario_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    """Obtener detalle de un horario específico"""
    horario = db.query(HorarioRecoleccion).filter(HorarioRecoleccion.id == horario_id).first()
    if not horario:
        raise HTTPException(status_code=404, detail="Horario no encontrado")
    
    return _preparar_horario_response(horario, db)


@router.put("/{horario_id}", response_model=HorarioResponse)
async def actualizar_horario(
    horario_id: int,
    horario_update: HorarioUpdate,
    db: Annotated[Session, Depends(get_db)]
):
    """Actualizar un horario existente"""
    horario = db.query(HorarioRecoleccion).filter(HorarioRecoleccion.id == horario_id).first()
    if not horario:
        raise HTTPException(status_code=404, detail="Horario no encontrado")
    
    # Actualizar campos proporcionados
    if horario_update.dias_semana is not None:
        horario.dias_semana = ','.join(map(str, horario_update.dias_semana))
    if horario_update.hora_inicio is not None:
        horario.hora_inicio = horario_update.hora_inicio
    if horario_update.hora_fin is not None:
        horario.hora_fin = horario_update.hora_fin
    if horario_update.tipo is not None:
        horario.tipo = horario_update.tipo.value
    if horario_update.descripcion is not None:
        horario.descripcion = horario_update.descripcion
    if horario_update.camion_tipo is not None:
        horario.camion_tipo = horario_update.camion_tipo.value
    if horario_update.conductor_id is not None:
        horario.conductor_id = horario_update.conductor_id
    if horario_update.camion_placa is not None:
        horario.camion_placa = horario_update.camion_placa
    if horario_update.activo is not None:
        horario.activo = horario_update.activo
    if horario_update.fecha_fin_vigencia is not None:
        horario.fecha_fin_vigencia = horario_update.fecha_fin_vigencia
    
    horario.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(horario)
    
    return _preparar_horario_response(horario, db)


@router.delete("/{horario_id}")
async def eliminar_horario(
    horario_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    """Desactivar un horario (soft delete)"""
    horario = db.query(HorarioRecoleccion).filter(HorarioRecoleccion.id == horario_id).first()
    if not horario:
        raise HTTPException(status_code=404, detail="Horario no encontrado")
    
    horario.activo = False
    horario.fecha_fin_vigencia = datetime.utcnow()
    horario.updated_at = datetime.utcnow()
    
    db.commit()
    return {"message": "Horario desactivado correctamente"}


# ============================================
# ENDPOINTS: EJECUCIONES
# ============================================

@router.get("/ejecuciones/hoy", response_model=List[EjecucionResponse])
async def listar_ejecuciones_hoy(
    db: Annotated[Session, Depends(get_db)],
    conductor_id: Optional[int] = None,
    estado: Optional[str] = None
):
    """
    Listar ejecuciones programadas para hoy
    
    Filtros opcionales:
    - conductor_id: ver solo ejecuciones de un conductor
    - estado: filtrar por estado (programada, en_curso, completada, etc.)
    """
    hoy = date.today()
    
    query = db.query(EjecucionHorario).filter(
        func.date(EjecucionHorario.fecha_programada) == hoy
    )
    
    if conductor_id:
        query = query.filter(EjecucionHorario.conductor_id == conductor_id)
    if estado:
        query = query.filter(EjecucionHorario.estado == estado)
    
    ejecuciones = query.order_by(EjecucionHorario.hora_inicio_programada).all()
    
    return [_preparar_ejecucion_response(e, db) for e in ejecuciones]


@router.get("/ejecuciones/{ejecucion_id}", response_model=EjecucionDetalle)
async def obtener_ejecucion(
    ejecucion_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    """Obtener detalle completo de una ejecución"""
    ejecucion = db.query(EjecucionHorario).filter(EjecucionHorario.id == ejecucion_id).first()
    if not ejecucion:
        raise HTTPException(status_code=404, detail="Ejecución no encontrada")
    
    # Calcular duración y retraso
    duracion_minutos = None
    retraso_minutos = None
    
    if ejecucion.fecha_inicio_real and ejecucion.fecha_fin_real:
        duracion = ejecucion.fecha_fin_real - ejecucion.fecha_inicio_real
        duracion_minutos = int(duracion.total_seconds() / 60)
        
        # Calcular retraso
        hora_fin_esperada = datetime.combine(
            ejecucion.fecha_programada.date(),
            datetime.strptime(ejecucion.hora_fin_programada, "%H:%M").time()
        )
        if ejecucion.fecha_fin_real > hora_fin_esperada:
            retraso = ejecucion.fecha_fin_real - hora_fin_esperada
            retraso_minutos = int(retraso.total_seconds() / 60)
    
    ejecucion_dict = _preparar_ejecucion_response(ejecucion, db)
    ejecucion_dict["ruta_recorrida"] = wkt_to_geojson(ejecucion.ruta_recorrida)
    ejecucion_dict["cantidad_puntos_tracking"] = len(ejecucion.puntos_tracking)
    ejecucion_dict["duracion_real_minutos"] = duracion_minutos
    ejecucion_dict["retraso_minutos"] = retraso_minutos
    
    return ejecucion_dict


@router.patch("/ejecuciones/{ejecucion_id}/iniciar")
async def iniciar_ejecucion(
    ejecucion_id: int,
    datos: EjecucionIniciar,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Iniciar una ejecución de horario
    
    El conductor marca el inicio de la ruta
    """
    ejecucion = db.query(EjecucionHorario).filter(EjecucionHorario.id == ejecucion_id).first()
    if not ejecucion:
        raise HTTPException(status_code=404, detail="Ejecución no encontrada")
    
    if ejecucion.estado != "programada":
        raise HTTPException(status_code=400, detail=f"La ejecución ya fue iniciada (estado: {ejecucion.estado})")
    
    ejecucion.fecha_inicio_real = datetime.utcnow()
    ejecucion.estado = "en_curso"
    ejecucion.camion_placa = datos.camion_placa
    if datos.observaciones:
        ejecucion.observaciones = datos.observaciones
    ejecucion.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(ejecucion)
    
    return {
        "message": "Ejecución iniciada correctamente",
        "ejecucion": _preparar_ejecucion_response(ejecucion, db)
    }


@router.patch("/ejecuciones/{ejecucion_id}/finalizar")
async def finalizar_ejecucion(
    ejecucion_id: int,
    datos: EjecucionFinalizar,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Finalizar una ejecución de horario
    
    El conductor marca el fin de la ruta y reporta métricas
    """
    ejecucion = db.query(EjecucionHorario).filter(EjecucionHorario.id == ejecucion_id).first()
    if not ejecucion:
        raise HTTPException(status_code=404, detail="Ejecución no encontrada")
    
    if ejecucion.estado != "en_curso":
        raise HTTPException(status_code=400, detail=f"La ejecución no está en curso (estado: {ejecucion.estado})")
    
    ejecucion.fecha_fin_real = datetime.utcnow()
    ejecucion.estado = "completada"
    ejecucion.toneladas_recolectadas = datos.toneladas_recolectadas
    ejecucion.viviendas_atendidas = datos.viviendas_atendidas
    if datos.observaciones:
        ejecucion.observaciones = datos.observaciones
    if datos.incidentes:
        ejecucion.incidentes = datos.incidentes
    
    # Calcular cumplimiento
    duracion_real = ejecucion.fecha_fin_real - ejecucion.fecha_inicio_real
    hora_fin_esperada = datetime.combine(
        ejecucion.fecha_programada.date(),
        datetime.strptime(ejecucion.hora_fin_programada, "%H:%M").time()
    )
    
    if ejecucion.fecha_fin_real <= hora_fin_esperada:
        cumplimiento = 100.0
    else:
        retraso_minutos = (ejecucion.fecha_fin_real - hora_fin_esperada).total_seconds() / 60
        cumplimiento = max(0, 100 - (retraso_minutos / 60 * 20))  # Penalización del 20% por hora
    
    ejecucion.porcentaje_cumplimiento = cumplimiento
    
    # Construir LineString de ruta recorrida
    puntos = db.query(PuntoTrackingHorario).filter(
        PuntoTrackingHorario.ejecucion_id == ejecucion_id
    ).order_by(PuntoTrackingHorario.timestamp).all()
    
    if puntos:
        coords = [(to_shape(p.punto).x, to_shape(p.punto).y) for p in puntos]
        linestring = LineString(coords)
        ejecucion.ruta_recorrida = from_shape(linestring, srid=4326)
    
    ejecucion.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(ejecucion)
    
    return {
        "message": "Ejecución finalizada correctamente",
        "porcentaje_cumplimiento": cumplimiento,
        "ejecucion": _preparar_ejecucion_response(ejecucion, db)
    }


@router.post("/ejecuciones/{ejecucion_id}/tracking")
async def registrar_tracking(
    ejecucion_id: int,
    punto: TrackingGPS,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Registrar punto de tracking GPS
    
    La app móvil envía la ubicación cada 30 segundos
    """
    ejecucion = db.query(EjecucionHorario).filter(EjecucionHorario.id == ejecucion_id).first()
    if not ejecucion:
        raise HTTPException(status_code=404, detail="Ejecución no encontrada")
    
    if ejecucion.estado != "en_curso":
        raise HTTPException(status_code=400, detail="La ejecución no está en curso")
    
    punto_geom = Point(punto.lon, punto.lat)
    
    nuevo_punto = PuntoTrackingHorario(
        ejecucion_id=ejecucion_id,
        punto=from_shape(punto_geom, srid=4326),
        velocidad=punto.velocidad
    )
    
    db.add(nuevo_punto)
    db.commit()
    
    return {"message": "Punto de tracking registrado"}


# ============================================
# ENDPOINTS: SUSPENSIONES
# ============================================

@router.post("/suspensiones", response_model=SuspensionResponse, status_code=201)
async def crear_suspension(
    suspension: SuspensionCreate,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Crear una suspensión de horario
    
    Usado para feriados, mantenimiento, etc.
    """
    horario = db.query(HorarioRecoleccion).filter(HorarioRecoleccion.id == suspension.horario_id).first()
    if not horario:
        raise HTTPException(status_code=404, detail="Horario no encontrado")
    
    nueva_suspension = SuspensionHorario(
        horario_id=suspension.horario_id,
        fecha_suspension=suspension.fecha_suspension,
        motivo=suspension.motivo,
        fecha_recuperacion=suspension.fecha_recuperacion
    )
    
    db.add(nueva_suspension)
    db.commit()
    db.refresh(nueva_suspension)
    
    return _preparar_suspension_response(nueva_suspension, db)


@router.get("/suspensiones", response_model=List[SuspensionResponse])
async def listar_suspensiones(
    db: Annotated[Session, Depends(get_db)],
    horario_id: Optional[int] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None
):
    """Listar suspensiones de horarios"""
    query = db.query(SuspensionHorario)
    
    if horario_id:
        query = query.filter(SuspensionHorario.horario_id == horario_id)
    if fecha_desde:
        query = query.filter(func.date(SuspensionHorario.fecha_suspension) >= fecha_desde)
    if fecha_hasta:
        query = query.filter(func.date(SuspensionHorario.fecha_suspension) <= fecha_hasta)
    
    suspensiones = query.order_by(SuspensionHorario.fecha_suspension.desc()).all()
    
    return [_preparar_suspension_response(s, db) for s in suspensiones]


# ============================================
# ENDPOINTS: ESTADÍSTICAS Y REPORTES
# ============================================

@router.get("/estadisticas/horario/{horario_id}", response_model=EstadisticasHorario)
async def estadisticas_horario(
    horario_id: int,
    db: Annotated[Session, Depends(get_db)],
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None
):
    """Obtener estadísticas de un horario específico"""
    horario = db.query(HorarioRecoleccion).filter(HorarioRecoleccion.id == horario_id).first()
    if not horario:
        raise HTTPException(status_code=404, detail="Horario no encontrado")
    
    query = db.query(EjecucionHorario).filter(EjecucionHorario.horario_id == horario_id)
    
    if fecha_desde:
        query = query.filter(func.date(EjecucionHorario.fecha_programada) >= fecha_desde)
    if fecha_hasta:
        query = query.filter(func.date(EjecucionHorario.fecha_programada) <= fecha_hasta)
    
    ejecuciones = query.all()
    
    total = len(ejecuciones)
    completadas = sum(1 for e in ejecuciones if e.estado == "completada")
    en_curso = sum(1 for e in ejecuciones if e.estado == "en_curso")
    canceladas = sum(1 for e in ejecuciones if e.estado == "cancelada")
    atrasadas = sum(1 for e in ejecuciones if e.estado == "atrasada")
    
    cumplimientos = [e.porcentaje_cumplimiento for e in ejecuciones if e.porcentaje_cumplimiento is not None]
    promedio_cumplimiento = sum(cumplimientos) / len(cumplimientos) if cumplimientos else 0
    
    total_toneladas = sum(e.toneladas_recolectadas or 0 for e in ejecuciones)
    total_viviendas = sum(e.viviendas_atendidas or 0 for e in ejecuciones)
    
    return {
        "horario_id": horario_id,
        "total_ejecuciones": total,
        "completadas": completadas,
        "en_curso": en_curso,
        "canceladas": canceladas,
        "atrasadas": atrasadas,
        "promedio_cumplimiento": round(promedio_cumplimiento, 2),
        "total_toneladas": round(total_toneladas, 2),
        "total_viviendas": total_viviendas
    }


@router.get("/estadisticas/resumen-diario", response_model=ResumenDiario)
async def resumen_diario(
    db: Annotated[Session, Depends(get_db)],
    fecha: date = Query(default_factory=date.today)
):
    """Obtener resumen de todas las ejecuciones de un día"""
    ejecuciones = db.query(EjecucionHorario).filter(
        func.date(EjecucionHorario.fecha_programada) == fecha
    ).all()
    
    total = len(ejecuciones)
    completadas = sum(1 for e in ejecuciones if e.estado == "completada")
    en_curso = sum(1 for e in ejecuciones if e.estado == "en_curso")
    atrasadas = sum(1 for e in ejecuciones if e.estado == "atrasada")
    canceladas = sum(1 for e in ejecuciones if e.estado == "cancelada")
    
    porcentaje_cumplimiento = (completadas / total * 100) if total > 0 else 0
    
    total_toneladas = sum(e.toneladas_recolectadas or 0 for e in ejecuciones)
    total_viviendas = sum(e.viviendas_atendidas or 0 for e in ejecuciones)
    
    return {
        "fecha": fecha,
        "total_programadas": total,
        "completadas": completadas,
        "en_curso": en_curso,
        "atrasadas": atrasadas,
        "canceladas": canceladas,
        "porcentaje_cumplimiento": round(porcentaje_cumplimiento, 2),
        "total_toneladas": round(total_toneladas, 2),
        "total_viviendas": total_viviendas
    }


# ============================================
# FUNCIONES AUXILIARES
# ============================================

def _preparar_horario_response(horario: HorarioRecoleccion, db: Session) -> dict:
    """Prepara la respuesta de un horario con información adicional"""
    # Manejar dias_semana como string (ej: "Lu,Mi,Vi" o "1,3,5")
    dias_str = horario.dias_semana
    dias_nombres = []
    
    try:
        # Intentar parsear como números (formato antiguo)
        dias_lista = [int(d.strip()) for d in dias_str.split(',')]
        dias_nombres = [DIAS_SEMANA.get(d, str(d)) for d in dias_lista]
    except (ValueError, AttributeError):
        # Si no son números, son abreviaciones o nombres de días
        dias_nombres = [d.strip() for d in dias_str.split(',')]
    
    conductor_nombre = None
    if horario.conductor_id:
        conductor = db.query(Conductor).filter(Conductor.id == horario.conductor_id).first()
        if conductor and conductor.usuario:
            conductor_nombre = conductor.usuario.username
    
    duracion_minutos = None
    if horario.duracion_estimada:
        duracion_minutos = int(horario.duracion_estimada.total_seconds() / 60)
    
    return {
        "id": horario.id,
        "sector_id": horario.sector_id,
        "sector_nombre": horario.sector.nombre if horario.sector else None,
        "dias_semana": horario.dias_semana,
        "dias_semana_nombres": dias_nombres,
        "hora_inicio": horario.hora_inicio,
        "hora_fin": horario.hora_fin,
        "tipo": horario.tipo,
        "descripcion": horario.descripcion,
        "camion_tipo": horario.camion_tipo,
        "conductor_id": horario.conductor_id,
        "conductor_nombre": conductor_nombre,
        "camion_placa": horario.camion_placa,
        "distancia_km": horario.distancia_km,
        "duracion_estimada_minutos": duracion_minutos,
        "activo": horario.activo,
        "fecha_inicio_vigencia": horario.fecha_inicio_vigencia,
        "fecha_fin_vigencia": horario.fecha_fin_vigencia,
        "created_at": horario.created_at
    }


def _preparar_ejecucion_response(ejecucion: EjecucionHorario, db: Session) -> dict:
    """Prepara la respuesta de una ejecución con información adicional"""
    conductor_nombre = None
    sector_nombre = None
    
    if ejecucion.conductor:
        conductor_nombre = ejecucion.conductor.usuario.username if ejecucion.conductor.usuario else None
    
    if ejecucion.horario and ejecucion.horario.sector:
        sector_nombre = ejecucion.horario.sector.nombre
    
    return {
        "id": ejecucion.id,
        "horario_id": ejecucion.horario_id,
        "sector_nombre": sector_nombre,
        "fecha_programada": ejecucion.fecha_programada,
        "hora_inicio_programada": ejecucion.hora_inicio_programada,
        "hora_fin_programada": ejecucion.hora_fin_programada,
        "fecha_inicio_real": ejecucion.fecha_inicio_real,
        "fecha_fin_real": ejecucion.fecha_fin_real,
        "conductor_id": ejecucion.conductor_id,
        "conductor_nombre": conductor_nombre,
        "camion_placa": ejecucion.camion_placa,
        "estado": ejecucion.estado,
        "porcentaje_cumplimiento": ejecucion.porcentaje_cumplimiento,
        "observaciones": ejecucion.observaciones,
        "incidentes": ejecucion.incidentes,
        "toneladas_recolectadas": ejecucion.toneladas_recolectadas,
        "viviendas_atendidas": ejecucion.viviendas_atendidas,
        "created_at": ejecucion.created_at
    }


def _preparar_suspension_response(suspension: SuspensionHorario, db: Session) -> dict:
    """Prepara la respuesta de una suspensión con información adicional"""
    sector_nombre = None
    if suspension.horario and suspension.horario.sector:
        sector_nombre = suspension.horario.sector.nombre
    
    return {
        "id": suspension.id,
        "horario_id": suspension.horario_id,
        "sector_nombre": sector_nombre,
        "fecha_suspension": suspension.fecha_suspension,
        "motivo": suspension.motivo,
        "fecha_recuperacion": suspension.fecha_recuperacion,
        "notificado": suspension.notificado,
        "created_at": suspension.created_at
    }
