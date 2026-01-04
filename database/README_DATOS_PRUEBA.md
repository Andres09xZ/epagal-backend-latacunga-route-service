# Insertar Datos de Prueba - EPAGAL Backend

## ⚠️ ERROR 404 en Endpoints

Si ves errores 404 en los endpoints de horarios y tracking, necesitas:

1. **Verificar que las tablas existen** en la base de datos de Supabase
2. **Insertar datos de ejemplo** para poder probar la aplicación

## 📋 Pasos para Insertar Datos de Prueba

### Opción 1: SQL Editor de Supabase (RECOMENDADO)

1. Ve a tu proyecto en Supabase: https://supabase.com/dashboard
2. Click en "SQL Editor" en el menú lateral
3. Click en "+ New query"
4. Copia y pega el contenido de uno de estos archivos:
   - `database/insert_basic_test_data.sql` (solo sectores y horarios)
   - `database/insert_test_data.sql` (incluye ejecuciones y tracking GPS)
5. Click en "Run" para ejecutar
6. Verifica los resultados en la pestaña "Results"

### Opción 2: Script Python (requiere DATABASE_URL)

```bash
# Configurar DATABASE_URL
export DATABASE_URL="postgresql://..."

# Ejecutar script
python populate_test_data.py
```

## 🔍 Verificar que los Datos se Insertaron

### En Supabase

1. Ve a "Table Editor"
2. Verifica estas tablas tienen datos:
   - `sectores` (debe tener 4 sectores)
   - `horarios_recoleccion` (debe tener 4 horarios)
   - `ejecuciones_horario` (opcional, para tracking)

### En el Backend

Ejecuta el script de verificación:

```bash
python check_endpoints.py
```

Deberías ver:
- ✓ `/api/horarios/sectores` retorna 4 sectores
- ✓ `/api/horarios` retorna 4 horarios
- ✓ `/api/tracking/activos` retorna lista de ejecuciones activas

## 📊 Datos de Ejemplo Incluidos

### Sectores
- **Centro Histórico** (Zona Occidental)
- **La Laguna** (Zona Occidental)
- **San Felipe** (Zona Oriental)
- **Eloy Alfaro** (Zona Oriental)

### Horarios de Recolección
1. Centro Histórico: Lunes/Miércoles/Viernes 07:00-12:00 (Orgánico)
2. La Laguna: Martes/Jueves 08:00-13:00 (Reciclable)
3. San Felipe: Lunes a Viernes 06:30-11:30 (Común)
4. Eloy Alfaro: Miércoles/Sábado 07:30-12:30 (Orgánico)

## 🐛 Troubleshooting

### Error 500 en `/api/horarios/sectores`

**Causa**: La tabla `sectores` no existe o tiene un schema diferente

**Solución**:
1. Ve a Supabase SQL Editor
2. Verifica que la tabla existe: `SELECT * FROM sectores LIMIT 1;`
3. Si no existe, ejecuta las migraciones desde `database/migrations/`

### Error 404 Persistente

**Causa**: El backend no se ha redesplegado con los nuevos routers

**Solución**:
1. Verifica el deployment en GitHub Actions:
   https://github.com/Andres09xZ/epagal-backend-latacunga-route-service/actions
2. Verifica que la versión del backend sea 2.0.1:
   ```bash
   curl https://epagal-backend-routing-latest.onrender.com/health
   ```
3. Si la versión es menor a 2.0.1, espera a que termine el deployment

### Datos Vacíos en los Endpoints

**Causa**: Los datos de ejemplo no se insertaron correctamente

**Solución**:
1. Ejecuta `database/insert_basic_test_data.sql` en Supabase
2. Verifica que los sectores se insertaron:
   ```sql
   SELECT COUNT(*) FROM sectores;
   ```
3. Si el conteo es 0, revisa los logs de errores en Supabase

## 🎯 Testing en Frontend

Una vez insertados los datos, prueba en el frontend:

1. **Horarios**: https://tesis-1-z78t.onrender.com/horarios
   - Debe cargar la tabla de sectores
   - Debe mostrar 4 horarios existentes
   - Botón "Nuevo Horario" debe abrir el diálogo

2. **Tracking**: https://tesis-1-z78t.onrender.com/tracking
   - Debe mostrar el mapa con Leaflet
   - Si hay ejecuciones activas, debe mostrar la lista de camiones
   - Si no hay ejecuciones, muestra mensaje "No hay camiones en operación"

## 📝 Notas

- Los datos de ejemplo usan coordenadas reales de Latacunga, Ecuador (-0.93, -78.61)
- Las placas de camiones son ficticias (ABC-1234, XYZ-5678, etc.)
- Los horarios están diseñados para cubrir toda la semana
- Las ejecuciones de tracking tienen timestamps relativos (30-45 minutos atrás)
