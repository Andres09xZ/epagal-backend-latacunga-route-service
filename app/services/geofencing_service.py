# app/services/geofencing_service.py
from sqlalchemy.orm import Session
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import nearest_points
from geopy.distance import geodesic
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict
import json

from app.models.geofencing import (
    GeofenceAlert, GeofenceConfig, ZonaGeografica, 
    HistorialPosicion, EstadisticaGeofencing,
    TipoAlerta, SeveridadAlerta, EstadoAlerta
)
from app.schemas.geofencing import (
    PosicionGPS, ResultadoValidacionGPS, 
    GeofenceAlertCreate, GeofenceAlertResponse
)


class GeofencingService:
    """
    Servicio principal para procesamiento de geofencing
    """
    
    def __init__(self, db: Session):
        self.db = db
        self._cargar_configuracion()
    
    def _cargar_configuracion(self):
        """Cargar configuración desde base de datos"""
        configs = self.db.query(GeofenceConfig).filter(GeofenceConfig.activo == True).all()
        
        self.config = {}
        for conf in configs:
            self.config[conf.parametro] = conf.valor
        
        # Valores por defecto si no existen en BD
        self.config.setdefault('velocidad_maxima_kmh', 80)
        self.config.setdefault('distancia_desviacion_m', 500)
        self.config.setdefault('tiempo_parada_min', 15)
        self.config.setdefault('precision_minima_gps_m', 50)
        self.config.setdefault('velocidad_critica_kmh', 100)
        self.config.setdefault('umbral_recurrencia_alertas', 3)
    
    def procesar_posicion_gps(
        self, 
        posicion: PosicionGPS,
        conductor_id: int
    ) -> ResultadoValidacionGPS:
        """
        Procesar posición GPS y generar alertas si corresponde
        
        Args:
            posicion: Datos de posición GPS
            conductor_id: ID del conductor
        
        Returns:
            ResultadoValidacionGPS con alertas generadas
        """
        alertas_generadas = []
        
        # 1. Validar calidad de datos GPS
        calidad_gps = self._evaluar_calidad_gps(posicion)
        
        if calidad_gps == 'mala':
            alerta = self._crear_alerta_precision_baja(posicion, conductor_id)
            alertas_generadas.append(alerta)
        
        # 2. Guardar en historial
        self._guardar_historial_posicion(posicion, conductor_id, calidad_gps)
        
        # 3. Obtener información del conductor y su ruta
        from app.models import Conductor
        conductor = self.db.query(Conductor).filter(Conductor.id == conductor_id).first()
        
        if not conductor:
            return ResultadoValidacionGPS(
                valido=False,
                calidad_gps=calidad_gps,
                estado_conductor='desconocido'
            )
        
        # 4. Verificar velocidad
        if posicion.velocidad_kmh:
            alerta_velocidad = self._verificar_velocidad(
                posicion, 
                conductor_id
            )
            if alerta_velocidad:
                alertas_generadas.append(alerta_velocidad)
        
        # 5. Verificar desviación de ruta (si tiene ruta asignada)
        distancia_a_ruta = None
        en_zona_correcta = True
        
        if hasattr(conductor, 'ruta_actual') and conductor.ruta_actual:
            distancia_a_ruta, alerta_desviacion = self._verificar_desviacion_ruta(
                posicion,
                conductor.ruta_actual,
                conductor_id
            )
            
            if alerta_desviacion:
                alertas_generadas.append(alerta_desviacion)
        
        # 6. Verificar zona geográfica
        alerta_zona = self._verificar_zona_geografica(
            posicion,
            conductor.zona_asignada if hasattr(conductor, 'zona_asignada') else None,
            conductor_id
        )
        
        if alerta_zona:
            alertas_generadas.append(alerta_zona)
            en_zona_correcta = False
        
        # 7. Verificar paradas prolongadas
        alerta_parada = self._verificar_parada_prolongada(
            posicion,
            conductor_id,
            conductor
        )
        
        if alerta_parada:
            alertas_generadas.append(alerta_parada)
        
        # 8. Verificar anomalías temporales
        alerta_temporal = self._verificar_salto_temporal(
            posicion,
            conductor_id
        )
        
        if alerta_temporal:
            alertas_generadas.append(alerta_temporal)
        
        # 9. Determinar estado del conductor
        estado_conductor = self._determinar_estado_conductor(
            posicion,
            alertas_generadas,
            distancia_a_ruta
        )
        
        return ResultadoValidacionGPS(
            valido=True,
            alertas_generadas=[GeofenceAlertResponse.from_orm(a) for a in alertas_generadas],
            distancia_a_ruta_m=distancia_a_ruta,
            en_zona_correcta=en_zona_correcta,
            calidad_gps=calidad_gps,
            recomendaciones=self._generar_recomendaciones(alertas_generadas),
            estado_conductor=estado_conductor
        )
    
    def _evaluar_calidad_gps(self, posicion: PosicionGPS) -> str:
        """
        Evaluar calidad de señal GPS
        
        Returns:
            'buena', 'aceptable' o 'mala'
        """
        if not posicion.precision_m:
            return 'aceptable'
        
        if posicion.precision_m <= 20:
            return 'buena'
        elif posicion.precision_m <= self.config['precision_minima_gps_m']:
            return 'aceptable'
        else:
            return 'mala'
    
    def _verificar_velocidad(
        self, 
        posicion: PosicionGPS,
        conductor_id: int
    ) -> Optional[GeofenceAlert]:
        """
        Verificar si la velocidad excede límites
        """
        velocidad_max = self.config['velocidad_maxima_kmh']
        velocidad_critica = self.config['velocidad_critica_kmh']
        
        if posicion.velocidad_kmh <= velocidad_max:
            return None
        
        # Determinar severidad
        exceso = posicion.velocidad_kmh - velocidad_max
        
        if posicion.velocidad_kmh >= velocidad_critica:
            severidad = SeveridadAlerta.CRITICAL
            descripcion = f"Velocidad crítica: {posicion.velocidad_kmh:.1f} km/h (límite: {velocidad_max} km/h, exceso: {exceso:.1f} km/h)"
        else:
            severidad = SeveridadAlerta.WARNING
            descripcion = f"Velocidad excesiva: {posicion.velocidad_kmh:.1f} km/h (límite: {velocidad_max} km/h, exceso: {exceso:.1f} km/h)"
        
        # Verificar recurrencia
        contador_recurrencias = self._contar_alertas_recientes(
            conductor_id,
            TipoAlerta.VELOCIDAD_EXCESIVA,
            minutos=30
        )
        
        if contador_recurrencias >= self.config['umbral_recurrencia_alertas']:
            severidad = SeveridadAlerta.CRITICAL
            descripcion += f" | RECURRENTE: {contador_recurrencias + 1} veces en 30 min"
        
        alerta = GeofenceAlert(
            conductor_id=conductor_id,
            tipo=TipoAlerta.VELOCIDAD_EXCESIVA.value,
            severidad=severidad.value,
            latitud=posicion.latitud,
            longitud=posicion.longitud,
            ubicacion=f'POINT({posicion.longitud} {posicion.latitud})',
            velocidad_actual_kmh=posicion.velocidad_kmh,
            velocidad_maxima_kmh=velocidad_max,
            descripcion=descripcion,
            contador_recurrencias=contador_recurrencias + 1,
            timestamp=posicion.timestamp
        )
        
        self.db.add(alerta)
        self.db.commit()
        self.db.refresh(alerta)
        
        return alerta
    
    def _verificar_desviacion_ruta(
        self,
        posicion: PosicionGPS,
        ruta,
        conductor_id: int
    ) -> Tuple[float, Optional[GeofenceAlert]]:
        """
        Verificar si el conductor se desvió de la ruta planificada
        
        Returns:
            (distancia_minima_metros, alerta_o_none)
        """
        # Crear punto actual
        punto_actual = Point(posicion.longitud, posicion.latitud)
        
        # Obtener puntos de la ruta (incidencias)
        puntos_ruta = []
        for incidencia in ruta.incidencias:
            puntos_ruta.append((incidencia.longitud, incidencia.latitud))
        
        if len(puntos_ruta) < 2:
            return 0, None
        
        # Crear LineString de la ruta
        linea_ruta = LineString(puntos_ruta)
        
        # Encontrar punto más cercano en la ruta
        punto_proyectado = linea_ruta.interpolate(linea_ruta.project(punto_actual))
        
        # Calcular distancia real en metros
        distancia_m = geodesic(
            (posicion.latitud, posicion.longitud),
            (punto_proyectado.y, punto_proyectado.x)
        ).meters
        
        # Verificar si excede umbral
        umbral = self.config['distancia_desviacion_m']
        
        if distancia_m <= umbral:
            return distancia_m, None
        
        # Generar alerta
        contador_recurrencias = self._contar_alertas_recientes(
            conductor_id,
            TipoAlerta.DESVIACION_RUTA,
            minutos=15
        )
        
        if contador_recurrencias >= 2:
            severidad = SeveridadAlerta.CRITICAL
        else:
            severidad = SeveridadAlerta.WARNING
        
        descripcion = f"Desviación de ruta: {distancia_m:.0f} metros (umbral: {umbral:.0f} m)"
        
        if contador_recurrencias > 0:
            descripcion += f" | Desviación recurrente ({contador_recurrencias + 1}x)"
        
        alerta = GeofenceAlert(
            conductor_id=conductor_id,
            tipo=TipoAlerta.DESVIACION_RUTA.value,
            severidad=severidad.value,
            latitud=posicion.latitud,
            longitud=posicion.longitud,
            ubicacion=f'POINT({posicion.longitud} {posicion.latitud})',
            distancia_desviacion_m=distancia_m,
            descripcion=descripcion,
            contador_recurrencias=contador_recurrencias + 1,
            timestamp=posicion.timestamp
        )
        
        self.db.add(alerta)
        self.db.commit()
        self.db.refresh(alerta)
        
        return distancia_m, alerta
    
    def _verificar_zona_geografica(
        self,
        posicion: PosicionGPS,
        zona_asignada: Optional[str],
        conductor_id: int
    ) -> Optional[GeofenceAlert]:
        """
        Verificar si el conductor está en la zona correcta
        """
        if not zona_asignada:
            return None
        
        # Obtener zona asignada
        zona = self.db.query(ZonaGeografica).filter(
            ZonaGeografica.nombre == zona_asignada,
            ZonaGeografica.activa == True
        ).first()
        
        if not zona:
            return None
        
        # Crear punto actual
        from geoalchemy2.shape import to_shape
        punto_actual = Point(posicion.longitud, posicion.latitud)
        poligono_zona = to_shape(zona.geometria)
        
        # Verificar si está dentro de la zona
        if poligono_zona.contains(punto_actual):
            return None
        
        # Verificar si está en área de cobertura general
        zona_cobertura = self.db.query(ZonaGeografica).filter(
            ZonaGeografica.tipo == 'cobertura',
            ZonaGeografica.activa == True
        ).first()
        
        if zona_cobertura:
            poligono_cobertura = to_shape(zona_cobertura.geometria)
            
            if not poligono_cobertura.contains(punto_actual):
                # Fuera del área de cobertura total
                descripcion = f"Conductor fuera del área de cobertura de EPAGAL"
                tipo = TipoAlerta.FUERA_ZONA_COBERTURA
                severidad = SeveridadAlerta.CRITICAL
            else:
                # En área de cobertura pero zona incorrecta
                descripcion = f"Conductor en zona incorrecta. Asignado: {zona_asignada}"
                tipo = TipoAlerta.ZONA_INCORRECTA
                severidad = SeveridadAlerta.WARNING
        else:
            descripcion = f"Conductor fuera de zona asignada: {zona_asignada}"
            tipo = TipoAlerta.ZONA_INCORRECTA
            severidad = SeveridadAlerta.WARNING
        
        alerta = GeofenceAlert(
            conductor_id=conductor_id,
            tipo=tipo.value,
            severidad=severidad.value,
            latitud=posicion.latitud,
            longitud=posicion.longitud,
            ubicacion=f'POINT({posicion.longitud} {posicion.latitud})',
            descripcion=descripcion,
            metadata_json=json.dumps({"zona_asignada": zona_asignada}),
            timestamp=posicion.timestamp
        )
        
        self.db.add(alerta)
        self.db.commit()
        self.db.refresh(alerta)
        
        return alerta
    
    def _verificar_parada_prolongada(
        self,
        posicion: PosicionGPS,
        conductor_id: int,
        conductor
    ) -> Optional[GeofenceAlert]:
        """
        Verificar si el conductor está detenido por mucho tiempo
        """
        # Obtener última posición
        ultima_posicion = self.db.query(HistorialPosicion).filter(
            HistorialPosicion.conductor_id == conductor_id
        ).order_by(HistorialPosicion.timestamp.desc()).first()
        
        if not ultima_posicion:
            return None
        
        # Calcular tiempo detenido
        if posicion.velocidad_kmh and posicion.velocidad_kmh > 5:
            # Se está moviendo
            return None
        
        # Calcular distancia desde última posición
        distancia_m = geodesic(
            (ultima_posicion.latitud, ultima_posicion.longitud),
            (posicion.latitud, posicion.longitud)
        ).meters
        
        if distancia_m > 100:  # Se movió más de 100m
            return None
        
        # Calcular tiempo detenido
        tiempo_detenido_min = (posicion.timestamp - ultima_posicion.timestamp).total_seconds() / 60
        
        umbral_parada = self.config['tiempo_parada_min']
        
        if tiempo_detenido_min <= umbral_parada:
            return None
        
        # Verificar si está en ubicación de incidencia
        if hasattr(conductor, 'ruta_actual') and conductor.ruta_actual:
            for incidencia in conductor.ruta_actual.incidencias:
                dist_a_incidencia = geodesic(
                    (posicion.latitud, posicion.longitud),
                    (incidencia.latitud, incidencia.longitud)
                ).meters
                
                if dist_a_incidencia < 50:  # Dentro de 50m de incidencia
                    # Está trabajando, no generar alerta
                    return None
        
        # Generar alerta de parada prolongada
        descripcion = f"Parada prolongada: {tiempo_detenido_min:.0f} minutos (umbral: {umbral_parada:.0f} min)"
        
        alerta = GeofenceAlert(
            conductor_id=conductor_id,
            tipo=TipoAlerta.PARADA_PROLONGADA.value,
            severidad=SeveridadAlerta.INFO.value,
            latitud=posicion.latitud,
            longitud=posicion.longitud,
            ubicacion=f'POINT({posicion.longitud} {posicion.latitud})',
            duracion_parada_min=tiempo_detenido_min,
            descripcion=descripcion,
            timestamp=posicion.timestamp
        )
        
        self.db.add(alerta)
        self.db.commit()
        self.db.refresh(alerta)
        
        return alerta
    
    def _verificar_salto_temporal(
        self,
        posicion: PosicionGPS,
        conductor_id: int
    ) -> Optional[GeofenceAlert]:
        """
        Detectar saltos anómalos en posiciones GPS
        """
        # Obtener última posición
        ultima_posicion = self.db.query(HistorialPosicion).filter(
            HistorialPosicion.conductor_id == conductor_id
        ).order_by(HistorialPosicion.timestamp.desc()).first()
        
        if not ultima_posicion:
            return None
        
        # Calcular tiempo transcurrido
        tiempo_seg = (posicion.timestamp - ultima_posicion.timestamp).total_seconds()
        
        if tiempo_seg > 300:  # Más de 5 minutos, esperable
            return None
        
        # Calcular distancia
        distancia_km = geodesic(
            (ultima_posicion.latitud, ultima_posicion.longitud),
            (posicion.latitud, posicion.longitud)
        ).kilometers
        
        # Calcular velocidad implícita
        velocidad_implicita_kmh = (distancia_km / tiempo_seg) * 3600
        
        # Si la velocidad implícita es imposible (>150 km/h en ciudad)
        if velocidad_implicita_kmh > 150:
            descripcion = (
                f"Salto temporal anómalo: {distancia_km:.2f} km en {tiempo_seg:.0f} segundos "
                f"(requeriría {velocidad_implicita_kmh:.0f} km/h)"
            )
            
            alerta = GeofenceAlert(
                conductor_id=conductor_id,
                tipo=TipoAlerta.SALTO_TEMPORAL_ANOMALO.value,
                severidad=SeveridadAlerta.WARNING.value,
                latitud=posicion.latitud,
                longitud=posicion.longitud,
                ubicacion=f'POINT({posicion.longitud} {posicion.latitud})',
                descripcion=descripcion,
                metadata_json=json.dumps({
                    "distancia_km": distancia_km,
                    "tiempo_seg": tiempo_seg,
                    "velocidad_implicita_kmh": velocidad_implicita_kmh
                }),
                timestamp=posicion.timestamp
            )
            
            self.db.add(alerta)
            self.db.commit()
            self.db.refresh(alerta)
            
            return alerta
        
        return None
    
    def _crear_alerta_precision_baja(
        self,
        posicion: PosicionGPS,
        conductor_id: int
    ) -> GeofenceAlert:
        """Crear alerta de precisión GPS baja"""
        descripcion = f"Precisión GPS baja: {posicion.precision_m:.0f} metros (mínimo: {self.config['precision_minima_gps_m']:.0f} m)"
        
        alerta = GeofenceAlert(
            conductor_id=conductor_id,
            tipo=TipoAlerta.PRECISION_GPS_BAJA.value,
            severidad=SeveridadAlerta.INFO.value,
            latitud=posicion.latitud,
            longitud=posicion.longitud,
            ubicacion=f'POINT({posicion.longitud} {posicion.latitud})',
            precision_gps_m=posicion.precision_m,
            descripcion=descripcion,
            timestamp=posicion.timestamp
        )
        
        self.db.add(alerta)
        self.db.commit()
        self.db.refresh(alerta)
        
        return alerta
    
    def _guardar_historial_posicion(
        self,
        posicion: PosicionGPS,
        conductor_id: int,
        calidad_gps: str
    ):
        """Guardar posición en historial"""
        historial = HistorialPosicion(
            conductor_id=conductor_id,
            latitud=posicion.latitud,
            longitud=posicion.longitud,
            ubicacion=f'POINT({posicion.longitud} {posicion.latitud})',
            precision_m=posicion.precision_m,
            altitud_m=posicion.altitud_m,
            velocidad_kmh=posicion.velocidad_kmh,
            direccion_grados=posicion.direccion_grados,
            calidad_gps=calidad_gps,
            datos_validados=True,
            timestamp=posicion.timestamp
        )
        
        self.db.add(historial)
        self.db.commit()
    
    def _contar_alertas_recientes(
        self,
        conductor_id: int,
        tipo_alerta: TipoAlerta,
        minutos: int = 30
    ) -> int:
        """Contar alertas del mismo tipo en período reciente"""
        tiempo_limite = datetime.utcnow() - timedelta(minutes=minutos)
        
        count = self.db.query(GeofenceAlert).filter(
            GeofenceAlert.conductor_id == conductor_id,
            GeofenceAlert.tipo == tipo_alerta.value,
            GeofenceAlert.timestamp >= tiempo_limite
        ).count()
        
        return count
    
    def _determinar_estado_conductor(
        self,
        posicion: PosicionGPS,
        alertas: List[GeofenceAlert],
        distancia_a_ruta: Optional[float]
    ) -> str:
        """Determinar estado actual del conductor"""
        if not posicion.velocidad_kmh or posicion.velocidad_kmh < 5:
            return "detenido"
        
        if any(a.tipo == TipoAlerta.DESVIACION_RUTA.value for a in alertas):
            return "desviado"
        
        if any(a.severidad == SeveridadAlerta.CRITICAL.value for a in alertas):
            return "alerta_critica"
        
        if distancia_a_ruta and distancia_a_ruta < 100:
            return "en_ruta_normal"
        
        return "en_movimiento"
    
    def _generar_recomendaciones(
        self,
        alertas: List[GeofenceAlert]
    ) -> List[str]:
        """Generar recomendaciones basadas en alertas"""
        recomendaciones = []
        
        for alerta in alertas:
            if alerta.tipo == TipoAlerta.VELOCIDAD_EXCESIVA.value:
                recomendaciones.append("Reducir velocidad inmediatamente")
            elif alerta.tipo == TipoAlerta.DESVIACION_RUTA.value:
                recomendaciones.append("Regresar a la ruta asignada")
            elif alerta.tipo == TipoAlerta.PRECISION_GPS_BAJA.value:
                recomendaciones.append("Mejorar señal GPS (salir de edificios, túneles)")
            elif alerta.tipo == TipoAlerta.FUERA_ZONA_COBERTURA.value:
                recomendaciones.append("Contactar con operador - fuera de zona de servicio")
        
        return list(set(recomendaciones))  # Eliminar duplicados
