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

from app.models import Incidencia, Config, RutaGenerada
from app.schemas.incidencias import IncidenciaCreate, TipoIncidencia


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
            estado='pendiente',
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

        Nota: Solo las incidencias con estado 'validada' son consideradas
        para la generación automática de rutas.
        """
        return db.query(Incidencia).filter(
            Incidencia.zona == zona,
            Incidencia.estado == 'validada'
        ).all()

    @staticmethod
    def calcular_suma_gravedad_zona(
        db: Session,
        zona: str
    ) -> int:
        """Calcula la suma total de gravedad de incidencias validadas en una zona

        Solo las incidencias validadas (estado='validada') cuentan para el umbral.
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
    def validar_incidencia(
        db: Session,
        incidencia_id: int,
        generar_ruta_auto: bool = True
    ) -> Tuple[Incidencia, Optional[RutaGenerada]]:
        """
        Marca una incidencia como 'validada' (control por administrador)

        Si generar_ruta_auto es True, tras validar se verifica el umbral y se
        puede generar una ruta automáticamente (mismo comportamiento que al crear
        rutas pero solo considerando incidencias validadas).
        """
        incidencia = db.query(Incidencia).filter(Incidencia.id == incidencia_id).first()
        if not incidencia:
            raise ValueError(f"Incidencia {incidencia_id} no encontrada")

        # Actualizar estado a 'validada'
        incidencia.estado = 'validada'
        db.commit()
        db.refresh(incidencia)

        ruta_generada = None
        if generar_ruta_auto:
            # Importar aquí para evitar dependencia circular
            from app.services.ruta_service import RutaService
            from app.services.notificacion_service import NotificacionService

            ruta_service = RutaService()
            zona = incidencia.zona

            # Verificar si hay rutas planeadas en la zona
            rutas_planeadas = ruta_service.verificar_rutas_planeadas_zona(db, zona)

            if rutas_planeadas:
                # Evaluar si se necesita recalcular (incidencia validada puede ser crítica)
                debe_recalcular = ruta_service.evaluar_necesidad_recalculo(db, zona, incidencia.gravedad)
                if debe_recalcular:
                    ruta_generada = ruta_service.recalcular_ruta_zona(
                        db,
                        zona,
                        motivo=f"Incidencia validada {incidencia.tipo} (gravedad {incidencia.gravedad})"
                    )
                    if ruta_generada:
                        NotificacionService.notificar_nueva_ruta(
                            ruta_generada.id,
                            zona,
                            ruta_generada.camiones_usados,
                            ruta_generada.suma_gravedad,
                            es_recalculo=True
                        )
            else:
                # No hay rutas planeadas: verificar umbral con incidencias validadas
                suma_gravedad = IncidenciaService.calcular_suma_gravedad_zona(db, zona)
                supera, umbral = ruta_service.verificar_supera_umbral(db, zona, suma_gravedad)
                if supera:
                    ruta_generada = ruta_service.generar_ruta_automatica(db, zona)
                    if ruta_generada:
                        NotificacionService.notificar_nueva_ruta(
                            ruta_generada.id,
                            zona,
                            ruta_generada.camiones_usados,
                            ruta_generada.suma_gravedad,
                            es_recalculo=False
                        )

        return incidencia, ruta_generada

    @staticmethod
    def obtener_estadisticas(db: Session) -> dict:
        """Obtiene estadísticas generales de incidencias"""
        total = db.query(Incidencia).count()
        pendientes = db.query(Incidencia).filter(Incidencia.estado == 'pendiente').count()
        validadas = db.query(Incidencia).filter(Incidencia.estado == 'validada').count()
        asignadas = db.query(Incidencia).filter(Incidencia.estado == 'asignada').count()
        completadas = db.query(Incidencia).filter(Incidencia.estado == 'completada').count()
        
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
