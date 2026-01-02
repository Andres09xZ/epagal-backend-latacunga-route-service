# 📱 Endpoints para App Móvil - Gestión de Rutas

## 🔄 Estados de Rutas

| Estado | Descripción | Cuándo se usa |
|--------|-------------|---------------|
| `planeada` | Ruta generada sin conductor | Al crear la ruta automáticamente |
| `asignada` | Conductor asignado pero no ha iniciado | Al asignar conductor a la ruta |
| `en_ejecucion` | Conductor inició el viaje físicamente | Cuando el conductor presiona "Iniciar Ruta" |
| `completada` | Viaje finalizado | Cuando el conductor presiona "Finalizar Ruta" |

## 🔄 Estados de Asignación de Conductor

| Estado | Descripción |
|--------|-------------|
| `asignado` | Conductor asignado a la ruta |
| `iniciado` | Conductor inició el viaje (fecha_inicio registrada) |
| `completado` | Conductor finalizó el viaje (fecha_finalizacion registrada) |
| `cancelado` | Asignación cancelada |

---

## 🆕 Nuevos Endpoints Agregados

### 1. **GET /api/rutas/historial/estado** - Historial de Rutas

Obtiene rutas filtradas por estado con información detallada de progreso.

#### Parámetros Query

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `estado` | string | No | `planeada`, `asignada`, `en_ejecucion`, `completada`, `pendiente` (todas las no completadas), o `null` |
| `zona` | string | No | `oriental` u `occidental` |
| `skip` | int | No | Paginación (default: 0) |
| `limit` | int | No | Límite de resultados (default: 50, max: 100) |

#### Ejemplo Request

```bash
# Rutas asignadas pero no iniciadas
GET http://localhost:9000/api/rutas/historial/estado?estado=asignada

# Rutas en ejecución de zona oriental  
GET http://localhost:9000/api/rutas/historial/estado?estado=en_ejecucion&zona=oriental

# Todas las rutas completadas
GET http://localhost:9000/api/rutas/historial/estado?estado=completada

# Todas las pendientes (planeada + asignada + en_ejecucion)
GET http://localhost:9000/api/rutas/historial/estado?estado=pendiente
```

#### Ejemplo Response

```json
{
  "total": 15,
  "skip": 0,
  "limit": 50,
  "filtros": {
    "estado": "completada",
    "zona": "todas"
  },
  "rutas": [
    {
      "id": 5,
      "zona": "oriental",
      "fecha_generacion": "2025-12-19T10:30:00",
      "estado": "completada",
      "suma_gravedad": 15,
      "camiones_usados": 2,
      "costo_total_km": 45.3,
      "duracion_estimada": "2:30:00",
      "incidencias": {
        "asignadas": 8,
        "completadas": 8,
        "porcentaje": 100.0
      },
      "asignaciones": [
        {
          "id": 10,
          "conductor_id": 1,
          "conductor_nombre": "Juan Pérez",
          "camion_tipo": "lateral",
          "camion_id": "ABC-123",
          "estado": "completado",
          "fecha_inicio": "2025-12-19T10:35:00",
          "fecha_fin": "2025-12-19T13:05:00"
        }
      ]
    }
  ]
}
```

---

### 2. **GET /api/rutas/calendario/activas** - Rutas para Calendario

Obtiene todas las rutas agrupadas por fecha para mostrar en un calendario móvil. **No requiere especificar fechas**, devuelve todas las rutas con asignaciones.

#### Parámetros Query

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `zona` | string | No | `oriental` u `occidental` |
| `estado` | string | No | `asignada`, `en_ejecucion`, `completada`. Por defecto: todas menos `planeada` |

**💡 Ventajas:**
- No hay límite de 90 días
- No necesitas calcular rangos de fechas
- Devuelve automáticamente el rango completo de rutas existentes
- Perfecto para cargar el calendario completo de una vez

#### Ejemplo Request

```bash
# Todas las rutas con asignaciones (por defecto: asignada, en_ejecucion, completada)
GET http://localhost:9000/api/rutas/calendario/activas

# Solo rutas en ejecución
GET http://localhost:9000/api/rutas/calendario/activas?estado=en_ejecucion

# Rutas completadas de zona occidental
GET http://localhost:9000/api/rutas/calendario/activas?estado=completada&zona=occidental

# Solo rutas asignadas (conductor asignado pero no iniciado)
GET http://localhost:9000/api/rutas/calendario/activas?estado=asignada
```

#### Ejemplo Response

```json
{
  "total_dias": 5,
  "rango_fechas": {
    "fecha_inicio": "2025-12-15",
    "fecha_fin": "2025-12-19"
  },
  "estadisticas": {
    "total_rutas": 12,
    "asignadas": 2,
    "en_ejecucion": 4,
    "completadas": 6,
    "zona_filtrada": "todas",
    "estado_filtrado": "asignada, en_ejecucion, completada"
  },
  "calendario": [
    {
      "fecha": "2025-12-19",
      "total_rutas": 3,
      "rutas": [
        {
          "id": 8,
          "zona": "oriental",
          "hora_generacion": "08:00",
          "estado": "en_ejecucion",
          "camiones_usados": 2,
          "incidencias_totales": 10,
          "incidencias_completadas": 6,
          "progreso": 60.0,
          "conductores": [
            {
              "id": 1,
              "nombre": "Juan Pérez",
              "camion_tipo": "lateral",
              "estado": "iniciado"
            },
            {
              "id": 2,
              "nombre": "María García",
              "camion_tipo": "posterior",
              "estado": "iniciado"
            }
          ]
        },
        {
          "id": 9,
          "zona": "occidental",
          "hora_generacion": "09:30",
          "estado": "completada",
          "camiones_usados": 1,
          "incidencias_totales": 5,
          "incidencias_completadas": 5,
          "progreso": 100.0,
          "conductores": [
            {
              "id": 3,
              "nombre": "Carlos López",
              "camion_tipo": "lateral",
              "estado": "completado"
            }
          ]
        }
      ]
    },
    {
      "fecha": "2025-12-18",
      "total_rutas": 2,
      "rutas": [...]
    }
  ]
}
```

---

### 3. **POST /api/conductores/iniciar-ruta** - Iniciar Ruta (Conductor)

Permite al conductor iniciar una ruta que le fue asignada. Cambia el estado de la asignación de `asignado` a `iniciado` y la ruta de `asignada` a `en_ejecucion`.

#### Autenticación
**Requiere:** Token JWT del conductor en el header `Authorization: Bearer {token}`

#### Request Body

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `ruta_id` | int | ✅ Sí | ID de la ruta a iniciar |

#### Ejemplo Request

```bash
POST http://localhost:9000/api/conductores/iniciar-ruta
Content-Type: application/json
Authorization: Bearer {token_conductor}

{
  "ruta_id": 5
}
```

#### Ejemplo Response - Éxito (200)

```json
{
  "message": "Ruta iniciada exitosamente",
  "asignacion_id": 10,
  "ruta_id": 5,
  "fecha_inicio": "2025-12-19T14:30:00",
  "estado": "iniciado"
}
```

#### Errores Posibles

| Código | Descripción |
|--------|-------------|
| 401 | Token no válido o conductor no autenticado |
| 404 | No tienes una asignación pendiente para esta ruta |

---

### 4. **POST /api/conductores/finalizar-ruta** - Finalizar Ruta (Conductor)

Permite al conductor finalizar una ruta que está en ejecución. Cambia el estado de la asignación de `iniciado` a `completado`, actualiza el conductor a `disponible`, y si todas las asignaciones están completadas, cambia la ruta a `completada`.

#### Autenticación
**Requiere:** Token JWT del conductor en el header `Authorization: Bearer {token_conductor}`

#### Request Body

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `ruta_id` | int | ✅ Sí | ID de la ruta a finalizar |
| `notas` | string | No | Notas u observaciones del conductor |

#### Ejemplo Request

```bash
POST http://localhost:9000/api/conductores/finalizar-ruta
Content-Type: application/json
Authorization: Bearer {token_conductor}

{
  "ruta_id": 5,
  "notas": "Todas las incidencias completadas. Sin problemas."
}
```

#### Ejemplo Response - Éxito (200)

```json
{
  "message": "Ruta finalizada exitosamente",
  "asignacion_id": 10,
  "ruta_id": 5,
  "fecha_finalizacion": "2025-12-19T17:45:00",
  "estado": "completado"
}
```

#### Errores Posibles

| Código | Descripción |
|--------|-------------|
| 401 | Token no válido o conductor no autenticado |
| 404 | No tienes una ruta en ejecución para finalizar |

#### 💡 Flujo Completo de Estado

```
1. Asignación creada → estado: 'asignado', ruta: 'asignada'
   ↓ POST /conductores/iniciar-ruta
2. Conductor inicia → estado: 'iniciado', ruta: 'en_ejecucion'
   ↓ (Conductor realiza el trabajo)
3. POST /conductores/finalizar-ruta
   ↓
4. Ruta finalizada → estado: 'completado', ruta: 'completada'
   → Conductor: 'disponible' (puede recibir nueva asignación)
```

---

### 5. **GET /api/conductores/{conductor_id}/rutas/activas** - Rutas Activas del Conductor

Obtiene todas las rutas activas (asignada, en_ejecucion) de un conductor específico con información detallada de incidencias, progreso y puntos de la ruta.

#### Parámetros Path

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `conductor_id` | int | ID del conductor |

#### Autenticación
**Requiere:** Token JWT (cualquier usuario autenticado)

#### Ejemplo Request

```bash
GET http://localhost:9000/api/conductores/3/rutas/activas
Authorization: Bearer {token}
```

#### Ejemplo Response

```json
{
  "conductor": {
    "id": 3,
    "nombre_completo": "Carlos López",
    "cedula": "1234567890",
    "estado": "ocupado"
  },
  "total_rutas_activas": 1,
  "rutas": [
    {
      "ruta_id": 8,
      "zona": "occidental",
      "estado_ruta": "en_ejecucion",
      "fecha_generacion": "2025-12-19T08:00:00",
      "duracion_estimada": "1:30:00",
      "costo_total_km": 23.5,
      "asignacion": {
        "id": 15,
        "estado": "iniciado",
        "camion_tipo": "lateral",
        "camion_id": "LAT-001",
        "fecha_asignacion": "2025-12-19T07:50:00",
        "fecha_inicio": "2025-12-19T08:05:00"
      },
      "progreso": {
        "incidencias_totales": 7,
        "incidencias_completadas": 4,
        "porcentaje": 57.1
      },
      "puntos": [
        {
          "orden": 0,
          "tipo_punto": "deposito",
          "lat": -0.9352,
          "lon": -78.6197,
          "distancia_desde_anterior_m": 0,
          "tiempo_desde_anterior_seg": 0
        },
        {
          "orden": 1,
          "tipo_punto": "incidencia",
          "lat": -0.9400,
          "lon": -78.6250,
          "distancia_desde_anterior_m": 850,
          "tiempo_desde_anterior_seg": 180,
          "incidencia": {
            "id": 45,
            "tipo": "acopio",
            "gravedad": 5,
            "descripcion": "Acumulación de basura",
            "estado": "completada",
            "foto_url": "https://..."
          }
        }
      ]
    }
  ]
}
```

---

### 6. **GET /api/conductores/me/estadisticas** - Mis Estadísticas

Obtiene estadísticas personales del conductor autenticado: rutas completadas, incidencias atendidas, tiempo promedio, rendimiento por zona.

#### Autenticación
**Requiere:** Token JWT del conductor

#### Ejemplo Request

```bash
GET http://localhost:9000/api/conductores/me/estadisticas
Authorization: Bearer {token_conductor}
```

#### Ejemplo Response

```json
{
  "conductor": {
    "id": 3,
    "nombre_completo": "Carlos López",
    "estado": "disponible"
  },
  "estadisticas": {
    "rutas_completadas": 45,
    "rutas_activas": 1,
    "incidencias_atendidas": 234,
    "tiempo_promedio_ruta": "1:25:30",
    "rendimiento_por_zona": {
      "oriental": 28,
      "occidental": 17
    },
    "ultima_ruta_completada": {
      "ruta_id": 42,
      "zona": "occidental",
      "fecha_finalizacion": "2025-12-19T15:30:00"
    }
  }
}
```

---

### 7. **GET /api/rutas/{ruta_id}/navegacion** - Navegación de Ruta

Obtiene información completa de navegación para una ruta: todos los puntos en orden, siguiente punto a visitar, puntos completados, progreso en tiempo real.

#### Parámetros Path

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `ruta_id` | int | ID de la ruta |

#### Ejemplo Request

```bash
GET http://localhost:9000/api/rutas/8/navegacion
```

#### Ejemplo Response

```json
{
  "ruta_id": 8,
  "zona": "occidental",
  "estado": "en_ejecucion",
  "conductor": {
    "id": 3,
    "nombre": "Carlos López",
    "telefono": "0991234567"
  },
  "navegacion": {
    "punto_actual": {
      "orden": 3,
      "tipo_punto": "incidencia",
      "lat": -0.9450,
      "lon": -78.6300,
      "completado": false,
      "incidencia": {
        "id": 48,
        "tipo": "zona_critica",
        "gravedad": 3,
        "descripcion": "Escombros en vía",
        "estado": "asignada"
      }
    },
    "punto_actual_index": 3,
    "total_puntos": 9,
    "puntos_completados": 3,
    "progreso_porcentaje": 33.3
  },
  "puntos": [
    {
      "orden": 0,
      "tipo_punto": "deposito",
      "lat": -0.9352,
      "lon": -78.6197,
      "nombre": "Depósito",
      "completado": true
    },
    {
      "orden": 1,
      "tipo_punto": "incidencia",
      "lat": -0.9400,
      "lon": -78.6250,
      "distancia_desde_anterior_m": 850,
      "tiempo_desde_anterior_seg": 180,
      "completado": true,
      "incidencia": {
        "id": 45,
        "tipo": "acopio",
        "gravedad": 5,
        "estado": "completada"
      }
    }
  ],
  "resumen": {
    "distancia_total_km": 23.5,
    "duracion_estimada": "1:30:00",
    "incidencias_totales": 7,
    "incidencias_completadas": 2
  }
}
```

**💡 Uso:** Este endpoint es ideal para mostrar en el mapa del conductor el siguiente punto a visitar y el progreso en tiempo real.

---

### 8. **POST /api/rutas/{ruta_id}/incidencia/{incidencia_id}/completar** - Completar Incidencia

Marca una incidencia específica como completada y actualiza el progreso de la ruta.

#### Parámetros Path

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `ruta_id` | int | ID de la ruta |
| `incidencia_id` | int | ID de la incidencia a completar |

#### Ejemplo Request

```bash
POST http://localhost:9000/api/rutas/8/incidencia/45/completar
```

#### Ejemplo Response - Éxito (200)

```json
{
  "message": "Incidencia marcada como completada",
  "incidencia": {
    "id": 45,
    "tipo": "acopio",
    "estado_anterior": "asignada",
    "estado_actual": "completada"
  },
  "progreso_ruta": {
    "ruta_id": 8,
    "incidencias_totales": 7,
    "incidencias_completadas": 3,
    "porcentaje": 42.9,
    "todas_completadas": false
  }
}
```

#### Errores Posibles

| Código | Descripción |
|--------|-------------|
| 404 | Ruta o incidencia no encontrada |
| 404 | La incidencia no pertenece a esta ruta |

**💡 Uso:** Cuando el conductor complete una incidencia, llama a este endpoint para actualizarla en tiempo real.

---

## 💡 Casos de Uso en App Móvil

### 📊 Pantalla de Historial

```javascript
// Obtener últimas rutas completadas
const response = await fetch(
  'http://localhost:9000/api/rutas/historial/estado?estado=completada&limit=20'
);
const data = await response.json();

// Mostrar lista con:
// - data.rutas[].zona
// - data.rutas[].fecha_generacion
// - data.rutas[].incidencias.porcentaje (barra de progreso)
// - data.rutas[].estado (badge de color)
```

### 📅 Pantalla de Calendario

```javascript
// Obtener todas las rutas para el calendario
const response = await fetch(
  'http://localhost:9000/api/rutas/calendario/activas'
);
const data = await response.json();

// Mapear al calendario
data.calendario.forEach(dia => {
  // dia.fecha -> "2025-12-19" (marcar en calendario)
  // dia.total_rutas -> Mostrar badge con número
  // dia.rutas -> Lista de rutas al hacer tap en el día
});

// Mostrar estadísticas generales
console.log(`Total rutas: ${data.estadisticas.total_rutas}`);
console.log(`Asignadas: ${data.estadisticas.asignadas}`);
console.log(`En ejecución: ${data.estadisticas.en_ejecucion}`);
console.log(`Completadas: ${data.estadisticas.completadas}`);
```

### 🚚 Vista de Conductor (Mis Rutas)

```javascript
// Obtener rutas donde está asignado el conductor actual
const conductorId = 1; // ID del conductor logueado

const response = await fetch(
  'http://localhost:9000/api/rutas/historial/estado?estado=pendiente'
);
const data = await response.json();

// Filtrar rutas donde el conductor está asignado
const misRutas = data.rutas.filter(ruta => 
  ruta.asignaciones.some(a => a.conductor_id === conductorId)
);
```

### 🚀 Iniciar y Finalizar Ruta (Conductor)

```javascript
// --- INICIAR RUTA ---
async function iniciarRuta(rutaId, token) {
  try {
    const response = await fetch(
      'http://localhost:9000/api/conductores/iniciar-ruta',
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ruta_id: rutaId
        })
      }
    );
    
    if (!response.ok) {
      throw new Error('Error al iniciar ruta');
    }
    
    const data = await response.json();
    console.log('✅ Ruta iniciada:', data);
    
    // Mostrar mensaje al usuario
    alert('¡Ruta iniciada exitosamente! Hora: ' + data.fecha_inicio);
    
    // Actualizar UI: cambiar botón "Iniciar" a "Finalizar"
    // Habilitar navegación GPS
    // Mostrar incidencias a completar
    
    return data;
  } catch (error) {
    console.error('❌ Error:', error);
    alert('No se pudo iniciar la ruta');
  }
}

// --- FINALIZAR RUTA ---
async function finalizarRuta(rutaId, notas, token) {
  try {
    const response = await fetch(
      'http://localhost:9000/api/conductores/finalizar-ruta',
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ruta_id: rutaId,
          notas: notas || 'Ruta completada sin observaciones'
        })
      }
    );
    
    if (!response.ok) {
      throw new Error('Error al finalizar ruta');
    }
    
    const data = await response.json();
    console.log('✅ Ruta finalizada:', data);
    
    // Mostrar mensaje de éxito
    alert('¡Ruta finalizada! Gracias por tu trabajo.');
    
    // Actualizar UI: volver a pantalla principal
    // Mostrar resumen de la ruta
    // El conductor ahora está disponible para nueva asignación
    
    return data;
  } catch (error) {
    console.error('❌ Error:', error);
    alert('No se pudo finalizar la ruta');
  }
}

// --- USO EN COMPONENTE ---
// Botón "Iniciar Ruta"
const btnIniciar = document.getElementById('btn-iniciar-ruta');
btnIniciar.addEventListener('click', () => {
  const rutaId = 5; // ID de la ruta asignada
  const token = localStorage.getItem('conductor_token');
  iniciarRuta(rutaId, token);
});

// Botón "Finalizar Ruta"
const btnFinalizar = document.getElementById('btn-finalizar-ruta');
btnFinalizar.addEventListener('click', () => {
  const rutaId = 5;
  const notas = document.getElementById('notas-input').value;
  const token = localStorage.getItem('conductor_token');
  finalizarRuta(rutaId, notas, token);
});
```

### 📈 Dashboard de Estadísticas

```javascript
// Obtener todas las rutas y calcular métricas
const response = await fetch(
  'http://localhost:9000/api/rutas/historial/estado'
);
const data = await response.json();

const stats = {
  total: data.total,
  completadas: data.rutas.filter(r => r.estado === 'completada').length,
  enEjecucion: data.rutas.filter(r => r.estado === 'en_ejecucion').length,
  promedioIncidencias: data.rutas.reduce((sum, r) => 
    sum + r.incidencias.porcentaje, 0
  ) / data.rutas.length
};
```

---

## 🎨 Sugerencias de UI para App Móvil

### Para el Calendario
- **Días con rutas:** Badge con número de rutas
- **Colores por estado:**
  - 🟢 Verde: Completadas
  - 🟡 Amarillo: En ejecución
  - 🔵 Azul: Planeadas
- **Al hacer tap:** Mostrar detalle de rutas del día

### Para el Historial
- **Card por ruta:**
  - Zona (badge oriental/occidental)
  - Fecha y hora
  - Barra de progreso (incidencias completadas)
  - Lista de conductores asignados
  - Estado (badge con color)

### Para Vista de Ruta Individual
- **Mapa con puntos**
- **Lista de incidencias con checkbox**
- **Botón "Iniciar Ruta"** (cambia estado a iniciado)
- **Botón "Finalizar Ruta"** (cambia estado a completado)

---

## 🔐 Autenticación

Todos los endpoints requieren token JWT en el header:

```javascript
fetch(url, {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
})
```

---

## 🐛 Códigos de Error

| Código | Descripción |
|--------|-------------|
| 400 | Parámetros inválidos (zona incorrecta, rango de fechas > 90 días) |
| 401 | Token no válido o expirado |
| 404 | Ruta no encontrada |
| 500 | Error interno del servidor |

---

## 📝 Notas Importantes

1. **Autenticación de Conductor:** Los endpoints de iniciar/finalizar requieren token JWT del conductor
2. **Estados sincronizados:** Al iniciar/finalizar, tanto la asignación como la ruta cambian de estado
3. **Conductor disponible:** Al finalizar, el conductor automáticamente queda disponible para nuevas asignaciones
4. **Paginación:** Usa `skip` y `limit` para cargar datos progresivamente
5. **Estados de ruta:**
   - `planeada`: Ruta generada pero no asignada
   - `asignada`: Conductor asignado pero no ha iniciado
   - `en_ejecucion`: Conductor trabajando en la ruta
   - `completada`: Ruta finalizada
6. **Progreso:** Se calcula en base a incidencias completadas vs totales
7. **Tiempo real:** Considera implementar WebSockets para updates en vivo

---

## ✅ Endpoints Implementados

### Gestión de Rutas
- ✅ `GET /api/rutas/historial/estado` - Historial de rutas con filtros
- ✅ `GET /api/rutas/calendario/activas` - Rutas agrupadas por fecha
- ✅ `GET /api/rutas/{ruta_id}/navegacion` - Navegación punto a punto con progreso
- ✅ `POST /api/rutas/{ruta_id}/incidencia/{incidencia_id}/completar` - Marcar incidencia completada
- ✅ `PATCH /api/rutas/{ruta_id}/estado` - Actualizar estado de ruta manualmente

### Gestión de Conductores
- ✅ `GET /api/conductores/{id}/rutas/activas` - Rutas activas de un conductor específico
- ✅ `GET /api/conductores/me/estadisticas` - Estadísticas personales del conductor
- ✅ `POST /api/conductores/iniciar-ruta` - Iniciar ruta (conductor autenticado)
- ✅ `POST /api/conductores/finalizar-ruta` - Finalizar ruta (conductor autenticado)

---

## 🚀 Próximos Endpoints Sugeridos

- `WebSocket /ws/rutas/{ruta_id}` - Actualizaciones en tiempo real del progreso de la ruta
- `POST /api/rutas/{ruta_id}/foto` - Subir foto de incidencia completada
- `GET /api/rutas/{ruta_id}/reporte` - Generar reporte PDF de ruta completada

¿Quieres que implemente alguno de estos? 🎯
