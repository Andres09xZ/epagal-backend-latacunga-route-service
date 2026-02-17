# 🔧 Solución al Problema de Generación de Rutas y Visualización

## 📋 Problema Identificado

### 1. **Las rutas NO se generan automáticamente**

**Causa Raíz**: Las rutas solo se generan cuando hay incidencias en estado `'validada'`, NO con incidencias en estado `'pendiente'`.

#### Flujo Actual del Sistema:

```
1. Crear Incidencia → estado = 'pendiente' (gravedad NO cuenta para umbral)
2. Validar Incidencia → estado = 'validada' (gravedad SÍ cuenta para umbral) ✅
3. Verificar Umbral → Si suma_gravedad > 20 → Generar Ruta Automáticamente
```

#### Código Relevante:

**En `app/services/incidencia_service.py` (línea 283-289)**:
```python
def calcular_suma_gravedad_zona(db: Session, zona: str) -> int:
    """Solo cuenta incidencias VALIDADAS"""
    incidencias = IncidenciaService.obtener_incidencias_validadas_por_zona(db, zona)
    return sum(inc.gravedad for inc in incidencias)
```

**En `app/services/ruta_service.py` (línea 247)**:
```python
def generar_ruta_automatica(self, db: Session, zona: str):
    """Solo usa incidencias con estado='validada'"""
    incidencias = db.query(Incidencia).filter(
        Incidencia.zona == zona,
        Incidencia.estado == 'validada'  # ← Aquí está la clave
    ).all()
```

### 2. **El dashboard NO muestra la polilínea de la ruta**

**Causa**: El endpoint del backend SÍ devuelve el campo `polyline`, pero el dashboard no lo renderizaba en un mapa.

---

## ✅ Soluciones Implementadas

### **Solución 1: Entender el Flujo Correcto**

**PASO A PASO para generar una ruta:**

```bash
# 1. Crear incidencias (estado: pendiente)
curl -X POST http://localhost:8000/api/incidencias/ \
  -H "Content-Type: application/json" \
  -d '{
    "tipo": "animal_muerto",
    "descripcion": "Perro muerto en vía",
    "lat": -0.9344,
    "lon": -78.6000
  }'
```

**Resultado**: Incidencia creada con:
- `estado = 'pendiente'`
- `gravedad = 5` (auto-asignada según tipo)
- `zona = 'oriental'` (auto-detectada por coordenadas)

```bash
# 2. VALIDAR la incidencia (CRÍTICO)
curl -X POST http://localhost:8000/api/incidencias/1/validate
```

**Resultado**: 
- Incidencia cambia a `estado = 'validada'`
- Se verifica el umbral de la zona
- **Si suma_gravedad > 20 → SE GENERA LA RUTA AUTOMÁTICAMENTE** 🚀

```bash
# 3. Repetir hasta superar el umbral
# Zona Oriental necesita:
#   - 5 incidencias de tipo "animal_muerto" (5 puntos c/u = 25 total) ✅
#   - O 21 incidencias de tipo "acopio" (1 punto c/u = 21 total) ✅
```

---

### **Ejemplo Práctico: Generar Ruta en Zona Oriental**

```json
// 1. Crear 5 incidencias de alta prioridad
[
  {"tipo": "animal_muerto", "lat": -0.9344, "lon": -78.6000},  // 5 pts
  {"tipo": "animal_muerto", "lat": -0.9350, "lon": -78.6010},  // 5 pts
  {"tipo": "animal_muerto", "lat": -0.9360, "lon": -78.6020},  // 5 pts
  {"tipo": "animal_muerto", "lat": -0.9370, "lon": -78.6030},  // 5 pts
  {"tipo": "animal_muerto", "lat": -0.9380, "lon": -78.6040}   // 5 pts
]
// Total: 25 puntos > 20 umbral ✅

// 2. Validar cada incidencia
POST /api/incidencias/1/validate
POST /api/incidencias/2/validate
POST /api/incidencias/3/validate
POST /api/incidencias/4/validate
POST /api/incidencias/5/validate  ← Al validar esta, SE GENERA LA RUTA 🗺️

// 3. Verificar la ruta generada
GET /api/rutas/zona/oriental
```

---

### **Solución 2: Visualización de Polilínea en Dashboard**

**Cambios implementados:**

#### 1. **Agregado Leaflet.js al HTML** (`dashboard/index.html`)

```html
<!-- Leaflet CSS para mapas -->
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>

<!-- Leaflet JS -->
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
```

#### 2. **Función de Renderizado de Mapa** (`dashboard/app.js`)

```javascript
function renderRutaMap(ruta) {
    // Inicializar mapa Leaflet
    const map = L.map('rutaMap').setView([centerLat, centerLon], 13);
    
    // Agregar capa de OpenStreetMap
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
    
    // Decodificar polilínea (formato Google Polyline)
    const decodedCoords = decodePolyline(ruta.polyline);
    
    // Dibujar la polilínea
    const polyline = L.polyline(decodedCoords, {
        color: '#2196F3',
        weight: 5,
        opacity: 0.7
    }).addTo(map);
    
    // Ajustar zoom automáticamente
    map.fitBounds(polyline.getBounds());
    
    // Agregar marcadores para puntos
    ruta.puntos.forEach(punto => {
        const marker = L.marker([punto.lat, punto.lon]).addTo(map);
        marker.bindPopup(`Punto ${punto.secuencia}: ${punto.tipo_punto}`);
    });
}
```

#### 3. **Decodificador de Polilínea de Google**

```javascript
function decodePolyline(encoded) {
    // Algoritmo de decodificación de Google Polyline
    // Convierte string comprimido a array de coordenadas [lat, lon]
    const coords = [];
    let index = 0, lat = 0, lng = 0;
    
    while (index < encoded.length) {
        // Decodificar latitud y longitud
        // ... (algoritmo completo en el código)
    }
    
    return coords;
}
```

#### 4. **Estilos CSS para el Mapa** (`dashboard/styles.css`)

```css
.ruta-map-container {
    margin: 20px 0;
    padding: 15px;
    background: var(--light);
    border-radius: 8px;
}

#rutaMap {
    width: 100%;
    height: 400px;
    border-radius: 8px;
    border: 2px solid var(--border);
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
}
```

---

## 🧪 Cómo Probar la Solución

### **Opción 1: Usando el Script de Python**

```bash
# Crear incidencias de prueba
python preparar_datos_app.py
```

### **Opción 2: Usando curl manualmente**

```bash
# 1. Crear incidencias
for i in {1..5}; do
  curl -X POST http://localhost:8000/api/incidencias/ \
    -H "Content-Type: application/json" \
    -d "{
      \"tipo\": \"animal_muerto\",
      \"descripcion\": \"Incidencia de prueba $i\",
      \"lat\": -0.934$i,
      \"lon\": -78.600$i
    }"
done

# 2. Validar incidencias
for i in {1..5}; do
  curl -X POST http://localhost:8000/api/incidencias/$i/validate
done

# 3. Verificar ruta generada
curl http://localhost:8000/api/rutas/zona/oriental
```

### **Opción 3: Desde el Dashboard**

1. **Abrir Dashboard**: http://localhost:8080
2. **Login**: admin / admin123
3. **Ir a Tab "Incidencias"**:
   - Ver umbrales actuales (Oriental/Occidental)
   - Ver incidencias pendientes
4. **Validar Incidencias**:
   - Click en "✅ Validar" de cada incidencia pendiente
   - Cuando superes el umbral (20 pts), verás mensaje: *"🗺️ ¡Se generó la ruta #X!"*
5. **Ir a Tab "Rutas"**:
   - Ver la ruta recién generada
   - Click en "👁️ Ver Detalles"
6. **Ver Mapa Interactivo**:
   - 🗺️ Mapa con polilínea azul de la ruta
   - 🏢 Marcador verde: Depósito (inicio)
   - 📍 Marcadores azules: Incidencias
   - 🗑️ Marcador rojo: Botadero (fin)

---

## 📊 Resumen de Estados de Incidencia

| Estado | Cuenta para Umbral | Se puede validar | Se puede asignar a ruta |
|--------|-------------------|------------------|------------------------|
| `pendiente` | ❌ NO | ✅ SÍ | ❌ NO |
| `validada` | ✅ SÍ | ❌ NO | ✅ SÍ |
| `asignada` | ✅ SÍ | ❌ NO | ❌ NO (ya está en ruta) |
| `completada` | ✅ SÍ | ❌ NO | ❌ NO |
| `cancelada` | ❌ NO | ❌ NO | ❌ NO |

---

## 🎯 Verificación Final

### **1. Verificar Umbral Actual**

```bash
curl http://localhost:8000/api/incidencias/umbrales
```

**Respuesta esperada:**
```json
{
  "umbral": 20,
  "oriental": {
    "gravedad_acumulada": 25,
    "incidencias_validadas": 5,
    "porcentaje": 125.0,
    "falta": 0,
    "supera_umbral": true
  },
  "occidental": {
    "gravedad_acumulada": 0,
    "incidencias_validadas": 0,
    "porcentaje": 0.0,
    "falta": 20,
    "supera_umbral": false
  }
}
```

### **2. Verificar Ruta Generada**

```bash
curl http://localhost:8000/api/rutas/1
```

**Respuesta esperada:**
```json
{
  "id": 1,
  "zona": "oriental",
  "estado": "planeada",
  "suma_gravedad": 25,
  "camiones_usados": 1,
  "duracion_estimada": "00:45:00",
  "costo_total_metros": 12500,
  "polyline": "abcxyzPolylineEncodedString...",
  "puntos": [
    {
      "secuencia": 1,
      "tipo_punto": "deposito",
      "lat": -0.9340,
      "lon": -78.6180
    },
    {
      "secuencia": 2,
      "tipo_punto": "incidencia",
      "lat": -0.9344,
      "lon": -78.6000,
      "incidencia_id": 1,
      "tipo_incidencia": "animal_muerto",
      "gravedad": 5
    },
    // ... más puntos ...
    {
      "secuencia": 7,
      "tipo_punto": "botadero",
      "lat": -0.9450,
      "lon": -78.6200
    }
  ]
}
```

---

## 🚀 Conclusión

### ✅ **Problemas Resueltos:**

1. **Generación de Rutas**: Ahora entiendes que las incidencias DEBEN estar en estado `'validada'` para contar hacia el umbral.

2. **Visualización**: El dashboard ahora muestra:
   - 🗺️ Mapa interactivo con Leaflet
   - 🔵 Polilínea azul de la ruta optimizada
   - 📍 Marcadores con iconos personalizados (depósito, incidencias, botadero)
   - 💬 Popups con información detallada de cada punto

3. **Umbral Dinámico**: El dashboard muestra en tiempo real:
   - Gravedad acumulada por zona
   - Porcentaje del umbral alcanzado
   - Cuántos puntos faltan para generar ruta

### 📝 **Recuerda:**

- **Umbral por defecto**: 20 puntos
- **Incidencias válidas**: Solo las que están en estado `'validada'`
- **Zonas**: Oriental (lon > -78.6191) y Occidental (lon <= -78.6191)
- **Gravedad por tipo**:
  - `acopio`: 1 punto
  - `zona_critica`: 3 puntos
  - `animal_muerto`: 5 puntos

### 🎉 **Ahora Puedes:**

1. Crear incidencias sin especificar zona ni gravedad (auto-detectadas)
2. Validarlas desde el dashboard
3. Ver en tiempo real cuándo se supera el umbral
4. Visualizar las rutas generadas en un mapa interactivo con la polilínea completa

---

## 📚 Referencias

- **Leaflet Documentation**: https://leafletjs.com/
- **Google Polyline Algorithm**: https://developers.google.com/maps/documentation/utilities/polylinealgorithm
- **OSRM API**: http://project-osrm.org/docs/v5.5.1/api/

---

**Autor**: GitHub Copilot  
**Fecha**: 12 de enero de 2026  
**Proyecto**: EPAGAL - Sistema de Gestión de Incidencias
