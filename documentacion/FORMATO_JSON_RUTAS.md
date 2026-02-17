# Formato JSON del Endpoint de Rutas

## 📍 Endpoint: `GET /api/rutas/{ruta_id}`

### Ejemplo de Respuesta Completa:

```json
{
  "id": 1,
  "zona": "oriental",
  "estado": "planeada",
  "suma_gravedad": 22,
  "camiones_usados": 1,
  "duracion_estimada": "0:22:55.400000",
  "costo_total_metros": 13233.5,
  "fecha_generacion": "2026-01-13T00:15:23.495747",
  "puntos": [
    {
      "id": 1,
      "secuencia": 1,
      "tipo_punto": "deposito",
      "lat": -0.936,
      "lon": -78.613,
      "tipo_camion": "posterior",
      "camion_id": "POSTERIOR-1",
      "llegada_estimada": "2026-01-13T00:15:23.495747",
      "tiempo_servicio": "0:05:00",
      "carga_acumulada": 0
    },
    {
      "id": 2,
      "secuencia": 2,
      "tipo_punto": "incidencia",
      "lat": -0.92,
      "lon": -78.61,
      "tipo_camion": "posterior",
      "camion_id": "POSTERIOR-1",
      "llegada_estimada": "2026-01-13T00:20:23.495747",
      "tiempo_servicio": "0:15:00",
      "carga_acumulada": 5,
      "incidencia_id": 1,
      "tipo_incidencia": "animal_muerto",
      "gravedad": 5,
      "descripcion": "Animal muerto - Norte 1",
      "foto_url": null,
      "estado_incidencia": "asignada"
    },
    {
      "id": 3,
      "secuencia": 3,
      "tipo_punto": "incidencia",
      "lat": -0.921,
      "lon": -78.611,
      "tipo_camion": "posterior",
      "camion_id": "POSTERIOR-1",
      "llegada_estimada": "2026-01-13T00:35:23.495747",
      "tiempo_servicio": "0:15:00",
      "carga_acumulada": 8,
      "incidencia_id": 2,
      "tipo_incidencia": "zona_critica",
      "gravedad": 3,
      "descripcion": "Zona crítica - Norte 2",
      "foto_url": null,
      "estado_incidencia": "asignada"
    },
    {
      "id": 4,
      "secuencia": 4,
      "tipo_punto": "incidencia",
      "lat": -0.922,
      "lon": -78.612,
      "tipo_camion": "posterior",
      "camion_id": "POSTERIOR-1",
      "llegada_estimada": "2026-01-13T00:50:23.495747",
      "tiempo_servicio": "0:15:00",
      "carga_acumulada": 11,
      "incidencia_id": 3,
      "tipo_incidencia": "zona_critica",
      "gravedad": 3,
      "descripcion": "Zona crítica - Norte 3",
      "foto_url": null,
      "estado_incidencia": "asignada"
    },
    {
      "id": 5,
      "secuencia": 5,
      "tipo_punto": "incidencia",
      "lat": -0.923,
      "lon": -78.613,
      "tipo_camion": "posterior",
      "camion_id": "POSTERIOR-1",
      "llegada_estimada": "2026-01-13T01:05:23.495747",
      "tiempo_servicio": "0:15:00",
      "carga_acumulada": 16,
      "incidencia_id": 4,
      "tipo_incidencia": "animal_muerto",
      "gravedad": 5,
      "descripcion": "Animal muerto - Norte 4",
      "foto_url": null,
      "estado_incidencia": "asignada"
    },
    {
      "id": 6,
      "secuencia": 6,
      "tipo_punto": "incidencia",
      "lat": -0.924,
      "lon": -78.614,
      "tipo_camion": "posterior",
      "camion_id": "POSTERIOR-1",
      "llegada_estimada": "2026-01-13T01:20:23.495747",
      "tiempo_servicio": "0:15:00",
      "carga_acumulada": 19,
      "incidencia_id": 5,
      "tipo_incidencia": "zona_critica",
      "gravedad": 3,
      "descripcion": "Zona crítica - Norte 5",
      "foto_url": null,
      "estado_incidencia": "asignada"
    },
    {
      "id": 7,
      "secuencia": 7,
      "tipo_punto": "incidencia",
      "lat": -0.925,
      "lon": -78.615,
      "tipo_camion": "posterior",
      "camion_id": "POSTERIOR-1",
      "llegada_estimada": "2026-01-13T01:35:23.495747",
      "tiempo_servicio": "0:15:00",
      "carga_acumulada": 22,
      "incidencia_id": 6,
      "tipo_incidencia": "zona_critica",
      "gravedad": 3,
      "descripcion": "Zona crítica - Norte 6",
      "foto_url": null,
      "estado_incidencia": "asignada"
    },
    {
      "id": 8,
      "secuencia": 8,
      "tipo_punto": "botadero",
      "lat": -0.949,
      "lon": -78.663,
      "tipo_camion": "posterior",
      "camion_id": "POSTERIOR-1",
      "llegada_estimada": "2026-01-13T01:50:23.495747",
      "tiempo_servicio": "0:10:00",
      "carga_acumulada": 22
    }
  ],
  "polyline": "r~qkAx~{mH~@FpACzAGbAOt@QlAg@lAu@p@k@`Am@nCuBfAs@j@Yf@OfBQtAAlACfA?l@?\\@vAHb@F`AZr@`@x@r@jBpBbAtA~@lAfAnBfAzB`@fAZfAVhALr@Jr@DdB?xBGlAKx@MbAa@tB_@rAk@nAy@~@_A|@_Av@qBvAoDpB"
}
```

---

## 🔍 Descripción de Campos:

### **Nivel Superior (Información de Ruta)**

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `id` | `int` | ID único de la ruta | `1` |
| `zona` | `string` | Zona geográfica | `"oriental"` o `"occidental"` |
| `estado` | `string` | Estado actual de la ruta | `"planeada"`, `"en_ejecucion"`, `"completada"` |
| `suma_gravedad` | `int` | Puntos totales de gravedad | `22` |
| `camiones_usados` | `int` | Cantidad de camiones asignados | `1` |
| `duracion_estimada` | `string` | Duración total en formato HH:MM:SS | `"0:22:55.400000"` |
| `costo_total_metros` | `float` | Distancia total en metros | `13233.5` |
| `fecha_generacion` | `string` | Timestamp ISO 8601 de creación | `"2026-01-13T00:15:23.495747"` |
| `puntos` | `array` | Lista de puntos de la ruta (ver abajo) | `[...]` |
| `polyline` | `string` | **Polilínea codificada en formato Google Polyline** | `"r~qkAx~{mH~@F..."` |

---

### **Objeto `puntos[]` (Cada Punto de la Ruta)**

#### Campos Comunes (Todos los Tipos de Punto):

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `id` | `int` | ID del detalle de ruta | `2` |
| `secuencia` | `int` | Orden de visita (1, 2, 3...) | `2` |
| `tipo_punto` | `string` | Tipo de punto | `"deposito"`, `"incidencia"`, `"botadero"` |
| `lat` | `float` | Latitud del punto | `-0.92` |
| `lon` | `float` | Longitud del punto | `-78.61` |
| `tipo_camion` | `string` | Tipo de camión asignado | `"posterior"` o `"lateral"` |
| `camion_id` | `string` | Identificador del camión | `"POSTERIOR-1"` |
| `llegada_estimada` | `string` | Timestamp ISO 8601 de llegada | `"2026-01-13T00:20:23.495747"` |
| `tiempo_servicio` | `string` | Tiempo de servicio en formato HH:MM:SS | `"0:15:00"` |
| `carga_acumulada` | `int` | Puntos de gravedad acumulados hasta este punto | `5` |

#### Campos Adicionales (Solo para `tipo_punto: "incidencia"`):

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `incidencia_id` | `int` | ID de la incidencia | `1` |
| `tipo_incidencia` | `string` | Tipo de incidencia | `"animal_muerto"`, `"zona_critica"`, `"acopio"` |
| `gravedad` | `int` | Puntos de gravedad | `5`, `3`, `1` |
| `descripcion` | `string` | Descripción de la incidencia | `"Animal muerto - Norte 1"` |
| `foto_url` | `string` o `null` | URL de la foto | `null` o `"https://..."` |
| `estado_incidencia` | `string` | Estado de la incidencia | `"asignada"`, `"completada"` |

---

## 🗺️ **CAMPO CLAVE: `polyline`**

### ¿Qué es?
Es una **cadena codificada** que representa la geometría completa de la ruta usando el **algoritmo de Google Polyline**.

### Ejemplo:
```json
"polyline": "r~qkAx~{mH~@FpACzAGbAOt@QlAg@lAu@p@k@`Am@nCuBfAs@j@Yf@OfBQtAAlACfA?l@?\\@vAHb@F`AZr@`@x@r@jBpBbAtA~@lAfAnBfAzB`@fAZfAVhALr@Jr@DdB?xBGlAKx@MbAa@tB_@rAk@nAy@~@_A|@_Av@qBvAoDpB"
```

### ¿Cómo se usa en la App Móvil?

#### **Para Flutter (Dart):**
```dart
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:flutter_polyline_points/flutter_polyline_points.dart';

// Decodificar polyline
List<LatLng> decodePolyline(String polyline) {
  PolylinePoints polylinePoints = PolylinePoints();
  List<PointLatLng> result = polylinePoints.decodePolyline(polyline);
  return result.map((point) => LatLng(point.latitude, point.longitude)).toList();
}

// Usar en el mapa
List<LatLng> routeCoordinates = decodePolyline(response['polyline']);

Polyline polyline = Polyline(
  polylineId: PolylineId('ruta_1'),
  color: Colors.blue,
  width: 5,
  points: routeCoordinates,
);
```

#### **Para React Native (JavaScript):**
```javascript
import Polyline from '@mapbox/polyline';

// Decodificar polyline
const decodedCoords = Polyline.decode(response.polyline);

// Convertir a formato lat/lng
const coordinates = decodedCoords.map(coord => ({
  latitude: coord[0],
  longitude: coord[1]
}));

// Usar en MapView
<Polyline
  coordinates={coordinates}
  strokeColor="#0000FF"
  strokeWidth={5}
/>
```

---

## 🚨 **Problema Común: Polyline No Se Pinta**

### Posibles Causas:

1. **Formato incorrecto**: El polyline está vacío o mal codificado
   - ✅ Verificar: `response.polyline` no debe ser `""`
   - ✅ Verificar logs del backend para errores de OSRM

2. **Orden de coordenadas invertido**: Algunas librerías esperan [lng, lat] en lugar de [lat, lng]
   - ✅ Google Polyline usa [lat, lng]
   - ✅ OSRM retorna [lng, lat] pero ya está convertido

3. **Librería de decodificación incorrecta**:
   - ✅ Usar `@mapbox/polyline` (JavaScript)
   - ✅ Usar `flutter_polyline_points` (Flutter)
   - ✅ NO intentar decodificar manualmente

4. **Coordenadas fuera del viewport**:
   - ✅ Ajustar el zoom del mapa para incluir toda la ruta
   - ✅ Usar `fitToCoordinates()` después de pintar

---

## ✅ **Verificación Rápida**

### Probar Polyline en Herramienta Online:
Copia el string del `polyline` y pruébalo en:
- https://developers.google.com/maps/documentation/utilities/polylineutility

### Ejemplo de Test:
```bash
curl http://localhost:8000/api/rutas/1 | jq '.polyline'
```

Si devuelve `""` (vacío), el problema está en el backend (OSRM no está respondiendo).

Si devuelve un string largo como `"r~qkAx~{mH~@F..."`, el problema está en la app móvil (decodificación).

---

## 📱 **Código de Ejemplo Completo para App Móvil**

### Flutter:
```dart
Future<void> cargarRuta(int rutaId) async {
  final response = await http.get(Uri.parse('http://API_URL/api/rutas/$rutaId'));
  final data = jsonDecode(response.body);
  
  // Decodificar polyline
  List<LatLng> routeCoords = decodePolyline(data['polyline']);
  
  // Agregar marcadores de puntos
  for (var punto in data['puntos']) {
    markers.add(Marker(
      markerId: MarkerId('punto_${punto['id']}'),
      position: LatLng(punto['lat'], punto['lon']),
      infoWindow: InfoWindow(
        title: punto['tipo_punto'],
        snippet: punto['descripcion'] ?? '',
      ),
    ));
  }
  
  // Dibujar polyline
  polylines.add(Polyline(
    polylineId: PolylineId('ruta_$rutaId'),
    color: Colors.blue,
    width: 5,
    points: routeCoords,
  ));
  
  setState(() {});
}
```

---

## 🔗 Más Información

- **Algoritmo Google Polyline**: https://developers.google.com/maps/documentation/utilities/polylinealgorithm
- **OSRM Documentation**: http://project-osrm.org/docs/v5.24.0/api/
- **Flutter Polyline Points**: https://pub.dev/packages/flutter_polyline_points
