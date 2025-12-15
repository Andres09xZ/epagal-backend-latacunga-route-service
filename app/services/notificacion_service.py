"""
Servicio de notificaciones para conductores y supervisores
"""
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class NotificacionService:
    """Servicio para gestión de notificaciones"""
    
    # En producción, esto se integraría con servicios reales como:
    # - Push notifications (Firebase, OneSignal)
    # - SMS (Twilio)
    # - Email (SendGrid)
    # - WebSocket para actualizaciones en tiempo real
    
    @staticmethod
    def notificar_nueva_ruta(
        ruta_id: int,
        zona: str,
        camiones_usados: int,
        suma_gravedad: int,
        es_recalculo: bool = False
    ) -> Dict:
        """
        Notifica a los conductores sobre una nueva ruta asignada
        
        Args:
            ruta_id: ID de la ruta generada
            zona: Zona de la ruta (oriental/occidental)
            camiones_usados: Número de camiones asignados
            suma_gravedad: Suma total de gravedad
            es_recalculo: True si es un recálculo de ruta existente
            
        Returns:
            Dict con información de la notificación enviada
        """
        tipo_notificacion = "RECÁLCULO DE RUTA" if es_recalculo else "NUEVA RUTA"
        
        mensaje = {
            "tipo": tipo_notificacion,
            "ruta_id": ruta_id,
            "zona": zona.upper(),
            "camiones": camiones_usados,
            "gravedad_total": suma_gravedad,
            "timestamp": datetime.utcnow().isoformat(),
            "urgencia": "ALTA" if es_recalculo else "NORMAL",
            "mensaje": (
                f"⚠️ {tipo_notificacion}: Se ha {'recalculado' if es_recalculo else 'generado'} "
                f"una ruta para zona {zona.upper()} con {suma_gravedad} puntos de gravedad. "
                f"Camiones asignados: {camiones_usados}. "
                f"Ruta ID: {ruta_id}"
            )
        }
        
        # Simular envío de notificación
        logger.info(
            f"📢 NOTIFICACIÓN ENVIADA a conductores de zona {zona}: "
            f"{mensaje['mensaje']}"
        )
        
        # En producción, aquí se enviaría la notificación real
        # Ejemplo:
        # - Firebase Cloud Messaging para apps móviles
        # - WebSocket para dashboard en tiempo real
        # - SMS para notificaciones críticas
        
        return mensaje
    
    @staticmethod
    def notificar_ruta_cancelada(
        ruta_id: int,
        zona: str,
        motivo: str = "Recálculo por nueva incidencia"
    ) -> Dict:
        """
        Notifica que una ruta planificada fue cancelada/reemplazada
        
        Args:
            ruta_id: ID de la ruta cancelada
            zona: Zona de la ruta
            motivo: Razón de la cancelación
            
        Returns:
            Dict con información de la notificación
        """
        mensaje = {
            "tipo": "RUTA_CANCELADA",
            "ruta_id": ruta_id,
            "zona": zona.upper(),
            "motivo": motivo,
            "timestamp": datetime.utcnow().isoformat(),
            "mensaje": (
                f"⚠️ La ruta {ruta_id} de zona {zona.upper()} ha sido cancelada. "
                f"Motivo: {motivo}. Espere nueva asignación."
            )
        }
        
        logger.warning(
            f"📢 NOTIFICACIÓN: Ruta {ruta_id} cancelada en zona {zona}. "
            f"Motivo: {motivo}"
        )
        
        return mensaje
    
    @staticmethod
    def notificar_incidencia_critica(
        incidencia_id: int,
        tipo: str,
        zona: str,
        gravedad: int,
        lat: float,
        lon: float
    ) -> Dict:
        """
        Notifica sobre una incidencia crítica (alta prioridad)
        
        Args:
            incidencia_id: ID de la incidencia
            tipo: Tipo de incidencia
            zona: Zona donde ocurrió
            gravedad: Nivel de gravedad
            lat, lon: Coordenadas
            
        Returns:
            Dict con información de la notificación
        """
        es_critica = gravedad >= 5 or tipo == "animal_muerto"
        
        mensaje = {
            "tipo": "INCIDENCIA_CRITICA" if es_critica else "NUEVA_INCIDENCIA",
            "incidencia_id": incidencia_id,
            "tipo_incidencia": tipo,
            "zona": zona.upper(),
            "gravedad": gravedad,
            "coordenadas": {"lat": lat, "lon": lon},
            "timestamp": datetime.utcnow().isoformat(),
            "mensaje": (
                f"🚨 INCIDENCIA {'CRÍTICA' if es_critica else 'NUEVA'}: "
                f"{tipo.replace('_', ' ').upper()} reportada en zona {zona.upper()}. "
                f"Gravedad: {gravedad}. ID: {incidencia_id}"
            )
        }
        
        if es_critica:
            logger.warning(
                f"🚨 INCIDENCIA CRÍTICA: {tipo} en zona {zona}, "
                f"gravedad {gravedad}, ID {incidencia_id}"
            )
        else:
            logger.info(
                f"📢 Nueva incidencia: {tipo} en zona {zona}, ID {incidencia_id}"
            )
        
        return mensaje
    
    @staticmethod
    def obtener_historial_notificaciones() -> List[Dict]:
        """
        Obtiene el historial de notificaciones enviadas
        
        En producción, esto consultaría una tabla de notificaciones en la BD
        Por ahora retorna un array vacío
        
        Returns:
            Lista de notificaciones enviadas
        """
        # En producción, esto consultaría la base de datos
        # SELECT * FROM notificaciones ORDER BY timestamp DESC
        return []
