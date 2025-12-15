# 📱 Guía de Integración - App Móvil Operadores EPAGAL

## 🔑 Credenciales de Prueba

### Operadores Disponibles
```
👤 OPERADOR 1
Username: operador1
Password: operador123
Zona: oriental
Licencia: C

👤 OPERADOR 2
Username: operador2
Password: operador123
Zona: occidental
Licencia: C

👤 OPERADOR 3
Username: operador3
Password: operador123
Zona: oriental
Licencia: D
```

### Administrador
```
👤 ADMIN
Username: admin
Password: admin123
```

---

## 🌐 Configuración API

```
Base URL: http://localhost:8081
Documentación Swagger: http://localhost:8081/docs
```

---

## 🚀 Flujo de la Aplicación

### 1️⃣ LOGIN
**POST** `/api/auth/login`

**Request:**
```json
{
  "username": "operador1",
  "password": "operador123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "user_id": 15,
  "username": "operador1",
  "tipo_usuario": "conductor",
  "conductor_id": 15
}
```

**Headers para siguientes requests:**
```
Authorization: Bearer {access_token}
```

---

### 2️⃣ VER MIS RUTAS ASIGNADAS
**GET** `/api/conductores/mis-rutas/todas`

**Headers:** `Authorization: Bearer {token}`

**Response:**
```json
{
  "total": 2,
  "asignado": 2,
  "iniciado": 0,
  "completado": 0,
  "rutas": [
    {
      "id": 18,
      "zona": "oriental",
      "estado": "planeada",
      "suma_gravedad": 17,
      "camiones_usados": 1,
      "duracion_estimada": "0:33:00.400000",
      "asignaciones": [
        {
          "id": 42,
          "ruta_id": 18,
          "conductor_id": 15,
          "camion_tipo": "posterior",
          "camion_id": "LAT-200",
          "estado": "asignado"
        }
      ]
    }
  ]
}
```

---

### 3️⃣ OBTENER DETALLES DE RUTA PARA NAVEGACIÓN
**GET** `/api/rutas/{ruta_id}`

**Headers:** `Authorization: Bearer {token}`

**Response:**
```json
{
  "id": 18,
  "zona": "oriental",
  "estado": "planeada",
  "suma_gravedad": 17,
  "camiones_usados": 1,
  "duracion_estimada": "0:33:00.400000",
  "costo_total_metros": 16124.80,
  "fecha_generacion": "2025-12-14T21:30:00",
  "puntos": [
    {
      "id": 118,
      "secuencia": 1,
      "tipo_punto": "deposito",
      "lat": -0.936,
      "lon": -78.613,
      "tipo_camion": "posterior",
      "camion_id": "LAT-200",
      "llegada_estimada": "2025-12-14T08:00:00",
      "tiempo_servicio": "0:05:00",
      "carga_acumulada": 0
    },
    {
      "id": 119,
      "secuencia": 2,
      "tipo_punto": "incidencia",
      "lat": -0.9350,
      "lon": -78.6100,
      "tipo_camion": "posterior",
      "camion_id": "LAT-200",
      "incidencia_id": 127,
      "tipo_incidencia": "acopio",
      "gravedad": 1,
      "descripcion": "Punto de acopio saturado - Barrio La Merced",
      "foto_url": null,
      "estado_incidencia": "asignada"
    }
  ],
  "polyline": "encoded_polyline_string"
}
```

**Uso del Polyline:**
- El campo `polyline` viene en formato Google Polyline Encoding
- Decodifícalo en tu app móvil para dibujar la ruta en el mapa
- Librerías disponibles: 
  - Flutter: `google_polyline_algorithm`
  - React Native: `@mapbox/polyline`
  - Android: `PolyUtil.decode()`
  - iOS: `GMSPath(fromEncodedPath:)`

---

### 4️⃣ OBTENER INCIDENCIAS DETALLADAS
**GET** `/api/rutas/{ruta_id}/detalles`

**Headers:** `Authorization: Bearer {token}`

**Response:**
```json
{
  "ruta": {
    "id": 18,
    "zona": "oriental",
    "estado": "planeada",
    "suma_gravedad": 17,
    "camiones_usados": 1,
    "duracion_estimada": "0:33:00.400000",
    "costo_total_metros": 16124.80
  },
  "incidencias": [
    {
      "id": 127,
      "tipo": "acopio",
      "gravedad": 1,
      "lat": -0.9350,
      "lon": -78.6100,
      "descripcion": "Punto de acopio saturado - Barrio La Merced",
      "foto_url": null,
      "estado": "asignada",
      "reportado_en": "2025-12-14T21:30:00"
    },
    {
      "id": 128,
      "tipo": "acopio",
      "gravedad": 1,
      "lat": -0.9360,
      "lon": -78.6090,
      "descripcion": "Contenedor rebosado - Av. Eloy Alfaro",
      "foto_url": null,
      "estado": "asignada",
      "reportado_en": "2025-12-14T21:30:00"
    }
  ],
  "puntos": [...]
}
```

---

### 5️⃣ INICIAR RUTA
**POST** `/api/conductores/iniciar-ruta`

**Headers:** `Authorization: Bearer {token}`

**Request:**
```json
{
  "ruta_id": 18
}
```

**Response:**
```json
{
  "message": "Ruta iniciada exitosamente",
  "asignacion_id": 42,
  "ruta_id": 18,
  "fecha_inicio": "2025-12-14T21:35:00",
  "estado": "iniciado"
}
```

---

### 6️⃣ ACTUALIZAR ESTADO DE INCIDENCIA
**PATCH** `/api/incidencias/{incidencia_id}`

**Headers:** `Authorization: Bearer {token}`

**Request:**
```json
{
  "estado": "completada"
}
```

**Response:**
```json
{
  "id": 127,
  "tipo": "acopio",
  "gravedad": 1,
  "estado": "completada",
  "lat": -0.9350,
  "lon": -78.6100
}
```

---

### 7️⃣ FINALIZAR RUTA
**POST** `/api/conductores/finalizar-ruta`

**Headers:** `Authorization: Bearer {token}`

**Request:**
```json
{
  "ruta_id": 18,
  "notas": "Ruta completada. Todos los puntos atendidos correctamente."
}
```

**Response:**
```json
{
  "message": "Ruta finalizada exitosamente",
  "asignacion_id": 42,
  "ruta_id": 18,
  "fecha_finalizacion": "2025-12-14T22:10:00",
  "estado": "completado"
}
```

---

## 📊 Estados

### Estados de Ruta
- `planeada` - Ruta generada, lista para iniciar
- `en_ejecucion` - Ruta en progreso
- `completada` - Ruta finalizada

### Estados de Asignación (Conductor)
- `asignado` - Asignado pero no ha iniciado
- `iniciado` - Ejecutando la ruta
- `completado` - Finalizó la ruta

### Estados de Incidencia
- `pendiente` - Reportada, sin asignar
- `asignada` - Incluida en una ruta
- `completada` - Atendida
- `cancelada` - Cancelada

---

## 🗺️ Ejemplo de Implementación (Pseudocódigo)

```javascript
// 1. Login
const loginResponse = await fetch('http://localhost:8081/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'operador1',
    password: 'operador123'
  })
});

const { access_token } = await loginResponse.json();

// 2. Obtener mis rutas
const rutasResponse = await fetch('http://localhost:8081/api/conductores/mis-rutas/todas', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});

const { rutas } = await rutasResponse.json();

// 3. Obtener detalles de ruta con polyline
const rutaId = rutas[0].id;
const detallesResponse = await fetch(`http://localhost:8081/api/rutas/${rutaId}`, {
  headers: { 'Authorization': `Bearer ${access_token}` }
});

const rutaDetalles = await detallesResponse.json();

// 4. Decodificar polyline y mostrar en mapa
const coordinates = decodePolyline(rutaDetalles.polyline);
map.addPolyline(coordinates);

// 5. Agregar marcadores de incidencias
rutaDetalles.puntos
  .filter(p => p.tipo_punto === 'incidencia')
  .forEach(punto => {
    map.addMarker({
      lat: punto.lat,
      lon: punto.lon,
      title: punto.tipo_incidencia,
      description: punto.descripcion
    });
  });

// 6. Iniciar ruta
await fetch('http://localhost:8081/api/conductores/iniciar-ruta', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ ruta_id: rutaId })
});

// 7. Al finalizar
await fetch('http://localhost:8081/api/conductores/finalizar-ruta', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    ruta_id: rutaId,
    notas: 'Ruta completada exitosamente'
  })
});
```

---

## 🧪 Datos de Prueba Disponibles

### Rutas Creadas
- **Ruta 18** - Zona Oriental (7 incidencias, 17 pts gravedad)
- **Ruta 19** - Zona Occidental (5 incidencias, 13 pts gravedad)

### Tipos de Incidencias
- `acopio` - Puntos de acopio saturados (Gravedad: 1)
- `zona_critica` - Zonas con acumulación (Gravedad: 3)
- `animal_muerto` - Animales en vía pública (Gravedad: 5)

---

## ✅ Checklist de Integración

- [ ] Implementar login con JWT
- [ ] Guardar token en almacenamiento seguro
- [ ] Listar rutas asignadas al conductor
- [ ] Mostrar mapa con polyline de navegación
- [ ] Marcar puntos de incidencias en el mapa
- [ ] Botón "Iniciar Ruta"
- [ ] Seguimiento GPS del conductor
- [ ] Actualizar estado de incidencias
- [ ] Botón "Finalizar Ruta" con notas
- [ ] Manejo de errores y reconexión

---

## 🐛 Testing

Usa Swagger UI para probar todos los endpoints:
```
http://localhost:8081/docs
```

1. Click en "Authorize" en la esquina superior derecha
2. Ingresa el token JWT (solo el token, sin "Bearer")
3. Prueba todos los endpoints interactivamente

---

## 📞 Soporte

Para más información, revisa:
- `API_ENDPOINTS.md` - Documentación completa de endpoints
- `README_DOCKER.md` - Configuración del servidor
- Swagger UI: http://localhost:8081/docs

---

**¡Listo para integrar con tu app móvil! 🚀**
