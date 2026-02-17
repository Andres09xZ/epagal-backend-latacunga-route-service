# 🚀 Guía de Despliegue en Render

## 📋 Prerequisitos

- Cuenta en [Render.com](https://render.com)
- Repositorio de GitHub conectado
- Imagen Docker publicada en Docker Hub: `mrengineer09/epagal-backend-routing:latest`
- Base de datos PostgreSQL (Neon Cloud ya configurada)

## 🎯 Opción 1: Deploy desde Docker Hub (Recomendado - Más Rápido)

### Paso 1: Crear Web Service en Render

1. Ve a tu [Dashboard de Render](https://dashboard.render.com/)
2. Haz clic en **"New +"** → **"Web Service"**
3. Selecciona **"Deploy an existing image from a registry"**

### Paso 2: Configurar la Imagen Docker

```
Image URL: mrengineer09/epagal-backend-routing:latest
```

- **Name:** `epagal-backend-latacunga`
- **Region:** Oregon (us-west) o la más cercana
- **Instance Type:** Free

### Paso 3: Configurar Variables de Entorno

Agrega las siguientes **Environment Variables**:

```bash
# Base de Datos (¡IMPORTANTE! Usar tu DB de Neon)
DB_URL=postgresql://<TU_USUARIO>:<TU_PASSWORD>@<TU_ENDPOINT>.neon.tech/neondb?sslmode=require&channel_binding=require

# JWT Secret (Cambiar por uno nuevo para producción)
JWT_SECRET=<GENERA_UN_SECRETO_SEGURO_AQUI>

# RabbitMQ (Deshabilitado temporalmente - no incluido en imagen)
# RABBITMQ_URL=amqp://guest:guest@localhost:5672/

# Puerto
PORT=8081

# OSRM - Usar servicio público (tu propio OSRM requiere otro servicio)
OSRM_URL=http://router.project-osrm.org

# CORS - Tu frontend
ALLOWED_ORIGINS=https://tesis-1-z78t.onrender.com,capacitor://localhost,ionic://localhost

# Ambiente
ENV=production
```

### Paso 4: Configurar Health Check

```
Health Check Path: /health
```

### Paso 5: Deploy

1. Haz clic en **"Create Web Service"**
2. Espera 3-5 minutos mientras Render descarga la imagen y arranca el servicio
3. Tu API estará disponible en: `https://epagal-backend-latacunga.onrender.com`

---

## 🎯 Opción 2: Deploy desde GitHub (Build en Render)

### Paso 1: Push render.yaml al Repositorio

```powershell
git add render.yaml
git commit -m "Add Render deployment configuration"
git push origin main
```

### Paso 2: Crear Blueprint en Render

1. En Render Dashboard → **"New +"** → **"Blueprint"**
2. Conecta tu repositorio de GitHub
3. Selecciona el repositorio: `Andres09xZ/epagal-backend-latacunga-route-service`
4. Render detectará automáticamente el `render.yaml`

### Paso 3: Configurar Variables Sensibles

Render te pedirá configurar manualmente:
- `DB_URL` - Tu connection string de Neon
- `JWT_SECRET` - Tu secreto JWT

### Paso 4: Deploy

Render construirá la imagen usando tu Dockerfile y desplegará el servicio.

---

## 🔧 Configuración Post-Deploy

### Actualizar Frontend

Una vez desplegado, actualiza tu frontend con la nueva URL del backend:

```typescript
// En tu app móvil/frontend
const API_BASE_URL = 'https://epagal-backend-latacunga.onrender.com/api';
```

### Probar Endpoints

```bash
# Health Check
curl https://epagal-backend-latacunga.onrender.com/health

# Login
curl -X POST https://epagal-backend-latacunga.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"nombre_usuario":"admin","password":"admin123"}'

# Documentación
https://epagal-backend-latacunga.onrender.com/docs
```

---

## 🎛️ OSRM en Producción

### Opción A: Usar OSRM Público (Actual)
✅ **Ya configurado** con `http://router.project-osrm.org`
- ✅ Gratis
- ⚠️ Sin garantía de disponibilidad
- ⚠️ Limitado a mapa mundial (puede que no tenga todos los caminos de Ecuador)

### Opción B: Desplegar tu Propio OSRM en Render

Si quieres usar tus datos de Ecuador, necesitas crear un **segundo servicio**:

1. **Crear Dockerfile para OSRM:**

```dockerfile
FROM osrm/osrm-backend:latest

WORKDIR /data

# Copiar archivos pre-procesados de Ecuador
COPY osrm-ecuador/ecuador-latest.osrm.* /data/

# Exponer puerto
EXPOSE 5000

# Ejecutar OSRM
CMD ["osrm-routed", "--algorithm", "mld", "/data/ecuador-latest.osrm"]
```

2. **Deploy OSRM Service:**
   - New Web Service en Render
   - Name: `epagal-osrm-ecuador`
   - Type: Docker
   - Port: 5000
   - Plan: Starter ($7/mes - Free no tiene suficiente RAM)

3. **Actualizar Backend:**
```bash
OSRM_URL=https://epagal-osrm-ecuador.onrender.com
```

---

## 📊 Monitoreo

### Logs en Tiempo Real
```
Render Dashboard → Tu servicio → Logs
```

### Métricas
```
Render Dashboard → Tu servicio → Metrics
```

### Reiniciar Servicio
```
Render Dashboard → Tu servicio → Manual Deploy → "Deploy latest commit"
```

---

## 🚨 Troubleshooting

### Error: Database Connection Failed
```bash
# Verificar que DB_URL esté correctamente configurada
# Neon requiere SSL: sslmode=require
```

### Error: OSRM Service Unreachable
```bash
# Si usas OSRM público, verifica conectividad
# Si usas tu propio OSRM, asegúrate que el servicio esté corriendo
```

### Error: CORS Blocked
```bash
# Verificar ALLOWED_ORIGINS incluya tu frontend
ALLOWED_ORIGINS=https://tesis-1-z78t.onrender.com
```

---

## 💰 Costos

### Plan Free (Actual)
- ✅ Backend: **$0/mes**
- ⚠️ Se duerme después de 15 min de inactividad
- ⚠️ Tarda 30-60 segundos en despertar
- ✅ Suficiente para pruebas y demos

### Plan Starter ($7/mes)
- ✅ Siempre activo
- ✅ Sin cold starts
- ✅ Mejor performance
- ✅ Ideal para producción

---

## 🎉 Siguiente Paso

Una vez desplegado, actualiza tu documentación con la URL de producción:

```markdown
# API Endpoints

**Base URL (Producción):** https://epagal-backend-latacunga.onrender.com/api
**Base URL (Desarrollo):** http://localhost:8081/api
```

---

## 📱 Integración con App Móvil

```typescript
// src/config/api.ts
export const API_CONFIG = {
  baseURL: __DEV__ 
    ? 'http://localhost:8081/api'
    : 'https://epagal-backend-latacunga.onrender.com/api',
  timeout: 10000,
};
```

**¡Listo para producción! 🚀**
