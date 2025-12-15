"""
Servicio para integración con OSRM (Open Source Routing Machine)
Calcula rutas optimizadas para los camiones de recolección en Latacunga
"""
import requests
import os
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class OSRMService:
    """Servicio para calcular rutas usando OSRM"""
    
    def __init__(self, base_url: str = None):
        # Usar variable de entorno o valor por defecto
        if base_url is None:
            base_url = os.getenv("OSRM_URL", "http://localhost:5000")
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Backend-Latacunga-Clean/1.0'
        })
        logger.info(f"OSRM Service initialized with URL: {self.base_url}")
    
    def health_check(self) -> bool:
        """Verifica que OSRM esté disponible"""
        try:
            # OSRM no tiene endpoint /health, probamos con una ruta simple
            response = self.session.get(
                f"{self.base_url}/route/v1/driving/-78.613,-0.936;-78.614,-0.937",
                timeout=5
            )
            data = response.json()
            return data.get("code") == "Ok"
        except Exception as e:
            logger.error(f"OSRM no disponible: {e}")
            return False
    
    def calculate_route(
        self,
        coordinates: List[Tuple[float, float]],  # [(lon, lat), ...]
        overview: str = "full",
        geometries: str = "geojson",
        steps: bool = False
    ) -> Optional[Dict]:
        """
        Calcula una ruta entre múltiples puntos
        
        Args:
            coordinates: Lista de tuplas (lon, lat)
            overview: 'full', 'simplified' o 'false'
            geometries: 'geojson', 'polyline' o 'polyline6'
            steps: Si True, incluye instrucciones paso a paso
        
        Returns:
            Dict con la ruta, distancia (metros) y duración (segundos)
        """
        if len(coordinates) < 2:
            logger.error("Se necesitan al menos 2 puntos para calcular ruta")
            return None
        
        # Formato: lon,lat;lon,lat;...
        coords_str = ";".join([f"{lon},{lat}" for lon, lat in coordinates])
        url = f"{self.base_url}/route/v1/driving/{coords_str}"
        
        params = {
            "overview": overview,
            "geometries": geometries,
            "steps": str(steps).lower(),
            "annotations": "true"
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != "Ok":
                logger.error(f"Error en OSRM: {data.get('message')}")
                return None
            
            route = data["routes"][0]
            return {
                "distance": route["distance"],  # metros
                "duration": route["duration"],  # segundos
                "geometry": route["geometry"],
                "legs": route["legs"]
            }
        
        except Exception as e:
            logger.error(f"Error al calcular ruta: {e}")
            return None
    
    def calculate_distance_matrix(
        self,
        sources: List[Tuple[float, float]],  # [(lon, lat), ...]
        destinations: Optional[List[Tuple[float, float]]] = None
    ) -> Optional[Dict]:
        """
        Calcula matriz de distancias/tiempos entre múltiples puntos
        Útil para el solver de OR-Tools
        
        Args:
            sources: Puntos de origen
            destinations: Puntos de destino (si None, usa sources)
        
        Returns:
            Dict con matrices de distancia (metros) y duración (segundos)
        """
        if destinations is None:
            destinations = sources
        
        all_coords = sources + [d for d in destinations if d not in sources]
        coords_str = ";".join([f"{lon},{lat}" for lon, lat in all_coords])
        
        url = f"{self.base_url}/table/v1/driving/{coords_str}"
        
        # Índices de sources y destinations
        source_indices = ";".join(str(i) for i in range(len(sources)))
        
        if destinations == sources:
            dest_indices = source_indices
        else:
            dest_indices = ";".join(str(i) for i in range(len(sources), len(all_coords)))
        
        params = {
            "sources": source_indices,
            "destinations": dest_indices,
            "annotations": "distance,duration"
        }
        
        try:
            response = self.session.get(url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != "Ok":
                logger.error(f"Error en matriz OSRM: {data.get('message')}")
                return None
            
            return {
                "distances": data["distances"],  # matriz en metros
                "durations": data["durations"]   # matriz en segundos
            }
        
        except Exception as e:
            logger.error(f"Error al calcular matriz: {e}")
            return None
    
    def get_nearest_road(
        self,
        lon: float,
        lat: float,
        number: int = 1
    ) -> Optional[Dict]:
        """
        Encuentra el punto más cercano en la red vial
        Útil para "snapping" de coordenadas GPS a carreteras reales
        
        Args:
            lon: Longitud
            lat: Latitud
            number: Número de puntos cercanos a retornar
        
        Returns:
            Dict con waypoints más cercanos
        """
        url = f"{self.base_url}/nearest/v1/driving/{lon},{lat}"
        params = {"number": number}
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != "Ok":
                return None
            
            return {
                "waypoints": data["waypoints"]
            }
        
        except Exception as e:
            logger.error(f"Error al buscar punto cercano: {e}")
            return None
    
    def optimize_trip(
        self,
        coordinates: List[Tuple[float, float]],
        source: str = "first",  # 'first', 'any' o índice
        destination: str = "last",  # 'last', 'any' o índice
        roundtrip: bool = True
    ) -> Optional[Dict]:
        """
        Optimiza el orden de visita de puntos (Traveling Salesman Problem)
        
        Args:
            coordinates: Lista de puntos a visitar
            source: Punto de inicio ('first', 'any' o índice numérico)
            destination: Punto final ('last', 'any' o índice numérico)
            roundtrip: Si True, regresa al punto de inicio
        
        Returns:
            Dict con ruta optimizada, distancia, duración y orden de visita
        """
        coords_str = ";".join([f"{lon},{lat}" for lon, lat in coordinates])
        url = f"{self.base_url}/trip/v1/driving/{coords_str}"
        
        params = {
            "source": source,
            "destination": destination,
            "roundtrip": str(roundtrip).lower(),
            "overview": "full",
            "geometries": "geojson"
        }
        
        try:
            response = self.session.get(url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != "Ok":
                logger.error(f"Error en optimización: {data.get('message')}")
                return None
            
            trip = data["trips"][0]
            return {
                "distance": trip["distance"],  # metros
                "duration": trip["duration"],  # segundos
                "geometry": trip["geometry"],
                "waypoint_order": [wp["waypoint_index"] for wp in data["waypoints"]]
            }
        
        except Exception as e:
            logger.error(f"Error al optimizar trip: {e}")
            return None
    
    def match_gps_trace(
        self,
        coordinates: List[Tuple[float, float]],
        timestamps: Optional[List[int]] = None,
        radiuses: Optional[List[int]] = None
    ) -> Optional[Dict]:
        """
        Ajusta una traza GPS a las carreteras (map matching)
        Útil para limpiar datos GPS ruidosos
        
        Args:
            coordinates: Lista de puntos GPS
            timestamps: Timestamps Unix opcionales
            radiuses: Radio de búsqueda por punto (metros)
        
        Returns:
            Dict con la ruta ajustada a las carreteras
        """
        coords_str = ";".join([f"{lon},{lat}" for lon, lat in coordinates])
        url = f"{self.base_url}/match/v1/driving/{coords_str}"
        
        params = {
            "overview": "full",
            "geometries": "geojson"
        }
        
        if timestamps:
            params["timestamps"] = ";".join(str(t) for t in timestamps)
        
        if radiuses:
            params["radiuses"] = ";".join(str(r) for r in radiuses)
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != "Ok":
                logger.error(f"Error en map matching: {data.get('message')}")
                return None
            
            matching = data["matchings"][0]
            return {
                "distance": matching["distance"],
                "duration": matching["duration"],
                "geometry": matching["geometry"],
                "confidence": matching.get("confidence", 0)
            }
        
        except Exception as e:
            logger.error(f"Error en map matching: {e}")
            return None


# Instancia global del servicio
osrm_service = OSRMService()


# Funciones de utilidad específicas para Latacunga

def calcular_ruta_recoleccion(
    incidencias: List[Dict],
    deposito: Tuple[float, float] = (-78.613, -0.936),
    botadero: Tuple[float, float] = (-78.663, -0.949)
) -> Optional[Dict]:
    """
    Calcula la ruta completa de recolección:
    Depósito -> Incidencias -> Botadero
    
    Args:
        incidencias: Lista de dict con 'lon' y 'lat'
        deposito: Coordenadas del depósito (lon, lat)
        botadero: Coordenadas del botadero (lon, lat)
    
    Returns:
        Dict con la ruta completa y estadísticas
    """
    # Construir secuencia: depósito + incidencias + botadero
    coordinates = [deposito]
    coordinates.extend([(inc['lon'], inc['lat']) for inc in incidencias])
    coordinates.append(botadero)
    
    resultado = osrm_service.calculate_route(coordinates)
    
    if resultado:
        resultado['num_incidencias'] = len(incidencias)
        resultado['num_paradas'] = len(coordinates)
        resultado['distancia_km'] = round(resultado['distance'] / 1000, 2)
        resultado['duracion_minutos'] = round(resultado['duration'] / 60, 1)
    
    return resultado


def obtener_matriz_distancias_zona(
    puntos: List[Dict]
) -> Optional[List[List[float]]]:
    """
    Obtiene matriz de distancias entre puntos para el solver
    
    Args:
        puntos: Lista de dict con 'lon' y 'lat'
    
    Returns:
        Matriz de distancias en metros
    """
    coordinates = [(p['lon'], p['lat']) for p in puntos]
    resultado = osrm_service.calculate_distance_matrix(coordinates)
    
    return resultado['distances'] if resultado else None
