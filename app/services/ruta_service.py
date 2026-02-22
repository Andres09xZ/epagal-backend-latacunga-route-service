"""
Servicio para generación automática de rutas optimizadas
Gestiona la activación por umbral y asignación de camiones
"""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging
import math

import numpy as np
from sklearn.cluster import DBSCAN

from app.models import (
    Incidencia, RutaGenerada, RutaDetalle, 
    PuntoFijo, Config
)
from app.osrm_service import OSRMService
from app.services.notificacion_service import NotificacionService

logger = logging.getLogger(__name__)


class RutaService:
    """Servicio para gestión de rutas optimizadas"""
    
    # Capacidades de camiones (en puntos de gravedad)
    CAPACIDAD_LATERAL = 15  # Camión lateral
    CAPACIDAD_POSTERIOR = 25  # Camión posterior
    
    # Umbral por defecto si no está configurado
    UMBRAL_DEFAULT = 20

    # Radio de clustering por defecto (km) — C4
    RADIO_CLUSTERING_DEFAULT = 3.0
    
    def __init__(self, osrm_service: Optional[OSRMService] = None):
        self.osrm = osrm_service or OSRMService()
    
    @staticmethod
    def obtener_umbral(db: Session) -> int:
        """Obtiene el umbral de gravedad desde la configuración"""
        config = db.query(Config).filter(Config.clave == 'umbral_gravedad').first()
        if config:
            return config.get_valor_convertido()
        return RutaService.UMBRAL_DEFAULT
    
    @staticmethod
    def verificar_supera_umbral(
        db: Session, 
        zona: str,
        suma_actual: int
    ) -> Tuple[bool, int]:
        """
        Verifica si la suma de gravedad supera estrictamente el umbral (>)
        
        Args:
            db: Sesión de base de datos
            zona: Zona a verificar ('oriental' o 'occidental')
            suma_actual: Suma actual de gravedad en la zona
            
        Returns:
            Tuple[supera: bool, umbral: int]
        """
        umbral = RutaService.obtener_umbral(db)
        supera = suma_actual > umbral  # Debe ser MAYOR, no >= 
        
        logger.info(
            f"Verificación umbral zona {zona}: "
            f"suma_actual={suma_actual}, umbral={umbral}, supera={supera}"
        )
        
        return supera, umbral
    
    def asignar_camiones(
        self,
        incidencias: List[Incidencia]
    ) -> List[Dict]:
        """
        Asigna camiones según capacidad y gravedad de incidencias
        
        Estrategia:
        1. Ordenar incidencias por gravedad (descendente)
        2. Usar posterior primero (mayor capacidad)
        3. Si excede capacidad, usar lateral adicional
        
        Args:
            incidencias: Lista de incidencias pendientes
            
        Returns:
            Lista de dicts con asignaciones: 
            [{"tipo": "posterior", "incidencias": [...], "carga": 15}, ...]
        """
        # Ordenar por gravedad descendente (más urgentes primero)
        incidencias_ordenadas = sorted(
            incidencias, 
            key=lambda x: x.gravedad, 
            reverse=True
        )
        
        camiones = []
        
        # Intentar usar posterior primero
        carga_actual = 0
        camion_actual = {
            "tipo": "posterior",
            "incidencias": [],
            "carga": 0
        }
        
        for inc in incidencias_ordenadas:
            # Si cabe en el camión actual
            if carga_actual + inc.gravedad <= RutaService.CAPACIDAD_POSTERIOR:
                camion_actual["incidencias"].append(inc)
                carga_actual += inc.gravedad
                camion_actual["carga"] = carga_actual
            else:
                # Guardar camión actual si tiene incidencias
                if camion_actual["incidencias"]:
                    camiones.append(camion_actual)
                
                # Crear nuevo camión lateral (menor capacidad)
                carga_actual = inc.gravedad
                camion_actual = {
                    "tipo": "lateral",
                    "incidencias": [inc],
                    "carga": carga_actual
                }
        
        # Agregar último camión
        if camion_actual["incidencias"]:
            camiones.append(camion_actual)
        
        logger.info(
            f"Asignación de camiones: {len(camiones)} camiones "
            f"({sum(1 for c in camiones if c['tipo']=='posterior')} posterior, "
            f"{sum(1 for c in camiones if c['tipo']=='lateral')} lateral)"
        )
        
        return camiones
    
    def calcular_ruta_optima(
        self,
        db: Session,
        camion: Dict,
        zona: str
    ) -> Optional[Dict]:
        """
        Calcula la ruta óptima para un camión
        
        Secuencia: Depósito -> Incidencias (optimizadas) -> Botadero
        
        Args:
            db: Sesión de base de datos
            camion: Dict con tipo e incidencias asignadas
            zona: Zona de la ruta
            
        Returns:
            Dict con información de la ruta calculada
        """
        # Obtener puntos fijos
        deposito = db.query(PuntoFijo).filter(
            PuntoFijo.tipo == 'deposito',
            PuntoFijo.activo == True
        ).first()
        
        botadero = db.query(PuntoFijo).filter(
            PuntoFijo.tipo == 'botadero',
            PuntoFijo.activo == True
        ).first()
        
        if not deposito or not botadero:
            logger.error("No se encontraron depósito o botadero activos")
            return None
        
        # Construir lista de coordenadas
        # Inicio: depósito
        coordenadas = [(deposito.lon, deposito.lat)]
        
        # Incidencias (usar OSRM optimize si hay más de 2)
        incidencias_coords = [
            (inc.lon, inc.lat) for inc in camion["incidencias"]
        ]
        
        logger.info(f"Calculando ruta: depósito={deposito.lon},{deposito.lat}, "
                   f"incidencias={len(incidencias_coords)}, botadero={botadero.lon},{botadero.lat}")
        
        if len(incidencias_coords) > 2:
            # Optimizar orden de visita con TSP
            todas_coords = [(deposito.lon, deposito.lat)] + incidencias_coords + [(botadero.lon, botadero.lat)]
            resultado_tsp = self.osrm.optimize_trip(
                todas_coords,
                source="first",  # Empezar en depósito
                destination="last",  # Terminar en botadero
                roundtrip=False
            )
            
            if resultado_tsp:
                # OSRM optimize_trip ya retorna la ruta completa
                # Usar los datos directamente
                coordenadas = todas_coords  # Usar coordenadas originales en orden dado
                # No necesitamos reorganizar porque OSRM trip ya lo hace
                logger.info(f"Ruta optimizada con TSP: {len(coordenadas)} puntos")
            else:
                # Fallback: usar orden original
                coordenadas.extend(incidencias_coords)
                coordenadas.append((botadero.lon, botadero.lat))
                logger.warning("No se pudo optimizar con TSP, usando orden original")
        else:
            # Pocas incidencias, usar orden directo
            coordenadas.extend(incidencias_coords)
            coordenadas.append((botadero.lon, botadero.lat))
            logger.info(f"Orden directo: {len(coordenadas)} puntos")
        
        # Calcular ruta final
        ruta = self.osrm.calculate_route(coordenadas)
        
        if not ruta:
            logger.error("Error al calcular ruta con OSRM")
            return None
        
        return {
            "coordenadas": coordenadas,
            "distancia": ruta["distance"],  # metros
            "duracion": ruta["duration"],   # segundos
            "geometria": ruta["geometry"],
            "deposito": deposito,
            "botadero": botadero
        }
    
    @staticmethod
    def obtener_radio_clustering(db: Session) -> float:
        """Obtiene el radio de clustering en km desde la configuración (C4)"""
        config = db.query(Config).filter(Config.clave == 'radio_clustering_km').first()
        if config:
            try:
                return float(config.valor)
            except (ValueError, TypeError):
                pass
        return RutaService.RADIO_CLUSTERING_DEFAULT

    def agrupar_por_clustering(
        self,
        db: Session,
        incidencias: List[Incidencia]
    ) -> List[List[Incidencia]]:
        """
        Agrupa incidencias por proximidad geográfica usando DBSCAN (C4).

        Utiliza la distancia Haversine convertida a radianes para el eps de DBSCAN.
        El radio máximo de cada cluster es configurable via Config 'radio_clustering_km'.

        Args:
            db: Sesión de base de datos
            incidencias: Lista de incidencias validadas a agrupar

        Returns:
            Lista de clusters; cada cluster es una lista de incidencias.
            Las incidencias marcadas como ruido (etiqueta -1) se agrupan en un
            cluster adicional de desbordamiento para no descartarlas.
        """
        if not incidencias:
            return []

        if len(incidencias) == 1:
            return [incidencias]

        # Radio en km → convertir a radianes para métrica haversine de sklearn
        radio_km = self.obtener_radio_clustering(db)
        # Radio de la Tierra ≈ 6371 km
        eps_rad = radio_km / 6371.0

        # Construir matriz (lat, lon) en radianes
        coordenadas = np.radians(
            [(inc.lat, inc.lon) for inc in incidencias]
        )

        db_scan = DBSCAN(
            eps=eps_rad,
            min_samples=1,           # Un solo punto ya forma un cluster
            algorithm='ball_tree',
            metric='haversine'
        )
        etiquetas = db_scan.fit_predict(coordenadas)

        # Agrupar por etiqueta
        clusters: Dict[int, List[Incidencia]] = {}
        for inc, etiqueta in zip(incidencias, etiquetas):
            clusters.setdefault(etiqueta, []).append(inc)

        # Las etiquetas ≥ 0 son clusters válidos; -1 son ruido (outliers)
        resultado = [v for k, v in sorted(clusters.items()) if k >= 0]

        # Si hay ruido, añadir como cluster de desbordamiento
        if -1 in clusters:
            resultado.append(clusters[-1])
            logger.info(
                f"DBSCAN: {len(clusters[-1])} incidencia(s) marcadas como ruido "
                "agrupadas en cluster de desbordamiento"
            )

        logger.info(
            f"DBSCAN clustering: {len(incidencias)} incidencias → "
            f"{len(resultado)} clusters (radio={radio_km}km)"
        )
        return resultado

    @staticmethod
    def calcular_centroide(incidencias: List[Incidencia]) -> Tuple[float, float]:
        """
        Calcula el centroide geográfico (media aritmética) de un grupo de incidencias (C5).

        Returns:
            Tuple (lat, lon) del centroide.
        """
        if not incidencias:
            return (0.0, 0.0)
        lat_mean = sum(inc.lat for inc in incidencias) / len(incidencias)
        lon_mean = sum(inc.lon for inc in incidencias) / len(incidencias)
        return (round(lat_mean, 6), round(lon_mean, 6))

    def generar_ruta_automatica(
        self,
        db: Session,
        zona: str
    ) -> Optional[RutaGenerada]:
        """
        Genera automáticamente una ruta óptima para una zona
        
        Proceso:
        1. Obtener incidencias pendientes de la zona
        2. Calcular suma de gravedad
        3. Asignar camiones según capacidad
        4. Calcular rutas óptimas para cada camión
        5. Crear registros en base de datos
        6. Actualizar estado de incidencias a 'en_ejecucion'
        
        Args:
            db: Sesión de base de datos
            zona: Zona para generar ruta ('oriental' o 'occidental')
            
        Returns:
            RutaGenerada creada o None si hay error
        """
        logger.info(f"Iniciando generación automática de ruta para zona {zona}")
        
        # 1. Obtener incidencias validadas (listas para asignar a rutas)
        incidencias = db.query(Incidencia).filter(
            Incidencia.zona == zona,
            Incidencia.estado == 'validado'
        ).all()
        
        if not incidencias:
            logger.warning(f"No hay incidencias validadas en zona {zona}")
            return None

        # 1b. Agrupar incidencias por cercanía (C4 — DBSCAN)
        clusters = self.agrupar_por_clustering(db, incidencias)

        # Si hay múltiples clusters, generar una ruta por cluster dominante
        # (el de mayor suma de gravedad), y encolar los demás para futura ejecución.
        # Por ahora tomamos el cluster con mayor gravedad acumulada como el principal.
        cluster_principal = max(clusters, key=lambda c: sum(inc.gravedad for inc in c))
        incidencias = cluster_principal

        # 2. Calcular suma de gravedad
        suma_gravedad = sum(inc.gravedad for inc in incidencias)
        logger.info(f"Cluster principal zona {zona}: {len(incidencias)} incidencias, gravedad={suma_gravedad}")

        # 2b. Calcular centroide del cluster (C5)
        centroide_lat, centroide_lon = self.calcular_centroide(incidencias)
        
        # 3. Asignar camiones
        asignacion_camiones = self.asignar_camiones(incidencias)
        
        # 4. Crear registro de ruta
        ruta_generada = RutaGenerada(
            zona=zona,
            fecha_generacion=datetime.utcnow(),
            suma_gravedad=suma_gravedad,
            costo_total=0.0,  # Se actualizará después
            duracion_estimada=timedelta(seconds=0),  # Se actualizará después
            camiones_usados=len(asignacion_camiones),
            estado='planeada',
            centroide_lat=centroide_lat,    # C5
            centroide_lon=centroide_lon,    # C5
            notas=f"Ruta generada automáticamente por umbral. {len(incidencias)} incidencias, {len(asignacion_camiones)} camiones"
        )
        
        db.add(ruta_generada)
        db.flush()  # Obtener ID sin commitear aún
        
        # 5. Calcular y guardar detalles de ruta para cada camión
        distancia_total = 0.0
        duracion_total = 0
        orden_global = 1
        
        for idx, camion in enumerate(asignacion_camiones, 1):
            ruta_info = self.calcular_ruta_optima(db, camion, zona)
            
            if not ruta_info:
                logger.error(f"Error al calcular ruta para camión {idx}")
                db.rollback()
                return None
            
            distancia_total += ruta_info["distancia"]
            duracion_total += ruta_info["duracion"]
            
            # Crear detalles de ruta
            # Punto 1: Depósito
            detalle_deposito = RutaDetalle(
                ruta_id=ruta_generada.id,
                camion_tipo=camion["tipo"],
                camion_id=f"{camion['tipo'].upper()}-{idx}",
                orden=orden_global,
                tipo_punto='deposito',
                lat=ruta_info["deposito"].lat,
                lon=ruta_info["deposito"].lon,
                llegada_estimada=datetime.utcnow(),
                tiempo_servicio=timedelta(minutes=5),
                carga_acumulada=0
            )
            db.add(detalle_deposito)
            orden_global += 1
            
            # Puntos 2-N: Incidencias
            carga_acum = 0
            tiempo_acum = timedelta(minutes=5)  # Tiempo en depósito
            
            for inc in camion["incidencias"]:
                carga_acum += inc.gravedad
                tiempo_acum += timedelta(minutes=15)  # Estimado por incidencia
                
                detalle_incidencia = RutaDetalle(
                    ruta_id=ruta_generada.id,
                    camion_tipo=camion["tipo"],
                    camion_id=f"{camion['tipo'].upper()}-{idx}",
                    orden=orden_global,
                    incidencia_id=inc.id,
                    tipo_punto='incidencia',
                    lat=inc.lat,
                    lon=inc.lon,
                    llegada_estimada=datetime.utcnow() + tiempo_acum,
                    tiempo_servicio=timedelta(minutes=10),
                    carga_acumulada=carga_acum
                )
                db.add(detalle_incidencia)
                orden_global += 1
                
                # Actualizar estado de incidencia a 'en_ejecucion'
                inc.estado = 'en_ejecucion'
            
            # Último punto: Botadero
            tiempo_acum += timedelta(minutes=10)
            detalle_botadero = RutaDetalle(
                ruta_id=ruta_generada.id,
                camion_tipo=camion["tipo"],
                camion_id=f"{camion['tipo'].upper()}-{idx}",
                orden=orden_global,
                tipo_punto='botadero',
                lat=ruta_info["botadero"].lat,
                lon=ruta_info["botadero"].lon,
                llegada_estimada=datetime.utcnow() + tiempo_acum,
                tiempo_servicio=timedelta(minutes=15),
                carga_acumulada=carga_acum
            )
            db.add(detalle_botadero)
            orden_global += 1
        
        # 6. Actualizar totales en ruta generada
        ruta_generada.costo_total = distancia_total  # metros
        ruta_generada.duracion_estimada = timedelta(seconds=duracion_total)
        
        # Commit final
        db.commit()
        db.refresh(ruta_generada)
        
        logger.info(
            f"Ruta generada exitosamente: ID={ruta_generada.id}, "
            f"zona={zona}, camiones={len(asignacion_camiones)}, "
            f"distancia={distancia_total:.2f}m, duración={duracion_total/60:.2f}min"
        )
        
        return ruta_generada
    
    @staticmethod
    def obtener_rutas_por_zona(
        db: Session,
        zona: str,
        estado: Optional[str] = None
    ) -> List[RutaGenerada]:
        """Obtiene rutas de una zona, opcionalmente filtradas por estado"""
        query = db.query(RutaGenerada).filter(RutaGenerada.zona == zona)
        
        if estado:
            query = query.filter(RutaGenerada.estado == estado)
        
        return query.order_by(RutaGenerada.fecha_generacion.desc()).all()
    
    @staticmethod
    def obtener_detalles_ruta(
        db: Session,
        ruta_id: int
    ) -> List[RutaDetalle]:
        """Obtiene los detalles ordenados de una ruta"""
        return db.query(RutaDetalle).filter(
            RutaDetalle.ruta_id == ruta_id
        ).order_by(RutaDetalle.orden).all()
    
    @staticmethod
    def verificar_rutas_planeadas_zona(
        db: Session,
        zona: str
    ) -> List[RutaGenerada]:
        """
        Verifica si existen rutas en estado 'planeada' para una zona
        
        Args:
            db: Sesión de base de datos
            zona: Zona a verificar
            
        Returns:
            Lista de rutas planeadas en la zona
        """
        return db.query(RutaGenerada).filter(
            RutaGenerada.zona == zona,
            RutaGenerada.estado == 'planeada'
        ).all()
    
    @staticmethod
    def calcular_gravedad_total_zona(
        db: Session,
        zona: str,
        incluir_asignadas: bool = True
    ) -> int:
        """
        Calcula la suma total de gravedad en una zona
        
        Args:
            db: Sesión de base de datos
            zona: Zona a calcular
            incluir_asignadas: Si True, incluye incidencias ya asignadas a rutas planeadas
            
        Returns:
            Suma total de gravedad
        """
        query = db.query(Incidencia).filter(Incidencia.zona == zona)
        
        if incluir_asignadas:
            # Incluir validadas y en_ejecucion (pero solo si la ruta está 'planeada', no en ejecución)
            query = query.filter(Incidencia.estado.in_(['validado', 'en_ejecucion']))
        else:
            # Solo validadas (listas para asignar)
            query = query.filter(Incidencia.estado == 'validado')
        
        incidencias = query.all()
        return sum(inc.gravedad for inc in incidencias)
    
    def recalcular_ruta_zona(
        self,
        db: Session,
        zona: str,
        motivo: str = "Nueva incidencia crítica"
    ) -> Optional[RutaGenerada]:
        """
        Recalcula la ruta de una zona cuando llegan nuevas incidencias críticas
        
        Proceso:
        1. Verificar si hay rutas planeadas en la zona
        2. Liberar incidencias de rutas planeadas (volver a 'validado')
        3. Marcar rutas antiguas como canceladas
        4. Generar nueva ruta con todas las incidencias
        5. Notificar a conductores
        
        Args:
            db: Sesión de base de datos
            zona: Zona a recalcular
            motivo: Razón del recálculo
            
        Returns:
            Nueva RutaGenerada o None si no se pudo recalcular
        """
        inicio_recalculo = datetime.utcnow()
        logger.info(f"🔄 Iniciando RECÁLCULO de ruta para zona {zona}. Motivo: {motivo}")
        
        # 1. Obtener rutas planeadas
        rutas_planeadas = self.verificar_rutas_planeadas_zona(db, zona)
        
        if rutas_planeadas:
            logger.info(f"Se encontraron {len(rutas_planeadas)} rutas planeadas que serán reemplazadas")
            
            # 2. Liberar incidencias asignadas de rutas planeadas
            for ruta in rutas_planeadas:
                # Obtener todas las incidencias de esta ruta
                detalles = db.query(RutaDetalle).filter(
                    RutaDetalle.ruta_id == ruta.id,
                    RutaDetalle.tipo_punto == 'incidencia'
                ).all()
                
                incidencias_liberadas = 0
                for detalle in detalles:
                    if detalle.incidencia_id:
                        incidencia = db.query(Incidencia).filter(
                            Incidencia.id == detalle.incidencia_id
                        ).first()
                        
                        if incidencia and incidencia.estado == 'en_ejecucion':
                            incidencia.estado = 'validado'  # Volver a validado
                            incidencias_liberadas += 1
                
                logger.info(f"Liberadas {incidencias_liberadas} incidencias de ruta {ruta.id}")
                
                # 3. Marcar ruta como cancelada/reemplazada
                ruta.estado = 'completada'  # O podríamos agregar un estado 'cancelada'
                ruta.notas = (ruta.notas or "") + f"\n[RECALCULADA] {motivo} - {datetime.utcnow().isoformat()}"
                
                # 4. Notificar cancelación
                NotificacionService.notificar_ruta_cancelada(
                    ruta.id,
                    zona,
                    motivo
                )
            
            db.commit()
        
        # 5. Generar nueva ruta con TODAS las incidencias pendientes
        nueva_ruta = self.generar_ruta_automatica(db, zona)
        
        if nueva_ruta:
            tiempo_recalculo = (datetime.utcnow() - inicio_recalculo).total_seconds()
            logger.info(
                f"✅ RECÁLCULO COMPLETADO en {tiempo_recalculo:.2f} segundos. "
                f"Nueva ruta ID: {nueva_ruta.id}"
            )
            
            # 6. Notificar nueva ruta (indicando que es recálculo)
            NotificacionService.notificar_nueva_ruta(
                nueva_ruta.id,
                zona,
                nueva_ruta.camiones_usados,
                nueva_ruta.suma_gravedad,
                es_recalculo=True
            )
            
            return nueva_ruta
        else:
            logger.error(f"❌ Error al generar nueva ruta durante recálculo de zona {zona}")
            return None
    
    def evaluar_necesidad_recalculo(
        self,
        db: Session,
        zona: str,
        nueva_gravedad: int
    ) -> bool:
        """
        Evalúa si es necesario recalcular ruta al agregar nueva incidencia
        
        Criterios:
        1. Hay rutas planeadas en la zona
        2. La nueva gravedad total supera significativamente el umbral
        3. La incidencia es de alta prioridad (gravedad >= 5)
        
        Args:
            db: Sesión de base de datos
            zona: Zona a evaluar
            nueva_gravedad: Gravedad de la nueva incidencia
            
        Returns:
            True si se debe recalcular, False si no
        """
        # Verificar si hay rutas planeadas
        rutas_planeadas = self.verificar_rutas_planeadas_zona(db, zona)
        
        if not rutas_planeadas:
            # No hay rutas planeadas, no es necesario recalcular
            return False
        
        # Calcular gravedad total (pendientes + asignadas a rutas planeadas)
        gravedad_total = self.calcular_gravedad_total_zona(db, zona, incluir_asignadas=True)
        umbral = self.obtener_umbral(db)
        
        # Criterios para recalcular:
        # 1. Incidencia de alta prioridad (animal muerto = 5 puntos)
        # 2. O suma total supera significativamente el umbral (> 1.5x)
        es_alta_prioridad = nueva_gravedad >= 5
        supera_significativamente = gravedad_total > (umbral * 1.5)
        
        if es_alta_prioridad or supera_significativamente:
            logger.info(
                f"📊 Evaluación recálculo zona {zona}: "
                f"gravedad_total={gravedad_total}, umbral={umbral}, "
                f"nueva_gravedad={nueva_gravedad}, "
                f"es_alta_prioridad={es_alta_prioridad}, "
                f"supera_significativamente={supera_significativamente}"
            )
            return True
        
        return False

