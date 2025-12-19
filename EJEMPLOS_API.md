# 🧪 EJEMPLOS PRÁCTICOS DE USO DEL API

## Base URL
```
http://localhost:9000
```

---

## 1️⃣ FLUJO COMPLETO: De Incidencia a Ruta Completada

### Paso 1: Ciudadano reporta incidencia

```bash
curl -X POST http://localhost:9000/api/incidencias/ \
  -H "Content-Type: application/json" \
  -d '{
    "tipo": "animal_muerto",
    "descripcion": "Perro muerto en Av. Unidad Nacional",
    "lat": -0.9350,
    "lon": -78.6140,
    "foto_url": "https://storage.example.com/foto123.jpg"
  }'
```

**Respuesta:**
```json
{
  "id": 150,
  "tipo": "animal_muerto",
  "gravedad": 5,
  "estado": "pendiente",
  "zona": "oriental",
  "lat": -0.9350,
  "lon": -78.6140,
  "ventana_inicio": "2025-12-18T14:30:00",
  "ventana_fin": "2025-12-18T16:30:00",
  "reportado_en": "2025-12-18T14:30:00"
}
```

---

### Paso 2: Admin lista incidencias pendientes

```bash
curl http://localhost:9000/api/incidencias/?estado=pendiente \
  -H "Authorization: Bearer {admin_token}"
```

**Respuesta:**
```json
[
  {
    "id": 150,
    "tipo": "animal_muerto",
    "gravedad": 5,
    "estado": "pendiente",
    "descripcion": "Perro muerto en Av. Unidad Nacional",
    "zona": "oriental"
  },
  {
    "id": 149,
    "tipo": "zona_critica",
    "gravedad": 3,
    "estado": "pendiente",
    "zona": "occidental"
  }
]
```

---

### Paso 3: Admin valida la incidencia

```bash
curl -X POST http://localhost:9000/api/incidencias/150/validate \
  -H "Authorization: Bearer {admin_token}"
```

**Respuesta:**
```json
{
  "incidencia_id": 150,
  "estado": "validada",
  "ruta_generada_id": 27  // ✅ Se generó ruta automáticamente
}
```

---

### Paso 4: Verificar umbral de zona

```bash
curl http://localhost:9000/api/incidencias/zona/oriental/umbral
```

**Respuesta:**
```json
{
  "zona": "oriental",
  "suma_gravedad": 23,
  "umbral_configurado": 20,
  "debe_generar_ruta": true,
  "incidencias_validadas": 6
}
```

---

### Paso 5: Ver detalles de la ruta generada

```bash
curl http://localhost:9000/api/rutas/27 \
  -H "Authorization: Bearer {admin_token}"
```

**Respuesta (resumida):**
```json
{
  "id": 27,
  "zona": "oriental",
  "estado": "planeada",
  "suma_gravedad": 23,
  "camiones_usados": 2,
  "duracion_estimada": "02:15:00",
  "costo_total_metros": 15200,
  "puntos": [
    {
      "secuencia": 1,
      "tipo_punto": "deposito",
      "lat": -0.9344,
      "lon": -78.6156
    },
    {
      "secuencia": 2,
      "tipo_punto": "incidencia",
      "incidencia_id": 150,
      "tipo_incidencia": "animal_muerto",
      "gravedad": 5,
      "lat": -0.9350,
      "lon": -78.6140
    }
  ],
  "polyline": "encoded_polyline_for_google_maps..."
}
```

---

### Paso 6: Admin lista conductores disponibles

```bash
curl http://localhost:9000/api/conductores/disponibles?zona=oriental \
  -H "Authorization: Bearer {admin_token}"
```

**Respuesta:**
```json
[
  {
    "id": 3,
    "nombre_completo": "Juan Pérez Martínez",
    "cedula": "1803456789",
    "telefono": "0987654321",
    "licencia_tipo": "C",
    "zona_preferida": "oriental"
  },
  {
    "id": 5,
    "nombre_completo": "Carlos López García",
    "cedula": "1804567890",
    "telefono": "0987654322",
    "licencia_tipo": "D",
    "zona_preferida": "ambas"
  }
]
```

---

### Paso 7: Admin asigna conductor CON HORARIO

```bash
curl -X POST http://localhost:9000/api/conductores/asignaciones/ \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "ruta_id": 27,
    "conductor_id": 3,
    "camion_tipo": "posterior",
    "camion_id": "LAT-003",
    "fecha_inicio": "2025-12-19T08:00:00"
  }'
```

**Respuesta:**
```json
{
  "id": 45,
  "ruta_id": 27,
  "conductor_id": 3,
  "camion_tipo": "posterior",
  "camion_id": "LAT-003",
  "fecha_asignacion": "2025-12-18T14:35:00",
  "fecha_inicio": "2025-12-19T08:00:00",  // ⏰ Horario programado
  "fecha_finalizacion": null,
  "estado": "asignado",
  "conductor_nombre": "Juan Pérez Martínez",
  "conductor_cedula": "1803456789",
  "conductor_telefono": "0987654321"
}
```

---

### Paso 8: Conductor ve sus rutas asignadas

```bash
curl http://localhost:9000/api/conductores/mis-rutas/todas \
  -H "Authorization: Bearer {conductor_token}"
```

**Respuesta:**
```json
{
  "total": 1,
  "asignado": 1,
  "iniciado": 0,
  "completado": 0,
  "rutas": [
    {
      "id": 27,
      "zona": "oriental",
      "estado": "planeada",
      "suma_gravedad": 23,
      "camiones_usados": 2,
      "fecha_generacion": "2025-12-18T14:33:00",
      "asignaciones": [
        {
          "id": 45,
          "estado": "asignado",
          "camion_tipo": "posterior",
          "camion_id": "LAT-003",
          "fecha_inicio": "2025-12-19T08:00:00"
        }
      ]
    }
  ]
}
```

---

### Paso 9: Conductor inicia ruta (en el horario programado)

```bash
curl -X POST http://localhost:9000/api/conductores/iniciar-ruta \
  -H "Authorization: Bearer {conductor_token}" \
  -H "Content-Type: application/json" \
  -d '{"ruta_id": 27}'
```

**Respuesta:**
```json
{
  "message": "Ruta iniciada exitosamente",
  "asignacion_id": 45,
  "ruta_id": 27,
  "fecha_inicio": "2025-12-19T08:00:15",
  "estado": "iniciado"
}
```

---

### Paso 10: Conductor obtiene navegación

```bash
curl http://localhost:9000/api/rutas/27 \
  -H "Authorization: Bearer {conductor_token}"
```

**Respuesta:** (ver paso 5)

---

### Paso 11: Conductor finaliza ruta

```bash
curl -X POST http://localhost:9000/api/conductores/finalizar-ruta \
  -H "Authorization: Bearer {conductor_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "ruta_id": 27,
    "notas": "Ruta completada sin problemas. Todas las incidencias atendidas."
  }'
```

**Respuesta:**
```json
{
  "message": "Ruta finalizada exitosamente",
  "asignacion_id": 45,
  "ruta_id": 27,
  "fecha_finalizacion": "2025-12-19T10:30:45",
  "estado": "completado"
}
```

---

## 2️⃣ AUTENTICACIÓN

### Login como Admin

```bash
curl -X POST http://localhost:9000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

**Respuesta:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": 1,
  "username": "admin",
  "tipo_usuario": "admin",
  "conductor_id": null
}
```

### Login como Conductor

```bash
curl -X POST http://localhost:9000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "conductor1",
    "password": "conductor123"
  }'
```

**Respuesta:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": 2,
  "username": "conductor1",
  "tipo_usuario": "conductor",
  "conductor_id": 1
}
```

### Obtener usuario actual

```bash
curl http://localhost:9000/auth/me \
  -H "Authorization: Bearer {token}"
```

---

## 3️⃣ GESTIÓN DE INCIDENCIAS (Admin)

### Rechazar incidencia (cancelar)

```bash
curl -X PATCH http://localhost:9000/api/incidencias/149 \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{"estado": "cancelada"}'
```

### Ver estadísticas

```bash
curl http://localhost:9000/api/incidencias/stats \
  -H "Authorization: Bearer {admin_token}"
```

**Respuesta:**
```json
{
  "total": 150,
  "pendientes": 5,
  "validadas": 45,
  "asignadas": 75,
  "completadas": 23,
  "por_tipo": {
    "acopio": 60,
    "zona_critica": 45,
    "animal_muerto": 45
  },
  "por_zona": {
    "oriental": 95,
    "occidental": 55
  }
}
```

---

## 4️⃣ GESTIÓN DE RUTAS (Admin)

### Generar ruta manualmente

```bash
curl -X POST http://localhost:9000/api/rutas/generar/oriental \
  -H "Authorization: Bearer {admin_token}"
```

### Listar rutas por zona

```bash
curl http://localhost:9000/api/rutas/zona/oriental?estado=planeada \
  -H "Authorization: Bearer {admin_token}"
```

### Cambiar estado de ruta

```bash
curl -X PATCH http://localhost:9000/api/rutas/27/estado \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{"nuevo_estado": "completada"}'
```

---

## 5️⃣ GESTIÓN DE CONDUCTORES (Admin)

### Crear nuevo conductor

```bash
curl -X POST http://localhost:9000/api/conductores/ \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "conductor6",
    "email": "nuevo.conductor@epagal.gob.ec",
    "password": "conductor123",
    "nombre_completo": "Pedro Ramírez Flores",
    "cedula": "1807890123",
    "telefono": "0987654325",
    "licencia_tipo": "C",
    "zona_preferida": "occidental"
  }'
```

### Actualizar conductor

```bash
curl -X PATCH http://localhost:9000/api/conductores/6 \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "estado": "inactivo",
    "telefono": "0999888777"
  }'
```

### Ver asignaciones de un conductor

```bash
curl http://localhost:9000/api/conductores/asignaciones/conductor/3 \
  -H "Authorization: Bearer {admin_token}"
```

---

## 6️⃣ HEALTH CHECK Y DOCUMENTACIÓN

### Health check

```bash
curl http://localhost:9000/health
```

**Respuesta:**
```json
{
  "status": "ok",
  "service": "incidencias-api"
}
```

### Documentación Swagger

```
http://localhost:9000/docs
```

### Documentación ReDoc

```
http://localhost:9000/redoc
```

---

## 📝 NOTAS IMPORTANTES

1. **Tokens:** Reemplaza `{admin_token}` y `{conductor_token}` con tokens reales obtenidos del login
2. **IDs:** Los IDs (incidencia_id, ruta_id, etc.) varían según tu base de datos
3. **Fechas:** Usa formato ISO 8601: `YYYY-MM-DDTHH:MM:SS`
4. **Horarios:** El campo `fecha_inicio` en asignaciones es opcional pero recomendado

---

## 🔧 HERRAMIENTAS RECOMENDADAS

- **Postman**: Importar colección de endpoints
- **cURL**: Ejemplos en esta guía
- **HTTPie**: Alternativa más amigable a cURL
- **Insomnia**: Cliente REST moderno

---

Última actualización: 2025-12-18
