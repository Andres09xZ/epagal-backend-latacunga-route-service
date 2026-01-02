# 🐳 Imagen Docker - EPAGAL Backend Latacunga

## 📦 Imagen en Docker Hub

**Nombre:** `mrengineer09/epagal-backend-latacunga:latest`

**URL:** https://hub.docker.com/r/mrengineer09/epagal-backend-latacunga

---

## 🚀 Cómo usar la imagen

### 1. Descargar la imagen

```bash
docker pull mrengineer09/epagal-backend-latacunga:latest
```

### 2. Ejecutar el contenedor

```bash
docker run -d \
  --name epagal-backend \
  -p 9000:8081 \
  -e DATABASE_URL="postgresql://user:password@host/database" \
  -e SECRET_KEY="your-secret-key" \
  -e OSRM_URL="http://osrm-server:5000" \
  mrengineer09/epagal-backend-latacunga:latest
```

### 3. Usando Docker Compose (Recomendado)

Crea un archivo `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    image: mrengineer09/epagal-backend-latacunga:latest
    container_name: epagal-backend
    ports:
      - "9000:8081"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - OSRM_URL=http://osrm:5000
    depends_on:
      - osrm
    restart: unless-stopped

  osrm:
    image: osrm/osrm-backend:latest
    container_name: osrm-server
    ports:
      - "5000:5000"
    volumes:
      - ./osrm-ecuador:/data
    command: osrm-routed --algorithm=MLD /data/ecuador-latest.osrm
    restart: unless-stopped
```

Luego ejecuta:

```bash
docker-compose up -d
```

---

## 🔧 Variables de Entorno Requeridas

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `DATABASE_URL` | URL de conexión a PostgreSQL | `postgresql://user:pass@host:5432/db` |
| `SECRET_KEY` | Clave secreta para JWT | `your-super-secret-key-here` |
| `OSRM_URL` | URL del servidor OSRM | `http://localhost:5000` |

---

## 📋 Características

✅ Backend FastAPI optimizado  
✅ Gestión de incidencias ciudadanas  
✅ Generación automática de rutas  
✅ Optimización con OR-Tools  
✅ Integración con OSRM  
✅ Autenticación JWT  
✅ PostgreSQL + PostGIS  

---

## 🔗 Endpoints Principales

- **API Docs:** `http://localhost:9000/docs`
- **Health Check:** `http://localhost:9000/health`
- **Incidencias:** `http://localhost:9000/api/incidencias/`
- **Rutas:** `http://localhost:9000/api/rutas/`
- **Conductores:** `http://localhost:9000/api/conductores/`

---

## 📊 Arquitectura

```
┌─────────────────┐
│   Dashboard     │
│  (Port 8000)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│  FastAPI        │◄────►│  PostgreSQL  │
│  (Port 9000)    │      │  + PostGIS   │
└────────┬────────┘      └──────────────┘
         │
         ▼
┌─────────────────┐
│  OSRM Server    │
│  (Port 5000)    │
└─────────────────┘
```

---

## 🛠️ Desarrollo

### Actualizar la imagen

```bash
# Construir nueva versión
docker build -t mrengineer09/epagal-backend-latacunga:latest .

# Subir a Docker Hub
docker push mrengineer09/epagal-backend-latacunga:latest

# Crear tag versionado
docker tag mrengineer09/epagal-backend-latacunga:latest mrengineer09/epagal-backend-latacunga:v1.0.0
docker push mrengineer09/epagal-backend-latacunga:v1.0.0
```

---

## 📝 Changelog

### v1.0.0 (2025-12-18)
- ✅ Flujo de validación de incidencias por administrador
- ✅ Generación automática de rutas al superar umbral
- ✅ Indicador de carga en dashboard
- ✅ Corrección de estados (pendiente → validada → asignada)
- ✅ Dashboard administrativo completo
- ✅ Gestión de conductores y asignaciones

---

## 📞 Soporte

Para reportar problemas o solicitar características:
- GitHub: https://github.com/Andres09xZ/epagal-backend-latacunga-route-service
- Issues: https://github.com/Andres09xZ/epagal-backend-latacunga-route-service/issues

---

## 📄 Licencia

MIT License - EPAGAL Latacunga © 2025
