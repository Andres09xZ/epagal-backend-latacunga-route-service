# FLUJO DEL SISTEMA CON VALIDACIÓN DE INCIDENCIAS Y ASIGNACIÓN DE HORARIOS

## 📋 RESUMEN DEL NUEVO FLUJO

El sistema ahora implementa un **control administrativo** sobre las incidencias antes de generar rutas, y permite **asignar horarios** a las rutas generadas.

---

## 🔄 FLUJO COMPLETO PASO A PASO

### FASE 1: REPORTE DE INCIDENCIAS (Ciudadano)

1. **Ciudadano reporta incidencia**
   - Endpoint: `POST /api/incidencias/`
   - La incidencia se crea con **estado: `pendiente`**
   - Se asigna automáticamente:
     - Gravedad según tipo (acopio=1, zona_critica=3, animal_muerto=5)
     - Zona (oriental/occidental)
     - Coordenadas UTM
     - Ventana de atención

```json
{
  "tipo": "animal_muerto",
  "descripcion": "Perro en la vía principal",
  "lat": -0.9365,
  "lon": -78.6135,
  "foto_url": "https://example.com/foto.jpg"
}
```

**Estado inicial:** `pendiente` ⏸️

---

### FASE 2: VALIDACIÓN (Administrador)

2. **Administrador revisa incidencias pendientes**
   - Endpoint: `GET /api/incidencias/?estado=pendiente`
   - El admin ve todas las incidencias reportadas
   - Verifica si son válidas o son spam/duplicados

3. **Administrador valida o rechaza**
   
   **VALIDAR (aprobar):**
   - Endpoint: `POST /api/incidencias/{id}/validate`
   - Cambia estado a **`validada`** ✅
   - **AUTOMÁTICAMENTE** verifica si se supera el umbral
   - Si se supera → genera ruta automáticamente
   
   **RECHAZAR (cancelar):**
   - Endpoint: `PATCH /api/incidencias/{id}`
   - Body: `{"estado": "cancelada"}`
   - La incidencia se marca como cancelada ❌

**Estados posibles:**
- `pendiente` → Esperando revisión del admin
- `validada` → Aprobada por admin, cuenta para rutas
- `cancelada` → Rechazada por admin
- `asignada` → Incluida en una ruta generada
- `completada` → Atendida por conductores

---

### FASE 3: VERIFICACIÓN DE UMBRAL (Automático)

4. **Sistema verifica umbral automáticamente**
   - Solo cuenta incidencias con estado **`validada`**
   - Umbral por defecto: 20 puntos de gravedad
   - Endpoint de consulta: `GET /api/incidencias/zona/{zona}/umbral`

```json
// Respuesta:
{
  "zona": "oriental",
  "suma_gravedad": 23,
  "umbral_configurado": 20,
  "debe_generar_ruta": true,
  "incidencias_validadas": 7
}
```

**Regla:** Si `suma_gravedad > umbral` → Se genera ruta automáticamente

---

### FASE 4: GENERACIÓN DE RUTAS (Automático o Manual)

5. **Ruta generada automáticamente** (al validar incidencia que supera umbral)
   - O **manualmente** por admin: `POST /api/rutas/generar/{zona}`
   - Usa algoritmo de optimización (OR-Tools + OSRM)
   - Incluye solo incidencias **validadas**
   - Calcula:
     - Orden óptimo de visita
     - Camiones necesarios
     - Distancia y tiempo estimado
     - Coordenadas de navegación (polyline)

```json
// Ruta generada:
{
  "id": 26,
  "zona": "oriental",
  "estado": "planeada",
  "suma_gravedad": 25,
  "camiones_usados": 2,
  "duracion_estimada": "02:30:00",
  "costo_total_metros": 12500
}
```

**Estado inicial de ruta:** `planeada` 📋

---

### FASE 5: ASIGNACIÓN DE CONDUCTORES Y HORARIOS (Administrador)

6. **Administrador asigna conductores a la ruta**
   - Endpoint: `POST /api/conductores/asignaciones/`
   - **NUEVO:** Puede incluir `fecha_inicio` para programar horario

```json
{
  "ruta_id": 26,
  "conductor_id": 3,
  "camion_tipo": "posterior",
  "camion_id": "LAT-003",
  "fecha_inicio": "2025-12-19T08:00:00"  // ⏰ HORARIO PROGRAMADO
}
```

7. **Listar conductores disponibles**
   - Endpoint: `GET /api/conductores/disponibles?zona=oriental`
   - Filtra por zona preferida y estado disponible

**Estados de asignación:**
- `asignado` → Conductor asignado, pendiente de iniciar
- `iniciado` → Ruta en ejecución
- `completado` → Ruta finalizada

---

### FASE 6: EJECUCIÓN DE RUTA (Conductor)

8. **Conductor inicia la ruta** (en el horario programado)
   - Endpoint: `POST /api/conductores/iniciar-ruta`
   - Cambia estado a **`iniciado`** 🚛
   - Marca `fecha_inicio` actual
   - Conductor pasa a estado `ocupado`

9. **Conductor sigue la ruta**
   - Endpoint: `GET /api/rutas/{ruta_id}`
   - Obtiene puntos de navegación con orden
   - Polyline para Google Maps/Leaflet
   - Detalles de cada incidencia

10. **Conductor finaliza la ruta**
    - Endpoint: `POST /api/conductores/finalizar-ruta`
    - Cambia estado a **`completado`** ✅
    - Conductor vuelve a `disponible`
    - Incidencias marcadas como `completada`

---

## 📊 DIAGRAMA DE ESTADOS

### Incidencias:
```
pendiente → validada → asignada → completada
   ↓           ↓
cancelada   cancelada
```

### Rutas:
```
planeada → en_ejecucion → completada
```

### Asignaciones:
```
asignado → iniciado → completado
   ↓
cancelado
```

---

## 🔐 ROLES Y PERMISOS

### Administrador (`admin`)
- ✅ Validar/rechazar incidencias
- ✅ Generar rutas manualmente
- ✅ Asignar conductores a rutas
- ✅ Programar horarios de inicio
- ✅ Ver todas las incidencias y rutas
- ✅ Crear/modificar conductores

### Conductor (`conductor`)
- ✅ Ver mis rutas asignadas
- ✅ Iniciar ruta asignada
- ✅ Ver detalles de navegación
- ✅ Finalizar ruta
- ❌ No puede validar incidencias
- ❌ No puede generar rutas

### Ciudadano (`ciudadano`)
- ✅ Reportar incidencias
- ❌ No puede validar
- ❌ No puede ver rutas

---

## 🔑 ENDPOINTS PRINCIPALES

### Incidencias
```
POST   /api/incidencias/                    # Crear incidencia (ciudadano)
GET    /api/incidencias/                    # Listar incidencias
GET    /api/incidencias/?estado=pendiente   # Filtrar pendientes (admin)
POST   /api/incidencias/{id}/validate       # 🆕 Validar incidencia (admin)
PATCH  /api/incidencias/{id}                # Actualizar/cancelar
GET    /api/incidencias/zona/{zona}/umbral  # Ver umbral y suma
```

### Rutas
```
POST   /api/rutas/generar/{zona}            # Generar ruta manual (admin)
GET    /api/rutas/{ruta_id}                 # Obtener ruta con navegación
GET    /api/rutas/zona/{zona}               # Listar rutas por zona
PATCH  /api/rutas/{ruta_id}/estado          # Cambiar estado de ruta
```

### Conductores y Asignaciones
```
POST   /api/conductores/asignaciones/       # 🆕 Asignar conductor + horario (admin)
GET    /api/conductores/disponibles         # Listar disponibles
POST   /api/conductores/iniciar-ruta        # Iniciar ruta (conductor)
POST   /api/conductores/finalizar-ruta      # Finalizar ruta (conductor)
GET    /api/conductores/mis-rutas/todas     # Mis rutas (conductor)
```

---

## 💡 EJEMPLOS DE USO

### 1. Ciudadano reporta y admin valida

```bash
# 1. Ciudadano reporta
curl -X POST http://localhost:9000/api/incidencias/ \
  -H "Content-Type: application/json" \
  -d '{
    "tipo": "zona_critica",
    "descripcion": "Basura acumulada 3 días",
    "lat": -0.9350,
    "lon": -78.6140
  }'
# → Incidencia ID=100, estado="pendiente"

# 2. Admin valida (con token de admin)
curl -X POST http://localhost:9000/api/incidencias/100/validate \
  -H "Authorization: Bearer {admin_token}"
# → estado="validada", verifica umbral, genera ruta si corresponde
```

### 2. Admin asigna conductor con horario

```bash
# Asignar conductor para mañana a las 8:00 AM
curl -X POST http://localhost:9000/api/conductores/asignaciones/ \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "ruta_id": 26,
    "conductor_id": 3,
    "camion_tipo": "posterior",
    "camion_id": "LAT-003",
    "fecha_inicio": "2025-12-19T08:00:00"
  }'
```

### 3. Conductor ejecuta ruta

```bash
# 1. Iniciar ruta
curl -X POST http://localhost:9000/api/conductores/iniciar-ruta \
  -H "Authorization: Bearer {conductor_token}" \
  -d '{"ruta_id": 26}'

# 2. Obtener navegación
curl http://localhost:9000/api/rutas/26 \
  -H "Authorization: Bearer {conductor_token}"
# → Obtiene puntos, polyline, incidencias

# 3. Finalizar ruta
curl -X POST http://localhost:9000/api/conductores/finalizar-ruta \
  -H "Authorization: Bearer {conductor_token}" \
  -d '{"ruta_id": 26, "notas": "Ruta completada sin problemas"}'
```

---

## 🎯 VENTAJAS DEL NUEVO FLUJO

✅ **Control de calidad:** Admin valida incidencias antes de generar rutas  
✅ **Evita spam:** Incidencias falsas no generan rutas innecesarias  
✅ **Planificación:** Admin puede programar horarios de inicio  
✅ **Flexibilidad:** Generación automática o manual de rutas  
✅ **Trazabilidad:** Histórico completo de estados y asignaciones  
✅ **Optimización:** Solo incidencias validadas en cálculos de rutas  

---

## 📌 NOTAS IMPORTANTES

1. **Solo incidencias VALIDADAS** cuentan para el umbral y generación de rutas
2. **El horario es opcional** al asignar conductor (fecha_inicio)
3. **La validación puede disparar generación automática** de rutas
4. **Múltiples conductores** pueden asignarse a una misma ruta (diferentes camiones)
5. **El estado de la ruta** cambia automáticamente cuando conductores inician/finalizan

---

Última actualización: 2025-12-18
