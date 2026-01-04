# 📅 Sistema de Horarios de Recolección

Sistema completo para gestionar horarios fijos de recolección domiciliaria por sectores geográficos.

## 📊 Resumen

Este módulo permite:
- ✅ Definir **sectores geográficos** con polígonos
- ✅ Configurar **horarios semanales** de recolección
- ✅ Programar **ejecuciones diarias** automáticamente
- ✅ Hacer **tracking GPS** en tiempo real
- ✅ Gestionar **suspensiones** (feriados, mantenimiento)
- ✅ Generar **estadísticas** y reportes

---

## 🗺️ Arquitectura

```
┌─────────────┐
│  SECTORES   │  →  Zonas geográficas (oriental/occidental)
└──────┬──────┘
       │
       ↓
┌─────────────┐
│  HORARIOS   │  →  Días y horas de recolección
└──────┬──────┘
       │
       ↓
┌─────────────┐
│ EJECUCIONES │  →  Registro diario de cumplimiento
└──────┬──────┘
       │
       ↓
┌─────────────┐
│  TRACKING   │  →  Puntos GPS en tiempo real
└─────────────┘
```

---

## 📡 Endpoints Principales

### **1. Gestión de Sectores**

```http
POST   /api/horarios/sectores              → Crear sector
GET    /api/horarios/sectores              → Listar sectores
GET    /api/horarios/sectores/{id}         → Detalle de sector
PATCH  /api/horarios/sectores/{id}         → Activar/desactivar
```

**Ejemplo: Crear sector**
```json
POST /api/horarios/sectores
{
  "nombre": "La Matriz",
  "zona": "occidental",
  "poligono": {
    "type": "Polygon",
    "coordinates": [[
      [-78.6191, -0.9344],
      [-78.6150, -0.9344],
      [-78.6150, -0.9300],
      [-78.6191, -0.9300],
      [-78.6191, -0.9344]
    ]]
  },
  "coordenadas_centro": {
    "type": "Point",
    "coordinates": [-78.6170, -0.9322]
  },
  "poblacion_estimada": 5000,
  "cantidad_viviendas": 1200
}
```

---

### **2. Gestión de Horarios**

```http
POST   /api/horarios                       → Crear horario
GET    /api/horarios                       → Listar horarios
GET    /api/horarios/{id}                  → Detalle de horario
PUT    /api/horarios/{id}                  → Actualizar horario
DELETE /api/horarios/{id}                  → Desactivar horario
```

**Ejemplo: Crear horario**
```json
POST /api/horarios
{
  "sector_id": 1,
  "dias_semana": [1, 3, 5],          // Lunes, Miércoles, Viernes
  "hora_inicio": "06:00",
  "hora_fin": "08:00",
  "tipo": "domestica",
  "descripcion": "Recolección matutina",
  "camion_tipo": "posterior",
  "conductor_id": 5,
  "camion_placa": "ABC-1234",
  "fecha_inicio_vigencia": "2026-01-06"
}
```

**Ejemplo: Filtrar horarios**
```http
GET /api/horarios?zona=occidental&activo=true
GET /api/horarios?sector_id=1
```

---

### **3. Ejecuciones Diarias**

```http
GET    /api/horarios/ejecuciones/hoy                    → Ejecuciones de hoy
GET    /api/horarios/ejecuciones/{id}                   → Detalle de ejecución
PATCH  /api/horarios/ejecuciones/{id}/iniciar           → Iniciar ruta
PATCH  /api/horarios/ejecuciones/{id}/finalizar         → Finalizar ruta
POST   /api/horarios/ejecuciones/{id}/tracking          → Enviar ubicación GPS
```

**Ejemplo: Ver agenda del conductor**
```http
GET /api/horarios/ejecuciones/hoy?conductor_id=5
```

**Respuesta:**
```json
[
  {
    "id": 123,
    "horario_id": 1,
    "sector_nombre": "La Matriz",
    "fecha_programada": "2026-01-06T06:00:00",
    "hora_inicio_programada": "06:00",
    "hora_fin_programada": "08:00",
    "conductor_id": 5,
    "conductor_nombre": "Juan Pérez",
    "camion_placa": "ABC-1234",
    "estado": "programada",
    "created_at": "2026-01-05T00:00:00"
  }
]
```

**Ejemplo: Iniciar ejecución**
```json
PATCH /api/horarios/ejecuciones/123/iniciar
{
  "camion_placa": "ABC-1234",
  "observaciones": "Clima despejado"
}
```

**Ejemplo: Enviar tracking GPS (cada 30 segundos)**
```json
POST /api/horarios/ejecuciones/123/tracking
{
  "lat": -0.9322,
  "lon": -78.6170,
  "velocidad": 15.5
}
```

**Ejemplo: Finalizar ejecución**
```json
PATCH /api/horarios/ejecuciones/123/finalizar
{
  "toneladas_recolectadas": 2.5,
  "viviendas_atendidas": 180,
  "observaciones": "Recolección completada sin incidentes"
}
```

---

### **4. Suspensiones**

```http
POST   /api/horarios/suspensiones          → Crear suspensión
GET    /api/horarios/suspensiones          → Listar suspensiones
```

**Ejemplo: Suspender por feriado**
```json
POST /api/horarios/suspensiones
{
  "horario_id": 1,
  "fecha_suspension": "2026-01-01",
  "motivo": "Feriado nacional - Año Nuevo",
  "fecha_recuperacion": "2026-01-02"
}
```

---

### **5. Estadísticas y Reportes**

```http
GET /api/horarios/estadisticas/horario/{id}        → Estadísticas de horario
GET /api/horarios/estadisticas/resumen-diario      → Resumen del día
```

**Ejemplo: Estadísticas de horario**
```http
GET /api/horarios/estadisticas/horario/1?fecha_desde=2026-01-01&fecha_hasta=2026-01-31
```

**Respuesta:**
```json
{
  "horario_id": 1,
  "total_ejecuciones": 12,
  "completadas": 10,
  "en_curso": 1,
  "canceladas": 0,
  "atrasadas": 1,
  "promedio_cumplimiento": 92.5,
  "total_toneladas": 28.4,
  "total_viviendas": 2100
}
```

**Ejemplo: Resumen diario**
```http
GET /api/horarios/estadisticas/resumen-diario?fecha=2026-01-06
```

**Respuesta:**
```json
{
  "fecha": "2026-01-06",
  "total_programadas": 8,
  "completadas": 7,
  "en_curso": 1,
  "atrasadas": 0,
  "canceladas": 0,
  "porcentaje_cumplimiento": 87.5,
  "total_toneladas": 15.2,
  "total_viviendas": 1240
}
```

---

## 🔄 Flujo de Uso Típico

### **Fase 1: Configuración Inicial (Administrador)**

1. **Crear sectores geográficos**
   ```bash
   POST /api/horarios/sectores
   ```

2. **Configurar horarios por sector**
   ```bash
   POST /api/horarios
   ```

3. **Asignar conductores (opcional)**
   ```bash
   PUT /api/horarios/{id}
   {"conductor_id": 5}
   ```

---

### **Fase 2: Programación Semanal (Automática - CRON)**

⚠️ **TODO:** Implementar job CRON que cada domingo:
- Lee todos los horarios activos
- Genera ejecuciones para la semana siguiente
- Asigna conductores disponibles
- Programa notificaciones

```python
# Pseudo-código del CRON
def programar_semana_siguiente():
    horarios = db.query(HorarioRecoleccion).filter(activo=True)
    
    for horario in horarios:
        fechas = calcular_fechas_semana(horario.dias_semana)
        
        for fecha in fechas:
            conductor = asignar_conductor_disponible(fecha)
            
            crear_ejecucion(
                horario_id=horario.id,
                fecha_programada=fecha,
                conductor_id=conductor.id
            )
```

---

### **Fase 3: Ejecución Diaria (Conductor)**

1. **Ver agenda del día**
   ```bash
   GET /api/horarios/ejecuciones/hoy?conductor_id=5
   ```

2. **Iniciar ruta**
   ```bash
   PATCH /api/horarios/ejecuciones/123/iniciar
   ```

3. **Enviar tracking GPS (cada 30 seg)**
   ```bash
   POST /api/horarios/ejecuciones/123/tracking
   ```

4. **Finalizar ruta**
   ```bash
   PATCH /api/horarios/ejecuciones/123/finalizar
   ```

---

### **Fase 4: Monitoreo (Administrador)**

1. **Ver ejecuciones en tiempo real**
   ```bash
   GET /api/horarios/ejecuciones/hoy
   ```

2. **Ver estadísticas**
   ```bash
   GET /api/horarios/estadisticas/resumen-diario
   ```

3. **Generar reportes**
   ```bash
   GET /api/horarios/estadisticas/horario/1?fecha_desde=...
   ```

---

## 🗄️ Modelos de Datos

### **Sector**
```python
{
  "id": 1,
  "nombre": "La Matriz",
  "zona": "occidental",
  "poligono": {...},            # GeoJSON Polygon
  "coordenadas_centro": {...},  # GeoJSON Point
  "poblacion_estimada": 5000,
  "cantidad_viviendas": 1200,
  "activo": true
}
```

### **HorarioRecoleccion**
```python
{
  "id": 1,
  "sector_id": 1,
  "dias_semana": "1,3,5",       # Lun, Mié, Vie
  "hora_inicio": "06:00",
  "hora_fin": "08:00",
  "tipo": "domestica",
  "camion_tipo": "posterior",
  "conductor_id": 5,
  "distancia_km": 8.5,
  "duracion_estimada": "00:45:00",
  "activo": true
}
```

### **EjecucionHorario**
```python
{
  "id": 123,
  "horario_id": 1,
  "fecha_programada": "2026-01-06T06:00:00",
  "fecha_inicio_real": "2026-01-06T06:05:00",
  "fecha_fin_real": "2026-01-06T07:50:00",
  "conductor_id": 5,
  "camion_placa": "ABC-1234",
  "estado": "completada",
  "porcentaje_cumplimiento": 92.5,
  "toneladas_recolectadas": 2.5,
  "viviendas_atendidas": 180,
  "ruta_recorrida": {...}  # LineString GeoJSON
}
```

---

## 🔧 Configuración

### **1. Aplicar migración de base de datos**

```bash
# PostgreSQL
psql -U usuario -d nombre_bd -f migrations/004_sistema_horarios.sql
```

### **2. Verificar tablas creadas**

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE '%horario%' OR table_name = 'sectores';
```

### **3. Configurar CRON job (TODO)**

```python
# Usando APScheduler en FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('cron', day_of_week='sun', hour=0)
async def programar_semana():
    # Lógica de programación semanal
    pass

scheduler.start()
```

---

## 📱 Integración con App Móvil

### **Vista del Conductor**

```
┌─────────────────────────────────────┐
│  📅 Mi Agenda - Lunes 6 Enero      │
├─────────────────────────────────────┤
│                                     │
│  🕐 06:00 - 08:00                  │
│     Recolección La Matriz          │
│     Camión: ABC-1234 (Posterior)   │
│     Ruta: 8.5 km (~45 min)         │
│     [Ver Ruta] [Iniciar]           │
│                                     │
│  🕐 09:00 - 11:00                  │
│     Ruta Incidencias - Oriental    │
│     7 puntos (animal_muerto, etc)  │
│     [Ver Ruta]                     │
│                                     │
└─────────────────────────────────────┘
```

### **Durante Ejecución**

```
┌─────────────────────────────────────┐
│  🗺️ Recolección en Curso           │
├─────────────────────────────────────┤
│  [Mapa con ruta y ubicación GPS]   │
│                                     │
│  Progreso: 65%                     │
│  Tiempo: 30 min / 45 min           │
│  Distancia: 5.5 km / 8.5 km        │
│                                     │
│  [📸 Reportar Incidente]           │
│  [⏸️  Pausar] [✅ Finalizar]        │
└─────────────────────────────────────┘
```

---

## 🎯 Próximos Pasos

- [ ] Implementar CRON job de programación semanal
- [ ] Sistema de notificaciones a ciudadanos
- [ ] Integración con app móvil del conductor
- [ ] Dashboard administrativo en tiempo real
- [ ] Algoritmo de optimización de rutas por sector
- [ ] Sistema de alertas por retrasos
- [ ] Exportación de reportes PDF/Excel
- [ ] API pública para consulta de horarios

---

## 🐛 Debug y Testing

### **Probar creación de sector**
```bash
curl -X POST http://localhost:8000/api/horarios/sectores \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Test Sector",
    "zona": "occidental",
    "poligono": {...},
    "coordenadas_centro": {...}
  }'
```

### **Ver logs de ejecuciones**
```sql
SELECT 
    e.id,
    s.nombre AS sector,
    e.estado,
    e.fecha_inicio_real,
    e.fecha_fin_real,
    e.porcentaje_cumplimiento
FROM ejecuciones_horario e
JOIN horarios_recoleccion h ON e.horario_id = h.id
JOIN sectores s ON h.sector_id = s.id
WHERE DATE(e.fecha_programada) = CURRENT_DATE
ORDER BY e.hora_inicio_programada;
```

---

## 📚 Documentación API

Una vez levantado el servidor, visita:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Busca la sección **"horarios"** para ver todos los endpoints documentados.

---

## 💡 Casos de Uso

### **Caso 1: Feriado Nacional**
```bash
POST /api/horarios/suspensiones
{
  "horario_id": 1,
  "fecha_suspension": "2026-12-25",
  "motivo": "Navidad"
}
```

### **Caso 2: Cambio de Conductor**
```bash
PUT /api/horarios/1
{
  "conductor_id": 8
}
```

### **Caso 3: Desactivar Sector Temporalmente**
```bash
PATCH /api/horarios/sectores/1
{
  "activo": false
}
```

---

**Sistema desarrollado para EPAGAL Latacunga - 2026**
