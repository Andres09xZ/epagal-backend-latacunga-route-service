# ✅ Sistema de Horarios - Resumen de Implementación

## 📦 Archivos Creados

### **1. Modelos de Base de Datos** (`app/models.py`)
```python
✅ Sector                    # Sectores geográficos
✅ HorarioRecoleccion        # Horarios semanales
✅ EjecucionHorario          # Ejecuciones diarias
✅ PuntoTrackingHorario      # Tracking GPS
✅ SuspensionHorario         # Suspensiones temporales
```

### **2. Schemas Pydantic** (`app/schemas/horarios.py`)
```python
✅ SectorCreate, SectorResponse, SectorDetalle
✅ HorarioCreate, HorarioUpdate, HorarioResponse
✅ EjecucionCreate, EjecucionIniciar, EjecucionFinalizar
✅ TrackingGPS
✅ SuspensionCreate, SuspensionResponse
✅ EstadisticasHorario, ResumenDiario
```

### **3. Router de API** (`app/routers/horarios.py`)
```python
✅ 20+ endpoints RESTful
✅ CRUD completo para sectores y horarios
✅ Gestión de ejecuciones (iniciar, finalizar, tracking)
✅ Suspensiones
✅ Estadísticas y reportes
```

### **4. Migración SQL** (`migrations/004_sistema_horarios.sql`)
```sql
✅ Creación de 5 tablas con PostGIS
✅ Índices espaciales y de rendimiento
✅ Triggers para updated_at
✅ Vistas útiles (horarios_activos, ejecuciones_hoy)
✅ Datos iniciales de ejemplo
```

### **5. Documentación** (`SISTEMA_HORARIOS.md`)
```
✅ Guía completa de uso
✅ Ejemplos de todos los endpoints
✅ Flujo de trabajo paso a paso
✅ Casos de uso reales
```

---

## 🔧 Próximos Pasos para Completar el Sistema

### **1. Aplicar Migración de Base de Datos**
```bash
# Conectar a PostgreSQL
psql -U usuario -d nombre_bd

# Aplicar migración
\i migrations/004_sistema_horarios.sql

# Verificar tablas
\dt sectores horarios* ejecuciones* puntos* suspensiones*
```

### **2. Implementar CRON Job de Programación Semanal**
```python
# app/services/horario_scheduler.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import date, timedelta

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('cron', day_of_week='sun', hour=0)
async def programar_semana_siguiente():
    """
    Se ejecuta cada domingo a las 00:00
    Crea ejecuciones para la semana siguiente
    """
    hoy = date.today()
    inicio_semana = hoy + timedelta(days=7 - hoy.weekday())
    fin_semana = inicio_semana + timedelta(days=6)
    
    horarios = db.query(HorarioRecoleccion).filter(
        HorarioRecoleccion.activo == True
    ).all()
    
    for horario in horarios:
        # Generar fechas según días_semana
        dias = [int(d) for d in horario.dias_semana.split(',')]
        
        for dia in range(7):
            fecha = inicio_semana + timedelta(days=dia)
            dia_semana = fecha.isoweekday()  # 1=Lun, 7=Dom
            
            if dia_semana in dias:
                # Verificar suspensiones
                suspension = db.query(SuspensionHorario).filter(
                    SuspensionHorario.horario_id == horario.id,
                    func.date(SuspensionHorario.fecha_suspension) == fecha
                ).first()
                
                if not suspension:
                    # Asignar conductor disponible
                    conductor = asignar_conductor_disponible(fecha, horario)
                    
                    # Crear ejecución
                    ejecucion = EjecucionHorario(
                        horario_id=horario.id,
                        fecha_programada=datetime.combine(fecha, 
                            datetime.strptime(horario.hora_inicio, "%H:%M").time()),
                        hora_inicio_programada=horario.hora_inicio,
                        hora_fin_programada=horario.hora_fin,
                        conductor_id=conductor.id,
                        camion_placa=conductor.camion_asignado,
                        estado="programada"
                    )
                    db.add(ejecucion)
    
    db.commit()
    print(f"✅ Semana {inicio_semana} - {fin_semana} programada")

# Iniciar scheduler en main.py
scheduler.start()
```

### **3. Detectar Retrasos Automáticamente**
```python
@scheduler.scheduled_job('interval', minutes=15)
async def detectar_retrasos():
    """
    Se ejecuta cada 15 minutos
    Marca ejecuciones como atrasadas
    """
    ahora = datetime.utcnow()
    
    ejecuciones_retrasadas = db.query(EjecucionHorario).filter(
        EjecucionHorario.estado == "en_curso",
        EjecucionHorario.fecha_programada < ahora - timedelta(minutes=15)
    ).all()
    
    for ej in ejecuciones_retrasadas:
        hora_fin = datetime.combine(
            ej.fecha_programada.date(),
            datetime.strptime(ej.hora_fin_programada, "%H:%M").time()
        )
        
        if ahora > hora_fin + timedelta(minutes=15):
            ej.estado = "atrasada"
            
            # Notificar administrador
            enviar_alerta_admin(
                f"⚠️ Retraso en {ej.horario.sector.nombre}"
            )
    
    db.commit()
```

### **4. Sistema de Notificaciones**
```python
# app/services/notificaciones.py

async def notificar_ciudadanos_sector(sector_id: int, mensaje: str):
    """
    Enviar notificación push a ciudadanos del sector
    """
    # Obtener usuarios suscritos al sector
    usuarios = db.query(Usuario).filter(
        Usuario.sector_id == sector_id,
        Usuario.notificaciones_activas == True
    ).all()
    
    for usuario in usuarios:
        # Enviar push notification (Firebase, OneSignal, etc.)
        await send_push_notification(
            user_id=usuario.id,
            title="Recolección de basura",
            body=mensaje
        )

# Ejemplos de uso:
# - 24h antes: "Recolección mañana 06:00-08:00"
# - 2h antes: "Recolección en 2 horas"
# - Al iniciar: "Camión iniciando ruta en su sector"
# - Al finalizar: "Recolección completada"
```

### **5. Integración con App Móvil del Conductor**
```typescript
// mobile-app/screens/HorariosScreen.tsx

interface JornadaDia {
  id: number;
  horario_id: number;
  sector_nombre: string;
  hora_inicio: string;
  hora_fin: string;
  estado: 'programada' | 'en_curso' | 'completada';
  distancia_km: number;
}

const HorariosScreen = () => {
  const [jornada, setJornada] = useState<JornadaDia[]>([]);
  
  useEffect(() => {
    // Obtener agenda del día
    fetch('/api/horarios/ejecuciones/hoy?conductor_id=' + conductorId)
      .then(res => res.json())
      .then(data => setJornada(data));
  }, []);
  
  const iniciarEjecucion = async (ejecucionId: number) => {
    await fetch(`/api/horarios/ejecuciones/${ejecucionId}/iniciar`, {
      method: 'PATCH',
      body: JSON.stringify({
        camion_placa: 'ABC-1234'
      })
    });
    
    // Iniciar tracking GPS
    startGPSTracking(ejecucionId);
  };
  
  const startGPSTracking = (ejecucionId: number) => {
    // Enviar ubicación cada 30 segundos
    const interval = setInterval(async () => {
      const position = await getCurrentPosition();
      
      await fetch(`/api/horarios/ejecuciones/${ejecucionId}/tracking`, {
        method: 'POST',
        body: JSON.stringify({
          lat: position.coords.latitude,
          lon: position.coords.longitude,
          velocidad: position.coords.speed
        })
      });
    }, 30000);
  };
  
  return (
    <View>
      {jornada.map(ejecucion => (
        <Card key={ejecucion.id}>
          <Text>{ejecucion.hora_inicio} - {ejecucion.hora_fin}</Text>
          <Text>{ejecucion.sector_nombre}</Text>
          <Button 
            onPress={() => iniciarEjecucion(ejecucion.id)}
            disabled={ejecucion.estado !== 'programada'}
          >
            Iniciar Ruta
          </Button>
        </Card>
      ))}
    </View>
  );
};
```

### **6. Dashboard Administrativo**
```tsx
// admin-dashboard/components/HorariosWidget.tsx

const HorariosWidget = () => {
  const [resumen, setResumen] = useState<ResumenDiario>();
  
  useEffect(() => {
    fetch('/api/horarios/estadisticas/resumen-diario')
      .then(res => res.json())
      .then(data => setResumen(data));
  }, []);
  
  return (
    <Card title="Resumen del Día">
      <Grid container spacing={2}>
        <Grid item xs={3}>
          <Metric
            label="Programadas"
            value={resumen?.total_programadas}
            color="blue"
          />
        </Grid>
        <Grid item xs={3}>
          <Metric
            label="Completadas"
            value={resumen?.completadas}
            color="green"
          />
        </Grid>
        <Grid item xs={3}>
          <Metric
            label="En Curso"
            value={resumen?.en_curso}
            color="orange"
          />
        </Grid>
        <Grid item xs={3}>
          <Metric
            label="Cumplimiento"
            value={`${resumen?.porcentaje_cumplimiento}%`}
            color="purple"
          />
        </Grid>
      </Grid>
      
      <LineChart
        data={historicoCumplimiento}
        xAxis="fecha"
        yAxis="cumplimiento"
      />
    </Card>
  );
};
```

---

## 🧪 Testing

### **Probar Endpoints Manualmente**
```bash
# 1. Crear sector
curl -X POST http://localhost:8000/api/horarios/sectores \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "La Matriz",
    "zona": "occidental",
    "poligono": {
      "type": "Polygon",
      "coordinates": [[[-78.62, -0.93], [-78.61, -0.93], [-78.61, -0.92], [-78.62, -0.92], [-78.62, -0.93]]]
    },
    "coordenadas_centro": {
      "type": "Point",
      "coordinates": [-78.615, -0.925]
    },
    "poblacion_estimada": 5000,
    "cantidad_viviendas": 1200
  }'

# 2. Crear horario
curl -X POST http://localhost:8000/api/horarios \
  -H "Content-Type: application/json" \
  -d '{
    "sector_id": 1,
    "dias_semana": [1, 3, 5],
    "hora_inicio": "06:00",
    "hora_fin": "08:00",
    "tipo": "domestica",
    "camion_tipo": "posterior",
    "fecha_inicio_vigencia": "2026-01-06"
  }'

# 3. Ver horarios
curl http://localhost:8000/api/horarios

# 4. Ver agenda de hoy
curl http://localhost:8000/api/horarios/ejecuciones/hoy

# 5. Iniciar ejecución
curl -X PATCH http://localhost:8000/api/horarios/ejecuciones/1/iniciar \
  -H "Content-Type: application/json" \
  -d '{
    "camion_placa": "ABC-1234"
  }'

# 6. Enviar tracking
curl -X POST http://localhost:8000/api/horarios/ejecuciones/1/tracking \
  -H "Content-Type: application/json" \
  -d '{
    "lat": -0.9322,
    "lon": -78.6170,
    "velocidad": 15.5
  }'

# 7. Finalizar ejecución
curl -X PATCH http://localhost:8000/api/horarios/ejecuciones/1/finalizar \
  -H "Content-Type: application/json" \
  -d '{
    "toneladas_recolectadas": 2.5,
    "viviendas_atendidas": 180,
    "observaciones": "Completado sin incidentes"
  }'

# 8. Ver estadísticas
curl http://localhost:8000/api/horarios/estadisticas/resumen-diario?fecha=2026-01-06
```

---

## 📊 Estructura de Base de Datos

```
sectores
├── id (PK)
├── nombre (UNIQUE)
├── zona (oriental/occidental)
├── poligono (GEOMETRY Polygon)
├── coordenadas_centro (GEOMETRY Point)
└── poblacion_estimada

horarios_recoleccion
├── id (PK)
├── sector_id (FK → sectores)
├── dias_semana ("1,3,5")
├── hora_inicio, hora_fin
├── tipo (domestica/comercial/barrido)
├── conductor_id (FK → conductores)
├── ruta_optimizada (GEOMETRY LineString)
└── activo

ejecuciones_horario
├── id (PK)
├── horario_id (FK → horarios_recoleccion)
├── fecha_programada
├── fecha_inicio_real, fecha_fin_real
├── conductor_id (FK → conductores)
├── estado (programada/en_curso/completada/atrasada)
├── porcentaje_cumplimiento
├── ruta_recorrida (GEOMETRY LineString)
├── toneladas_recolectadas
└── viviendas_atendidas

puntos_tracking_horario
├── id (PK)
├── ejecucion_id (FK → ejecuciones_horario)
├── punto (GEOMETRY Point)
├── timestamp
└── velocidad

suspensiones_horario
├── id (PK)
├── horario_id (FK → horarios_recoleccion)
├── fecha_suspension
├── motivo
└── fecha_recuperacion
```

---

## 🎯 Checklist de Implementación

- [x] Modelos SQLAlchemy
- [x] Schemas Pydantic
- [x] Router FastAPI con 20+ endpoints
- [x] Migración SQL con PostGIS
- [x] Documentación completa
- [ ] Aplicar migración en BD
- [ ] Implementar CRON job programación semanal
- [ ] Implementar CRON job detección retrasos
- [ ] Sistema de notificaciones push
- [ ] Integración app móvil conductor
- [ ] Dashboard administrativo
- [ ] Tests unitarios
- [ ] Tests de integración

---

## 📚 Recursos Adicionales

- **Documentación API**: http://localhost:8000/docs
- **Archivo de documentación**: `SISTEMA_HORARIOS.md`
- **Migración SQL**: `migrations/004_sistema_horarios.sql`
- **Schemas**: `app/schemas/horarios.py`
- **Router**: `app/routers/horarios.py`
- **Modelos**: `app/models.py` (líneas 300+)

---

**✅ Sistema listo para probar y extender!**
