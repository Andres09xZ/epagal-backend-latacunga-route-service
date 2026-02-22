# HU — Navegación Paso a Paso con OSRM

**Versión:** 1.0  
**Fecha:** 2026-02-22  
**Estado:** ✅ Backend implementado y probado  
**Rama:** `main` — commit `feat: endpoint turn-by-turn GET /rutas/{id}/direcciones`

---

## 1. Historia de Usuario

> **Como operador**, quiero navegar paso a paso en la ruta con integración a OSRM para seguir el camino óptimo y llegar a cada punto sin perder tiempo.

### Criterios de Aceptación

| # | Criterio | Responsable | Estado |
|---|---|---|---|
| CA-1 | Botón visible "Iniciar navegación" en vista de rutas asignadas | Frontend | 🔲 Pendiente |
| CA-2 | Al presionar: mapa full-screen con ruta completa turn-by-turn | Frontend | 🔲 Pendiente |
| CA-3 | OSRM calcula ruta real desde GPS actual hasta siguiente punto | **Backend ✅** | ✅ Listo |
| CA-4 | Panel de instrucciones en tiempo real ("Gira a la derecha en 200m") | Frontend | 🔲 Pendiente |
| CA-5 | GPS actualiza posición del marcador en tiempo real (`navigator.geolocation`) | Frontend | 🔲 Pendiente |
| CA-6 | Al acercarse a punto (≤50m): resaltar como "actual", avanzar al siguiente | Frontend | 🔲 Pendiente |
| CA-7 | Sin conexión: mostrar ruta cacheada / mensaje "Sin conexión" | Frontend | 🔲 Pendiente |
| CA-8 | Botón "Finalizar navegación" para volver a vista normal | Frontend | 🔲 Pendiente |
| CA-9 | Orden de puntos estricto del backend — no se puede saltar | **Backend ✅** | ✅ Listo |
| CA-10 | UI responsive, prioridad móvil vertical, botones grandes, legible bajo sol | Frontend | 🔲 Pendiente |
| CA-11 | Tests E2E con mock de geolocalización | Frontend | 🔲 Pendiente |

---

## 2. Arquitectura Backend — Lo que ya existe

### 2.1 Endpoints disponibles para la navegación

| Método | URL | Descripción |
|---|---|---|
| `GET` | `/api/rutas/{id}` | Ruta completa con puntos ordenados y polyline |
| `GET` | `/api/rutas/{id}/navegacion` | Estado de navegación: punto actual, progreso, puntos completados |
| `GET` | `/api/rutas/{id}/direcciones` | **NUEVO ✅** Instrucciones turn-by-turn desde GPS actual |
| `POST` | `/api/rutas/{id}/incidencia/{inc_id}/completar` | Marca un punto como completado |
| `GET` | `/api/conductores/mis-rutas/actual` | Ruta actualmente asignada al conductor autenticado |

### 2.2 Flujo de datos Backend → Frontend

```
App inicia navegación
        ↓
GET /api/rutas/{id}
← Recibe: puntos[] ordenados + polyline completa de la ruta
        ↓
Renderizar mapa con todos los puntos y trazado
        ↓
[LOOP cada 3-5 segundos mientras navega]
        ↓
navigator.geolocation.getCurrentPosition()
← lat_actual, lon_actual del GPS del dispositivo
        ↓
GET /api/rutas/{id}/direcciones
  ?lat_actual={lat}&lon_actual={lon}&punto_destino_orden={N}
← instrucciones[], distancia_metros, duracion_segundos, geometry
        ↓
Actualizar panel de instrucciones
        ↓
¿Distancia al punto < 50m?
  SÍ → POST /api/rutas/{id}/incidencia/{inc_id}/completar
       Pasar al siguiente punto (orden N+1)
  NO → Continuar mostrando instrucciones actuales
        ↓
¿Todos los puntos completados?
  SÍ → Mostrar pantalla "Ruta finalizada 🎉"
  NO → Volver al LOOP
```

---

## 3. API Reference — Endpoints de Navegación

### 3.1 `GET /api/rutas/{id}` — Cargar ruta completa

Se llama **una vez** al iniciar la navegación para obtener todos los puntos y el trazado.

**URL:** `GET /api/rutas/{ruta_id}`  
**Auth:** Bearer Token

#### Response 200

```json
{
  "id": 6,
  "zona": "oriental",
  "estado": "planeada",
  "suma_gravedad": 24,
  "camiones_usados": 1,
  "duracion_estimada": "0:27:04",
  "costo_total_metros": 14517.2,
  "centroide_lat": -0.93275,
  "centroide_lon": -78.61375,
  "puntos": [
    { "secuencia": 1, "tipo_punto": "deposito",   "lat": -0.936,  "lon": -78.613 },
    { "secuencia": 2, "tipo_punto": "incidencia", "lat": -0.9345, "lon": -78.6155, "incidencia_id": 143 },
    { "secuencia": 3, "tipo_punto": "incidencia", "lat": -0.934,  "lon": -78.615,  "incidencia_id": 138 },
    { "secuencia": 4, "tipo_punto": "incidencia", "lat": -0.933,  "lon": -78.614,  "incidencia_id": 141 },
    { "secuencia": 5, "tipo_punto": "incidencia", "lat": -0.9325, "lon": -78.6135, "incidencia_id": 136 },
    { "secuencia": 6, "tipo_punto": "incidencia", "lat": -0.9315, "lon": -78.6125, "incidencia_id": 140 },
    { "secuencia": 7, "tipo_punto": "incidencia", "lat": -0.931,  "lon": -78.612,  "incidencia_id": 135 },
    { "secuencia": 8, "tipo_punto": "botadero",   "lat": -0.949,  "lon": -78.663  }
  ],
  "polyline": "..."
}
```

---

### 3.2 `GET /api/rutas/{id}/direcciones` — Turn-by-turn ⭐ NUEVO

Se llama **repetidamente** durante la navegación para obtener instrucciones actualizadas.

**URL:** `GET /api/rutas/{ruta_id}/direcciones`  
**Auth:** Bearer Token

#### Query Parameters

| Parámetro | Tipo | Requerido | Descripción |
|---|---|---|---|
| `lat_actual` | `float` | ✅ | Latitud GPS actual del dispositivo |
| `lon_actual` | `float` | ✅ | Longitud GPS actual del dispositivo |
| `punto_destino_orden` | `int` | ✅ | Número de orden del punto destino en la ruta |

#### Ejemplo de llamada

```
GET /api/rutas/6/direcciones?lat_actual=-0.9310&lon_actual=-78.6120&punto_destino_orden=2
```

#### Response 200 — Con OSRM disponible

```json
{
  "origen": { "lat": -0.9310, "lon": -78.6120 },
  "destino": {
    "orden": 2,
    "tipo_punto": "incidencia",
    "lat": -0.9345,
    "lon": -78.6155,
    "incidencia_id": 143
  },
  "distancia_metros": 1679.4,
  "duracion_segundos": 212.3,
  "geometry": {
    "type": "LineString",
    "coordinates": [[-78.611893, -0.931171], [-78.611806, -0.931125], "..."]
  },
  "instrucciones": [
    {
      "tipo": "depart",
      "modificador": "left",
      "texto": "Oriente",
      "distancia_metros": 147,
      "duracion_segundos": 23.3,
      "coordenada": { "lon": -78.611893, "lat": -0.931171 }
    },
    {
      "tipo": "turn",
      "modificador": "right",
      "texto": "San Salvador",
      "distancia_metros": 440.8,
      "duracion_segundos": 63.5,
      "coordenada": { "lon": -78.610608, "lat": -0.93117 }
    },
    {
      "tipo": "roundabout",
      "modificador": "right",
      "texto": "Marquez de Maenza",
      "distancia_metros": 6.5,
      "duracion_segundos": 0.9,
      "coordenada": { "lon": -78.610294, "lat": -0.936097 }
    },
    {
      "tipo": "arrive",
      "modificador": "right",
      "texto": "General Maldonado",
      "distancia_metros": 0,
      "duracion_segundos": 0,
      "coordenada": { "lon": -78.615536, "lat": -0.934373 }
    }
  ],
  "osrm_disponible": true
}
```

#### Response 200 — Sin OSRM (fallback)

```json
{
  "origen": { "lat": -0.9310, "lon": -78.6120 },
  "destino": { "orden": 2, "tipo_punto": "incidencia", "lat": -0.9345, "lon": -78.6155 },
  "distancia_metros": 450.2,
  "duracion_segundos": 162,
  "instrucciones": [],
  "osrm_disponible": false,
  "advertencia": "OSRM no disponible — distancia estimada por línea recta"
}
```

#### Tipos de instrucción OSRM (`tipo`)

| Valor | Significado para mostrar |
|---|---|
| `depart` | "Salir hacia..." |
| `turn` | "Gira a la [modificador]" |
| `roundabout` | "Tomar rotonda" |
| `exit roundabout` | "Salir de rotonda" |
| `arrive` | "Has llegado a tu destino" |
| `continue` | "Continuar recto" |
| `merge` | "Incorporarse" |
| `fork` | "Mantener [izquierda/derecha]" |

#### Modificadores (`modificador`) → Ícono

| Valor | Ícono sugerido |
|---|---|
| `left` | ⬅️ |
| `right` | ➡️ |
| `straight` | ⬆️ |
| `slight left` | ↖️ |
| `slight right` | ↗️ |
| `sharp left` | 🔙 |
| `sharp right` | ↪️ |
| `uturn` | 🔄 |

---

### 3.3 `GET /api/rutas/{id}/navegacion` — Estado de progreso

Consulta el estado actual de la ruta: cuántos puntos completados, cuál es el siguiente.

**URL:** `GET /api/rutas/{ruta_id}/navegacion`

#### Response 200

```json
{
  "ruta_id": 6,
  "zona": "oriental",
  "estado": "planeada",
  "navegacion": {
    "punto_actual": {
      "orden": 2,
      "tipo_punto": "incidencia",
      "lat": -0.9345,
      "lon": -78.6155,
      "completado": false
    },
    "punto_actual_index": 1,
    "total_puntos": 8,
    "puntos_completados": 1,
    "progreso_porcentaje": 12.5
  },
  "puntos": [...],
  "resumen": {
    "distancia_total_km": 14.52,
    "duracion_estimada": "0:27:04",
    "incidencias_totales": 6,
    "incidencias_completadas": 0
  }
}
```

---

### 3.4 `POST /api/rutas/{id}/incidencia/{inc_id}/completar` — Marcar punto visitado

Se llama cuando el operador llega a un punto (o automáticamente al entrar al radio de 50m).

**URL:** `POST /api/rutas/{ruta_id}/incidencia/{incidencia_id}/completar`

#### Response 200

```json
{
  "message": "Incidencia marcada como completada",
  "incidencia": {
    "id": 143,
    "tipo": "animal_muerto",
    "estado_anterior": "en_ejecucion",
    "estado_actual": "completada"
  },
  "progreso_ruta": {
    "ruta_id": 6,
    "incidencias_totales": 6,
    "incidencias_completadas": 1,
    "porcentaje": 16.7,
    "todas_completadas": false
  }
}
```

---

## 4. Guía de Implementación Frontend

### 4.1 Tecnologías recomendadas

| Componente | Tecnología |
|---|---|
| Mapa base | **Leaflet.js** + OpenStreetMap (gratuito, sin API key) |
| Geolocalización | `navigator.geolocation.watchPosition()` |
| Polyline en mapa | `L.polyline(coordinates)` de Leaflet |
| Decodificación polyline | Librería `@mapbox/polyline` si el backend devuelve formato Google |
| Íconos marcadores | Leaflet `DivIcon` personalizado (colores por estado) |
| Notificaciones | Web Notifications API o toast en pantalla |

---

### 4.2 Pantalla: Lista de Rutas Asignadas

```
┌─────────────────────────────────────────┐
│  🚛 Mis Rutas Asignadas                 │
│─────────────────────────────────────────│
│  ┌─────────────────────────────────┐   │
│  │  Ruta #6 — Zona Oriental        │   │
│  │  📍 6 incidencias | 14.5 km     │   │
│  │  ⏱ Estimado: 27 min             │   │
│  │  Estado: PLANEADA               │   │
│  │                                 │   │
│  │  [🗺️ Ver Ruta] [▶️ INICIAR NAV] │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

**El botón `▶️ INICIAR NAVEGACIÓN`** solo aparece si `estado === "planeada"` o `"asignada"`.

---

### 4.3 Pantalla: Modo Navegación (full-screen)

```
┌──────────────────────────────────────────┐
│ ← Salir   NAVEGANDO — Ruta #6    ⏸ Pausar│
├──────────────────────────────────────────┤
│                                          │
│         [  MAPA LEAFLET FULL ]           │
│                                          │
│   📍 Tú aquí   🔴 Punto actual           │
│   ⚫ Pendientes  ✅ Completados          │
│          [trazado azul de ruta]          │
│                                          │
├──────────────────────────────────────────┤
│  ➡️  Gira a la derecha                   │
│      San Salvador — en 441 m             │
│─────────────────────────────────────────-│
│  Siguiente: ⬆️  Av. Roosevelt — 169 m   │
├──────────────────────────────────────────┤
│  📍 Destino: Incidencia #143             │
│  Animal muerto — 1.68 km — ~3.5 min     │
├──────────────────────────────────────────┤
│  Progreso: ██░░░░░░  1/6  (16.7%)       │
│            [✅ Marcar como Atendido]     │
└──────────────────────────────────────────┘
```

---

### 4.4 Colores de Marcadores en el Mapa

| Estado del punto | Color del pin | Descripción |
|---|---|---|
| Depósito (inicio) | 🟢 Verde | Punto de partida |
| Pendiente | 🔴 Rojo | No visitado aún |
| Actual / En curso | 🟡 Amarillo parpadeante | El operador va hacia aquí |
| Completado | ⚫ Gris | Ya atendido |
| Botadero | 🔵 Azul | Punto final |

---

### 4.5 Implementación JavaScript — Código completo

```javascript
const BASE_URL = "http://127.0.0.1:8000";
let watchId = null;          // ID del watchPosition
let puntoActualOrden = 2;    // Empieza en el primer punto después del depósito
let rutaData = null;         // Datos de la ruta completa
let map = null;              // Instancia de Leaflet
let marcadorUsuario = null;  // Marcador GPS del operador

// ─── 1. INICIAR NAVEGACIÓN ────────────────────────────────────────────────

async function iniciarNavegacion(rutaId, token) {
  // Cargar datos completos de la ruta
  const res = await fetch(`${BASE_URL}/api/rutas/${rutaId}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  rutaData = await res.json();

  // Inicializar mapa Leaflet centrado en el primer punto
  const primerPunto = rutaData.puntos[0];
  map = L.map('mapa-navegacion').setView([primerPunto.lat, primerPunto.lon], 16);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

  // Dibujar todos los marcadores de puntos
  dibujarPuntosEnMapa(rutaData.puntos);

  // Determinar primer punto a visitar (orden 2, después del depósito)
  puntoActualOrden = rutaData.puntos.find(p => p.tipo_punto === "incidencia")?.secuencia || 2;

  // Activar seguimiento GPS
  if (!navigator.geolocation) {
    alert("Este dispositivo no soporta geolocalización");
    return;
  }
  watchId = navigator.geolocation.watchPosition(
    onPosicionActualizada,
    onErrorGPS,
    { enableHighAccuracy: true, maximumAge: 3000, timeout: 10000 }
  );
}

// ─── 2. ACTUALIZACIÓN GPS ─────────────────────────────────────────────────

async function onPosicionActualizada(position) {
  const { latitude: lat, longitude: lon } = position.coords;

  // Actualizar marcador del usuario en el mapa
  if (!marcadorUsuario) {
    marcadorUsuario = L.circleMarker([lat, lon], {
      radius: 10, color: "#007bff", fillColor: "#007bff", fillOpacity: 0.8
    }).addTo(map);
  } else {
    marcadorUsuario.setLatLng([lat, lon]);
  }
  map.panTo([lat, lon]);

  // Obtener instrucciones turn-by-turn actualizadas
  try {
    const res = await fetch(
      `${BASE_URL}/api/rutas/${rutaData.id}/direcciones` +
      `?lat_actual=${lat}&lon_actual=${lon}&punto_destino_orden=${puntoActualOrden}`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    const nav = await res.json();
    actualizarPanelInstrucciones(nav);

    // Verificar si el operador llegó al punto (radio 50 metros)
    if (nav.distancia_metros <= 50) {
      await marcarPuntoComoCompletado();
    }
  } catch (e) {
    // Sin conexión: mantener instrucciones anteriores en caché
    mostrarModoOffline();
  }
}

// ─── 3. PANEL DE INSTRUCCIONES ────────────────────────────────────────────

function actualizarPanelInstrucciones(nav) {
  if (!nav.instrucciones || nav.instrucciones.length === 0) return;

  const instruccionActual = nav.instrucciones[0];
  const instruccionSiguiente = nav.instrucciones[1];

  const iconos = {
    "left": "⬅️", "right": "➡️", "straight": "⬆️",
    "slight left": "↖️", "slight right": "↗️", "uturn": "🔄"
  };

  document.getElementById("instruccion-principal").innerHTML = `
    <span class="icono">${iconos[instruccionActual.modificador] || "⬆️"}</span>
    <span class="texto">${instruccionActual.texto}</span>
    <span class="distancia">${formatearDistancia(instruccionActual.distancia_metros)}</span>
  `;

  if (instruccionSiguiente) {
    document.getElementById("instruccion-siguiente").textContent =
      `Después: ${iconos[instruccionSiguiente.modificador] || ""} ${instruccionSiguiente.texto}`;
  }

  document.getElementById("distancia-destino").textContent =
    `${formatearDistancia(nav.distancia_metros)} — ~${Math.ceil(nav.duracion_segundos / 60)} min`;
}

// ─── 4. COMPLETAR PUNTO ───────────────────────────────────────────────────

async function marcarPuntoComoCompletado() {
  const puntoActual = rutaData.puntos.find(p => p.secuencia === puntoActualOrden);
  if (!puntoActual || puntoActual.tipo_punto !== "incidencia") return;

  const res = await fetch(
    `${BASE_URL}/api/rutas/${rutaData.id}/incidencia/${puntoActual.incidencia_id}/completar`,
    { method: "POST", headers: { Authorization: `Bearer ${token}` } }
  );
  const resultado = await res.json();

  // Actualizar marcador en mapa a "completado" (gris)
  actualizarColorMarcador(puntoActualOrden, "completado");

  // Vibración háptica en móvil
  if (navigator.vibrate) navigator.vibrate([200, 100, 200]);

  // Mostrar toast de confirmación
  mostrarToast(`✅ Punto atendido — ${resultado.progreso_ruta.porcentaje}% completado`);

  // Verificar si terminó la ruta
  if (resultado.progreso_ruta.todas_completadas) {
    finalizarNavegacion();
    return;
  }

  // Avanzar al siguiente punto de incidencia
  const siguientePunto = rutaData.puntos.find(
    p => p.secuencia > puntoActualOrden && p.tipo_punto === "incidencia"
  );
  if (siguientePunto) {
    puntoActualOrden = siguientePunto.secuencia;
    resaltarPuntoActual(puntoActualOrden);
  } else {
    // No hay más incidencias, ir al botadero
    finalizarNavegacion();
  }
}

// ─── 5. FINALIZAR NAVEGACIÓN ──────────────────────────────────────────────

function finalizarNavegacion() {
  if (watchId) navigator.geolocation.clearWatch(watchId);
  watchId = null;

  // Mostrar pantalla de éxito
  document.getElementById("pantalla-navegacion").style.display = "none";
  document.getElementById("pantalla-completado").style.display = "block";
  document.getElementById("mensaje-final").textContent =
    "🎉 ¡Ruta completada! Todas las incidencias han sido atendidas.";
}

// ─── 6. MODO OFFLINE ──────────────────────────────────────────────────────

function mostrarModoOffline() {
  document.getElementById("banner-offline").style.display = "block";
  document.getElementById("banner-offline").textContent =
    "📡 Sin conexión — usando mapa base OSM. Las instrucciones no están disponibles.";
}

// ─── 7. HELPERS ───────────────────────────────────────────────────────────

function formatearDistancia(metros) {
  return metros >= 1000
    ? `${(metros / 1000).toFixed(1)} km`
    : `${Math.round(metros)} m`;
}

function onErrorGPS(error) {
  console.warn("Error GPS:", error.message);
  mostrarToast("⚠️ No se puede obtener tu ubicación. Verifica que el GPS está activado.");
}
```

---

### 4.6 Tests E2E — Mock de Geolocalización

```javascript
// tests/e2e/navegacion.test.js
describe("Navegación paso a paso", () => {

  // Mock de geolocalización
  const mockPositions = [
    { lat: -0.9310, lon: -78.6120 },  // Posición inicial
    { lat: -0.9320, lon: -78.6130 },  // En movimiento
    { lat: -0.9344, lon: -78.6154 },  // Cerca del punto 2 (49m)
  ];

  beforeEach(() => {
    let posIndex = 0;
    global.navigator.geolocation = {
      watchPosition: (success) => {
        const interval = setInterval(() => {
          if (posIndex < mockPositions.length) {
            success({ coords: mockPositions[posIndex++] });
          }
        }, 100);
        return interval;
      },
      clearWatch: (id) => clearInterval(id)
    };
  });

  test("CA-4: Las instrucciones cambian cuando cambia la posición GPS", async () => {
    await iniciarNavegacion(6, testToken);
    // Primera posición
    expect(document.getElementById("instruccion-principal").textContent)
      .toContain("Oriente");
    // Simular movimiento
    await esperar(200);
    expect(document.getElementById("instruccion-principal").textContent)
      .not.toBe("");
  });

  test("CA-6: Al llegar a 50m del punto, se marca como completado", async () => {
    await iniciarNavegacion(6, testToken);
    // Simular posición a 49m del punto 2
    await esperar(300); // esperar 3 actualizaciones del mock
    expect(document.getElementById("toast-mensaje").textContent)
      .toContain("Punto atendido");
  });

  test("CA-9: El orden es estricto, no se puede saltar puntos", () => {
    const ruta = { puntos: [
      { secuencia: 1, tipo_punto: "deposito" },
      { secuencia: 2, tipo_punto: "incidencia", incidencia_id: 143 },
      { secuencia: 3, tipo_punto: "incidencia", incidencia_id: 138 },
    ]};
    // El sistema siempre va al siguiente en orden secuencial
    const siguiente = ruta.puntos.find(
      p => p.secuencia > 2 && p.tipo_punto === "incidencia"
    );
    expect(siguiente.incidencia_id).toBe(138); // No puede saltar al 3
  });

  test("CA-7: Sin conexión, muestra banner de offline sin romper navegación", async () => {
    // Simular fallo de red
    global.fetch = jest.fn().mockRejectedValue(new Error("Network Error"));
    await onPosicionActualizada({ coords: { latitude: -0.931, longitude: -78.612 } });
    expect(document.getElementById("banner-offline").style.display).toBe("block");
  });

});

function esperar(ms) { return new Promise(r => setTimeout(r, ms)); }
```

---

## 5. Flujo de Estados del Mapa en Tiempo Real

```
Inicio navegación
      ↓
Todos los puntos: 🔴 Rojo (pendiente)
      ↓
GPS se mueve → instrucciones se actualizan (cada 3s)
      ↓
Punto actual (en camino): 🟡 Amarillo parpadeante
      ↓
Llega a ≤50m → automático:
  POST /completar
  Punto → ⚫ Gris (completado)
  Siguiente punto → 🟡 Amarillo
      ↓
Todos los puntos ⚫ → Pantalla final 🎉
```

---

## 6. Comportamiento Offline (CA-7)

| Situación | Comportamiento |
|---|---|
| Sin internet, GPS activo | Mapa OSM cacheado por Leaflet, sin instrucciones, marcador se mueve |
| Sin internet, sin GPS | Banner: "Sin conexión — navegación pausada" |
| OSRM caído, internet OK | Backend devuelve fallback Haversine con `osrm_disponible: false` |
| Reconexión | `instrucciones` vuelven automáticamente en la siguiente llamada |

**Estrategia de caché recomendada:** Al cargar la ruta inicialmente, guardar en `localStorage`:
```javascript
localStorage.setItem(`ruta_${rutaId}`, JSON.stringify(rutaData));
```

---

## 7. Consideraciones de UX Móvil (CA-10)

| Elemento | Especificación |
|---|---|
| Botones de acción | Mínimo **48×48px**, sin hover (táctil) |
| Texto instrucción | Fuente ≥18px, alto contraste (negro sobre blanco) |
| Mapa | 60% de la pantalla en modo vertical |
| Panel instrucciones | 40% inferior, fijo |
| Icono de dirección | ≥40px, reconocible bajo luz solar directa |
| Orientación | Prioritariamente **portrait** (vertical) |
| Keep screen on | `navigator.wakeLock.request("screen")` para evitar apagado |

---

## 8. Resumen de Endpoints — Tabla Rápida para el Frontend

| Cuándo llamar | Endpoint | Método | Body / Params |
|---|---|---|---|
| Al iniciar navegación | `/api/rutas/{id}` | GET | — |
| Cada 3s (GPS loop) | `/api/rutas/{id}/direcciones` | GET | `lat_actual`, `lon_actual`, `punto_destino_orden` |
| Al llegar a ≤50m | `/api/rutas/{id}/incidencia/{inc_id}/completar` | POST | — |
| Para ver progreso | `/api/rutas/{id}/navegacion` | GET | — |
| Al finalizar ruta | `/api/conductores/finalizar-ruta` | POST | `{ ruta_id }` |

---

## 9. Prueba Backend Realizada

```
GET /api/rutas/6/direcciones
  ?lat_actual=-0.9310&lon_actual=-78.6120
  &punto_destino_orden=2
```

**Resultado:** ✅ `200 OK`
- Distancia: **1679.4 m**
- Duración: **212.3 s (~3.5 min)**
- **8 instrucciones** con calles reales de Latacunga:
  - Oriente → San Salvador → Av. Roosevelt → Márquez de Maenza → Belisario Quevedo → General Maldonado → Arrive
- Geometry: **51 puntos** LineString GeoJSON
- `osrm_disponible: true`
