"""
Servicios para gestión de incidencias
Incluye clasificación automática de zona y cálculo de ventanas de atención
"""
from sqlalchemy.orm import Session
from geoalchemy2 import WKTElement
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
import pyproj
from pyproj import Transformer
import logging

from app.models import Incidencia, Config, RutaGenerada, RutaDetalle
from app.schemas.incidencias import IncidenciaCreate, TipoIncidencia

# Configurar logger
logger = logging.getLogger(__name__)


# Configuración de proyecciones
# WGS84 -> UTM Zone 17S (Ecuador)
transformer_to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32717", always_xy=True)
transformer_to_wgs84 = Transformer.from_crs("EPSG:32717", "EPSG:4326", always_xy=True)


# CONFIGURACIÓN DE COORDENADAS DE LATACUNGA
class LatacungaConfig:
    """Configuración geográfica de Latacunga"""
    
    # Centro de la ciudad (Parque Vicente León)
    CENTRO_LAT = -0.9344
    CENTRO_LON = -78.6156
    
    # Límites de la zona urbana (para validación)
    LAT_MIN = -0.97  # Sur
    LAT_MAX = -0.90  # Norte
    LON_MIN = -78.65  # Oeste
    LON_MAX = -78.58  # Este
    
    # División Oriental/Occidental (Panamericana)
    LONGITUD_DIVISORIA = -78.615


class IncidenciaService:
    """Servicio para gestión de incidencias"""

    # Mapa de tipo de incidencia a gravedad
    GRAVEDAD_MAP = {
        TipoIncidencia.ACOPIO: 1,
        TipoIncidencia.ZONA_CRITICA: 3,
        TipoIncidencia.ANIMAL_MUERTO: 5
    }

    # Ventanas de atención en horas
    VENTANA_ATENCION_MAP = {
        TipoIncidencia.ACOPIO: 24,  # 24 horas
        TipoIncidencia.ZONA_CRITICA: 8,  # 8 horas
        TipoIncidencia.ANIMAL_MUERTO: 2  # 2 horas (alta prioridad)
    }

    @staticmethod
    def clasificar_zona(lon: float, lat: float) -> str:
        """
        Clasifica automáticamente la zona (oriental/occidental)
        basándose en la división de la Panamericana
        
        Args:
            lon: Longitud en WGS84
            lat: Latitud en WGS84
            
        Returns:
            'oriental' o 'occidental'
        """
        # Validar que la coordenada esté dentro de Latacunga
        if not (LatacungaConfig.LAT_MIN <= lat <= LatacungaConfig.LAT_MAX):
            raise ValueError(
                f"Latitud {lat} fuera de los límites de Latacunga "
                f"({LatacungaConfig.LAT_MIN} a {LatacungaConfig.LAT_MAX})"
            )
        
        if not (LatacungaConfig.LON_MIN <= lon <= LatacungaConfig.LON_MAX):
            raise ValueError(
                f"Longitud {lon} fuera de los límites de Latacunga "
                f"({LatacungaConfig.LON_MIN} a {LatacungaConfig.LON_MAX})"
            )
        
        # Clasificar zona
        if lon > LatacungaConfig.LONGITUD_DIVISORIA:
            return "oriental"
        else:
            return "occidental"

    @staticmethod
    def convertir_a_utm(lon: float, lat: float) -> Tuple[float, float]:
        """Convierte coordenadas WGS84 a UTM Zone 17S (Ecuador)"""
        easting, northing = transformer_to_utm.transform(lon, lat)
        return easting, northing

    @staticmethod
    def calcular_ventana_atencion(
        tipo: TipoIncidencia,
        reportado_en: datetime
    ) -> Tuple[datetime, datetime]:
        """
        Calcula ventana de atención según tipo de incidencia
        
        Returns:
            Tuple[inicio, fin] de la ventana de atención
        """
        ventana_inicio = reportado_en
        horas_ventana = IncidenciaService.VENTANA_ATENCION_MAP[tipo]
        ventana_fin = reportado_en + timedelta(hours=horas_ventana)
        
        return ventana_inicio, ventana_fin

    @staticmethod
    def crear_incidencia(
        db: Session,
        incidencia_data: IncidenciaCreate,
        generar_ruta_auto: bool = True
    ) -> Tuple[Incidencia, Optional[RutaGenerada]]:
        """
        Crea una nueva incidencia con clasificación automática
        y verifica si debe generar ruta automáticamente
        
        Reglas de negocio:
        1. Asigna gravedad según tipo
        2. Clasifica zona automáticamente
        3. Convierte a coordenadas UTM
        4. Calcula ventana de atención
        5. Verifica umbral y genera ruta si corresponde
        
        Args:
            db: Sesión de base de datos
            incidencia_data: Datos de la incidencia a crear
            generar_ruta_auto: Si True, verifica umbral y genera ruta automáticamente
            
        Returns:
            Tuple[incidencia_creada, ruta_generada_o_None]
        """
        # 1. Obtener gravedad según tipo
        gravedad = IncidenciaService.GRAVEDAD_MAP[incidencia_data.tipo]
        
        # 2. Clasificar zona automáticamente
        zona = IncidenciaService.clasificar_zona(
            incidencia_data.lon,
            incidencia_data.lat
        )
        
        # 3. Convertir a UTM
        utm_easting, utm_northing = IncidenciaService.convertir_a_utm(
            incidencia_data.lon,
            incidencia_data.lat
        )
        
        # 4. Crear geometría PostGIS (WKT)
        geom_wkt = f'POINT({incidencia_data.lon} {incidencia_data.lat})'
        geom = WKTElement(geom_wkt, srid=4326)
        
        # 5. Calcular ventana de atención
        reportado_en = datetime.utcnow()
        ventana_inicio, ventana_fin = IncidenciaService.calcular_ventana_atencion(
            incidencia_data.tipo,
            reportado_en
        )
        
        # 6. Crear instancia de incidencia
        incidencia = Incidencia(
            tipo=incidencia_data.tipo.value,
            gravedad=gravedad,
            descripcion=incidencia_data.descripcion,
            foto_url=incidencia_data.foto_url,
            lat=incidencia_data.lat,
            lon=incidencia_data.lon,
            geom=geom,
            utm_easting=utm_easting,
            utm_northing=utm_northing,
            zona=zona,
            ventana_inicio=ventana_inicio,
            ventana_fin=ventana_fin,
            estado='emitido',
            reportado_en=reportado_en,
            usuario_id=incidencia_data.usuario_id
        )
        
        db.add(incidencia)
        db.commit()
        db.refresh(incidencia)
        
        # 7. Verificar umbral y generar/recalcular ruta si corresponde
        ruta_generada = None
        if generar_ruta_auto:
            # Importar aquí para evitar dependencia circular
            from app.services.ruta_service import RutaService
            from app.services.notificacion_service import NotificacionService
            
            ruta_service = RutaService()
            
            # Verificar si hay rutas planeadas en la zona
            rutas_planeadas = ruta_service.verificar_rutas_planeadas_zona(db, zona)
            
            if rutas_planeadas:
                # Hay rutas planeadas, evaluar si necesitamos recalcular
                import logging
                logger = logging.getLogger(__name__)
                
                logger.info(
                    f"🔍 Zona {zona} tiene {len(rutas_planeadas)} ruta(s) planeada(s). "
                    f"Evaluando necesidad de recálculo..."
                )
                
                # Notificar incidencia crítica si aplica
                if gravedad >= 5:
                    NotificacionService.notificar_incidencia_critica(
                        incidencia.id,
                        incidencia.tipo,
                        zona,
                        gravedad,
                        incidencia.lat,
                        incidencia.lon
                    )
                
                # Evaluar si debemos recalcular
                debe_recalcular = ruta_service.evaluar_necesidad_recalculo(
                    db, zona, gravedad
                )
                
                if debe_recalcular:
                    logger.warning(
                        f"🚨 RECÁLCULO NECESARIO: Nueva incidencia crítica "
                        f"(gravedad={gravedad}) requiere recalcular rutas de zona {zona}"
                    )
                    
                    # Recalcular ruta
                    ruta_generada = ruta_service.recalcular_ruta_zona(
                        db,
                        zona,
                        motivo=f"Nueva incidencia {incidencia.tipo} (gravedad {gravedad})"
                    )
                else:
                    logger.info(
                        f"✓ No es necesario recalcular. Incidencia agregada a pendientes."
                    )
            else:
                # No hay rutas planeadas, verificar si supera umbral para generar nueva
                suma_gravedad = IncidenciaService.calcular_suma_gravedad_zona(db, zona)
                supera, umbral = ruta_service.verificar_supera_umbral(db, zona, suma_gravedad)
                
                if supera:
                    # Generar ruta automáticamente
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(
                        f"🚨 UMBRAL SUPERADO en zona {zona}: "
                        f"suma={suma_gravedad} > umbral={umbral}. "
                        f"Generando ruta automática..."
                    )
                    
                    ruta_generada = ruta_service.generar_ruta_automatica(db, zona)
                    
                    if ruta_generada:
                        logger.info(
                            f"✅ Ruta generada automáticamente: ID={ruta_generada.id}, "
                            f"zona={zona}, camiones={ruta_generada.camiones_usados}"
                        )
                        
                        # Notificar nueva ruta
                        NotificacionService.notificar_nueva_ruta(
                            ruta_generada.id,
                            zona,
                            ruta_generada.camiones_usados,
                            ruta_generada.suma_gravedad,
                            es_recalculo=False
                        )
        
        return incidencia, ruta_generada

    @staticmethod
    def obtener_incidencias_validadas_por_zona(
        db: Session,
        zona: str
    ) -> List[Incidencia]:
        """Obtiene todas las incidencias VALIDADAS de una zona

        Nota: Solo las incidencias con estado 'validado' son consideradas
        para la generación automática de rutas.
        """
        return db.query(Incidencia).filter(
            Incidencia.zona == zona,
            Incidencia.estado == 'validado'
        ).all()

    @staticmethod
    def calcular_suma_gravedad_zona(
        db: Session,
        zona: str
    ) -> int:
        """Calcula la suma total de gravedad de incidencias validadas en una zona

        Solo las incidencias validadas (estado='validado') cuentan para el umbral.
        """
        incidencias = IncidenciaService.obtener_incidencias_validadas_por_zona(db, zona)
        return sum(inc.gravedad for inc in incidencias)

    @staticmethod
    def verificar_umbral_ruta(
        db: Session,
        zona: str
    ) -> Tuple[bool, int]:
        """
        Verifica si se alcanzó el umbral para generar ruta
        
        IMPORTANTE: Debe SUPERAR estrictamente (>) el umbral, no solo alcanzarlo (>=)
        
        Returns:
            Tuple[debe_generar_ruta: bool, suma_gravedad: int]
        """
        # Obtener umbral desde configuración
        config = db.query(Config).filter(Config.clave == 'umbral_gravedad').first()
        umbral = int(config.valor) if config else 20

        # Solo se cuentan incidencias validadas
        suma_gravedad = IncidenciaService.calcular_suma_gravedad_zona(db, zona)

        # Debe ser estrictamente mayor (>) no mayor o igual (>=)
        return suma_gravedad > umbral, suma_gravedad

    @staticmethod
    def calcular_distancia_haversine(
        lat1: float, lon1: float,
        lat2: float, lon2: float
    ) -> float:
        """
        Calcula distancia en metros entre dos coordenadas usando fórmula de Haversine
        
        Args:
            lat1, lon1: Coordenadas del primer punto
            lat2, lon2: Coordenadas del segundo punto
            
        Returns:
            float: Distancia en metros
        """
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371000  # Radio de la Tierra en metros
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        return R * c

    @staticmethod
    def validar_incidencia(
        db: Session,
        incidencia_id: int,
        generar_ruta_auto: bool = True
    ) -> Tuple[Incidencia, Optional[RutaGenerada]]:
        """
        Valida una incidencia y gestiona la generación automática de rutas
        
        LÓGICA MEJORADA PARA EVITAR SOLAPAMIENTO:
        1. Valida la incidencia (recibido → validado)
        2. Verifica si hay rutas PLANEADAS en la zona
        3. Si hay rutas planeadas:
           - Calcula distancia a cada punto de cada ruta
           - Si está CERCA (< 500m): NO genera nueva ruta, solo registra
           - Si está LEJOS (≥ 500m): Acumula y verifica umbral para nueva ruta
        4. Si NO hay rutas planeadas: Verifica umbral y genera si supera
        
        Args:
            db: Sesión de base de datos
            incidencia_id: ID de la incidencia a validar
            generar_ruta_auto: Si True, verifica umbral y genera ruta automáticamente
            
        Returns:
            Tuple[incidencia_validada, ruta_generada_o_None]
        """
        # 1. Obtener y validar incidencia
        incidencia = db.query(Incidencia).filter(Incidencia.id == incidencia_id).first()
        if not incidencia:
            raise ValueError(f"Incidencia {incidencia_id} no encontrada")
        
        if incidencia.estado not in ('emitido', 'recibido'):
            raise ValueError(
                f"No se puede validar una incidencia en estado '{incidencia.estado}'"
            )

        # Cambiar estado a validado
        incidencia.estado = 'validado'
        db.commit()
        db.refresh(incidencia)
        
        logger.info(f"✅ Incidencia #{incidencia.id} validada exitosamente")

        ruta_generada = None
        if not generar_ruta_auto:
            return incidencia, None
            
        # Importar servicios
        from app.services.ruta_service import RutaService
        from app.services.notificacion_service import NotificacionService

        ruta_service = RutaService()
        zona = incidencia.zona

        # 2. Verificar si hay rutas PLANEADAS en la zona
        rutas_planeadas = ruta_service.verificar_rutas_planeadas_zona(db, zona)

        if rutas_planeadas:
            # Hay rutas planeadas: verificar si la incidencia está cerca de alguna
            logger.info(
                f"📋 Existen {len(rutas_planeadas)} ruta(s) planeada(s) en zona {zona}. "
                f"Verificando cercanía con incidencia #{incidencia.id}..."
            )
            
            RADIO_CERCANIA = 500  # 500 metros
            esta_cerca = False
            ruta_mas_cercana = None
            distancia_minima = float('inf')
            
            # Verificar distancia a cada ruta planeada
            for ruta in rutas_planeadas:
                # Obtener detalles de incidencias de esta ruta
                detalles = db.query(RutaDetalle).filter(
                    RutaDetalle.ruta_id == ruta.id,
                    RutaDetalle.tipo_punto == 'incidencia'
                ).all()
                
                for detalle in detalles:
                    distancia = IncidenciaService.calcular_distancia_haversine(
                        incidencia.lat, incidencia.lon,
                        detalle.lat, detalle.lon
                    )
                    
                    if distancia < distancia_minima:
                        distancia_minima = distancia
                        ruta_mas_cercana = ruta
                    
                    if distancia < RADIO_CERCANIA:
                        esta_cerca = True
            
            if esta_cerca and ruta_mas_cercana:
                # La incidencia está CERCA de una ruta existente
                logger.info(
                    f"📍 Incidencia #{incidencia.id} está a {distancia_minima:.0f}m "
                    f"de la Ruta #{ruta_mas_cercana.id}. "
                    f"⚠️ NO se genera nueva ruta para evitar solapamiento. "
                    f"La incidencia queda validada para futuras rutas."
                )
                # No hacemos nada más, la incidencia queda en estado 'validado'
                return incidencia, None
            
            # La incidencia está LEJOS de todas las rutas existentes
            logger.info(
                f"📍 Incidencia #{incidencia.id} está LEJOS de todas las rutas planeadas "
                f"(distancia mínima: {distancia_minima:.0f}m > {RADIO_CERCANIA}m). "
                f"Verificando si incidencias lejanas superan umbral..."
            )
            
            # CLAVE: Solo contar incidencias validadas que NO están en rutas planeadas
            # Obtener IDs de incidencias ya asignadas a rutas planeadas
            ids_en_rutas = set()
            for ruta in rutas_planeadas:
                detalles = db.query(RutaDetalle).filter(
                    RutaDetalle.ruta_id == ruta.id,
                    RutaDetalle.tipo_punto == 'incidencia'
                ).all()
                ids_en_rutas.update(d.incidencia_id for d in detalles if d.incidencia_id)
            
            # Calcular suma solo con incidencias validadas NO asignadas a rutas
            incidencias_disponibles = db.query(Incidencia).filter(
                Incidencia.zona == zona,
                Incidencia.estado == 'validado',
                ~Incidencia.id.in_(ids_en_rutas) if ids_en_rutas else True
            ).all()
            
            suma_gravedad = sum(inc.gravedad for inc in incidencias_disponibles)
            
            # Obtener umbral para comparación
            config = db.query(Config).filter(Config.clave == 'umbral_gravedad').first()
            umbral = int(config.valor) if config else 20
            supera = suma_gravedad > umbral
            
            logger.info(
                f"📊 Umbral zona {zona}: "
                f"suma={suma_gravedad} (de {len(incidencias_disponibles)} incidencias disponibles, "
                f"excluyendo {len(ids_en_rutas)} ya en rutas), "
                f"umbral={umbral}, supera={supera}"
            )
            
            if supera:
                # Generar NUEVA ruta independiente
                logger.info(f"🚨 ¡UMBRAL SUPERADO! Generando nueva ruta en zona {zona}...")
                ruta_generada = ruta_service.generar_ruta_automatica(db, zona)
                
                if ruta_generada:
                    logger.info(
                        f"✅ Nueva Ruta #{ruta_generada.id} generada con "
                        f"{ruta_generada.camiones_usados} camión(es)"
                    )
                    NotificacionService.notificar_nueva_ruta(
                        ruta_generada.id,
                        zona,
                        ruta_generada.camiones_usados,
                        ruta_generada.suma_gravedad,
                        es_recalculo=False
                    )
            else:
                logger.info(
                    f"ℹ️ Umbral no superado. Faltan {umbral - suma_gravedad} puntos "
                    f"para generar nueva ruta."
                )
        else:
            # NO hay rutas planeadas: verificar umbral normalmente
            logger.info(f"📋 NO hay rutas planeadas en zona {zona}. Verificando umbral...")
            
            suma_gravedad = IncidenciaService.calcular_suma_gravedad_zona(db, zona)
            supera, umbral = ruta_service.verificar_supera_umbral(db, zona, suma_gravedad)
            
            logger.info(
                f"� Umbral zona {zona}: suma={suma_gravedad}, umbral={umbral}, supera={supera}"
            )
            
            if supera:
                logger.info(f"🚨 ¡UMBRAL SUPERADO! Generando primera ruta en zona {zona}...")
                ruta_generada = ruta_service.generar_ruta_automatica(db, zona)
                
                if ruta_generada:
                    logger.info(
                        f"✅ Ruta #{ruta_generada.id} generada con "
                        f"{ruta_generada.camiones_usados} camión(es)"
                    )
                    NotificacionService.notificar_nueva_ruta(
                        ruta_generada.id,
                        zona,
                        ruta_generada.camiones_usados,
                        ruta_generada.suma_gravedad,
                        es_recalculo=False
                    )
            else:
                logger.info(
                    f"ℹ️ Umbral no superado. Faltan {umbral - suma_gravedad} puntos."
                )

        return incidencia, ruta_generada

    @staticmethod
    def obtener_estadisticas(db: Session) -> dict:
        """Obtiene estadísticas generales de incidencias"""
        total = db.query(Incidencia).count()
        pendientes = db.query(Incidencia).filter(Incidencia.estado == 'recibido').count()
        validadas = db.query(Incidencia).filter(Incidencia.estado == 'validado').count()
        asignadas = db.query(Incidencia).filter(Incidencia.estado == 'en_ejecucion').count()
        completadas = db.query(Incidencia).filter(Incidencia.estado == 'finalizado').count()
        
        # Por tipo
        por_tipo = {}
        for tipo in ['acopio', 'zona_critica', 'animal_muerto']:
            count = db.query(Incidencia).filter(Incidencia.tipo == tipo).count()
            por_tipo[tipo] = count
        
        # Por zona
        por_zona = {}
        for zona in ['oriental', 'occidental']:
            count = db.query(Incidencia).filter(Incidencia.zona == zona).count()
            por_zona[zona] = count
        
        return {
            "total": total,
            "pendientes": pendientes,
            "validadas": validadas,
            "asignadas": asignadas,
            "completadas": completadas,
            "por_tipo": por_tipo,
            "por_zona": por_zona
        }
