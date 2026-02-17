# API Backend - App Operador EPAGAL
**Base URL:** `http://localhost:8081`

## 🔐 Login Operador

### POST `/api/auth/login`
```json
Request:
{
  "username": "conductor1",
  "password": "conductor123"
}

Response:
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "user_id": 2,
  "username": "conductor1",
  "tipo_usuario": "conductor",
  "conductor_id": 1
}
```

---

## 🚛 Mis Rutas

### GET `/api/conductores/mis-rutas/todas`
Obtener todas mis rutas asignadas
```
Headers: Authorization: Bearer {token}

Response:
{
  "total": 3,
  "asignado": 1,
  "iniciado": 1,
  "completado": 1,
  "rutas": [
    {
      "asignacion_id": 15,
      "ruta_id": 10,
      "estado_asignacion": "asignado",
      "camion_tipo": "posterior",
      "camion_id": "LAT-001",
      "fecha_asignacion": "2025-12-13T18:00:00",
      "ruta": {
        "id": 10,
        "zona": "oriental",
        "estado": "planeada",
        "suma_gravedad": 21,
        "camiones_usados": 2,
        "duracion_estimada": "0:28:45"
      }
    }
  ]
}
```

### GET `/api/conductores/mis-rutas/actual`
Obtener mi ruta actualmente en ejecución
```
Headers: Authorization: Bearer {token}

Response:
{
  "asignacion_id": 15,
  "ruta_id": 10,
  "estado": "iniciado",
  "camion_tipo": "posterior",
  "camion_id": "LAT-001",
  "fecha_inicio": "2025-12-13T19:00:00",
  "ruta": {
    "id": 10,
    "zona": "oriental",
    "puntos": [...],
    "polyline": "encoded_polyline"
  }
}
```

---

## � Detalles de Ruta

### GET `/api/rutas/{id}`
Obtener ruta con puntos para navegación
```
Headers: Authorization: Bearer {token}

Response:
{
  "id": 10,
  "zona": "oriental",
  "estado": "planeada",
  "suma_gravedad": 21,
  "camiones_usados": 2,
  "duracion_estimada": "0:28:45",
  "costo_total_metros": 15234.5,
  "puntos": [
    {
      "id": 1,
      "secuencia": 1,
      "tipo_punto": "incidencia",
      "lat": -0.9350,
      "lon": -78.610,
      "tipo_camion": "posterior",
      "incidencia_id": 5,
      "tipo_incidencia": "acopio",
      "gravedad": 5
    },
    {
      "id": 2,
      "secuencia": 2,
      "tipo_punto": "incidencia",
      "lat": -0.9360,
      "lon": -78.609,
      "tipo_camion": "posterior",
      "incidencia_id": 6,
      "tipo_incidencia": "zona_critica",
      "gravedad": 3
    }
  ],
  "polyline": "m~nlFtmzbN..."
}
```

### GET `/api/rutas/{id}/detalles`
Detalles completos con incidencias
```
Headers: Authorization: Bearer {token}

Response:
{
  "ruta": {
    "id": 10,
    "zona": "oriental",
    "estado": "planeada"
  },
  "incidencias": [
    {
      "id": 5,
      "tipo": "acopio",
      "gravedad": 5,
      "lat": -0.9350,
      "lon": -78.610,
      "descripcion": "...",
      "foto_url": "https://...",
      "estado": "asignada"
    }
  ],
  "puntos": [...]
}
```

---

## ▶️ Iniciar Ruta

### POST `/api/conductores/iniciar-ruta`
```
Headers: Authorization: Bearer {token}

Request:
{
  "ruta_id": 10
}

Response:
{
  "id": 15,
  "estado": "iniciado",
  "fecha_inicio": "2025-12-13T19:00:00",
  "mensaje": "Ruta iniciada exitosamente"
}
```

---

## ✅ Finalizar Ruta

### POST `/api/conductores/finalizar-ruta`
```
Headers: Authorization: Bearer {token}

Request:
{
  "ruta_id": 10,
  "notas": "Ruta completada. Todos los puntos atendidos sin problemas."
}

Response:
{
  "id": 15,
  "estado": "completado",
  "fecha_finalizacion": "2025-12-13T20:30:00",
  "notas_finalizacion": "Ruta completada...",
  "mensaje": "Ruta finalizada exitosamente"
}
```

---

## 📊 Estados de Rutas
- `asignado` - Ruta asignada, pendiente de inicio
- `iniciado` - Ruta en ejecución
- `completado` - Ruta finalizada

## 🗺️ Uso del Polyline
El campo `polyline` contiene la ruta codificada en formato Google Polyline. 
Decodificar en frontend para mostrar el camino en el mapa.
