# 🐳 Guía de Despliegue con Docker

## 📋 Requisitos Previos

- Docker Desktop instalado (Windows/Mac) o Docker Engine (Linux)
- Docker Compose v2.0+
- Al menos 4GB de RAM disponible
- 5GB de espacio en disco

## 🚀 Inicio Rápido

### 1. Configurar variables de entorno

```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Editar .env con tus credenciales
# Asegúrate de configurar DB_URL y JWT_SECRET
```

### 2. Construir y ejecutar los servicios

```bash
# Construir las imágenes
docker-compose build

# Iniciar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f
```

### 3. Verificar que todo está funcionando

```bash
# Verificar estado de los contenedores
docker-compose ps

# Verificar backend
curl http://localhost:8081/health

# Verificar OSRM
curl http://localhost:5000/health

# Acceder a Swagger
# Abrir en navegador: http://localhost:8081/docs
```

## 📦 Servicios Incluidos

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| **backend** | 8081 | API FastAPI con sistema de incidencias y conductores |
| **osrm** | 5000 | Motor de enrutamiento OSRM |
| **rabbitmq** | 5672, 15672 | Cola de mensajes (opcional) |

## 🔧 Comandos Útiles

### Gestión de contenedores

```bash
# Iniciar servicios
docker-compose up -d

# Detener servicios
docker-compose down

# Detener y eliminar volúmenes
docker-compose down -v

# Reiniciar un servicio específico
docker-compose restart backend

# Ver logs de un servicio
docker-compose logs -f backend

# Ver logs en tiempo real de todos los servicios
docker-compose logs -f
```

### Construcción y actualización

```bash
# Reconstruir imagen del backend
docker-compose build backend

# Reconstruir sin caché
docker-compose build --no-cache

# Actualizar y reiniciar
docker-compose up -d --build
```

### Acceso a contenedores

```bash
# Acceder al shell del backend
docker-compose exec backend bash

# Acceder al shell de Python
docker-compose exec backend python

# Ejecutar un comando en el backend
docker-compose exec backend python -c "print('Hello')"
```

### Gestión de base de datos

```bash
# Ejecutar migraciones
docker-compose exec backend alembic upgrade head

# Ver estado de migraciones
docker-compose exec backend alembic current

# Crear nueva migración
docker-compose exec backend alembic revision --autogenerate -m "mensaje"
```

## 🔍 Monitoreo y Debug

### Ver estado de salud

```bash
# Estado de todos los contenedores
docker-compose ps

# Inspeccionar un contenedor
docker inspect epagal-backend

# Ver recursos utilizados
docker stats
```

### Logs y debugging

```bash
# Logs completos
docker-compose logs

# Últimas 100 líneas
docker-compose logs --tail=100

# Logs de un servicio específico
docker-compose logs backend

# Seguir logs en tiempo real
docker-compose logs -f backend
```

## 🌐 Acceso a Servicios

Una vez iniciado, puedes acceder a:

- **API Backend:** http://localhost:8081
- **Swagger UI:** http://localhost:8081/docs
- **ReDoc:** http://localhost:8081/redoc
- **OSRM:** http://localhost:5000
- **RabbitMQ Management:** http://localhost:15672 (usuario: tesis, password: tesis)

## 🛠️ Desarrollo Local

Para desarrollo con hot-reload:

```bash
# El volumen ya está configurado en docker-compose.yml
# Solo necesitas editar los archivos localmente y se reflejarán automáticamente

# Para desarrollo, asegúrate de que el uvicorn tenga --reload
# Modifica el Dockerfile si es necesario
```

## 🗄️ Volúmenes Persistentes

Los datos se almacenan en:

- `./osrm-ecuador`: Datos de OSRM (mapeado a host)
- `rabbitmq-data`: Datos de RabbitMQ (volumen Docker)

## 🔐 Seguridad

### Variables de entorno sensibles

**IMPORTANTE:** Nunca commitear el archivo `.env` con credenciales reales.

```bash
# .env debe contener:
DB_URL=postgresql://usuario:password@host/db
JWT_SECRET=cambiar_este_secreto_en_produccion
```

### Cambiar secretos en producción

```bash
# Generar nuevo JWT_SECRET
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Actualizar .env y reiniciar
docker-compose up -d --force-recreate backend
```

## 📊 Escalado

Para escalar el backend:

```bash
# Crear múltiples instancias del backend
docker-compose up -d --scale backend=3

# Nota: Necesitarás configurar un load balancer (nginx, traefik, etc.)
```

## 🧹 Limpieza

```bash
# Detener y eliminar contenedores
docker-compose down

# Eliminar también volúmenes
docker-compose down -v

# Eliminar imágenes no utilizadas
docker image prune -a

# Limpieza completa del sistema Docker
docker system prune -a --volumes
```

## 🚨 Troubleshooting

### El backend no inicia

```bash
# Ver logs detallados
docker-compose logs backend

# Verificar variables de entorno
docker-compose exec backend env | grep DB_URL

# Verificar conectividad a la base de datos
docker-compose exec backend python -c "import psycopg2; print('DB OK')"
```

### OSRM no responde

```bash
# Verificar que los archivos OSRM existen
ls -lh osrm-ecuador/

# Reiniciar OSRM
docker-compose restart osrm

# Ver logs de OSRM
docker-compose logs osrm
```

### Error de permisos

```bash
# En Linux, puede ser necesario dar permisos
sudo chown -R $USER:$USER osrm-ecuador/

# O ejecutar con permisos
sudo docker-compose up -d
```

### Puerto ya en uso

```bash
# Ver qué está usando el puerto 8081
# Windows PowerShell
netstat -ano | findstr :8081

# Linux/Mac
lsof -i :8081

# Cambiar puerto en docker-compose.yml
ports:
  - "8082:8081"  # Host:Container
```

## 📝 Notas Importantes

1. **Primera ejecución**: La primera vez puede tardar varios minutos en descargar imágenes y construir.

2. **Archivos OSRM**: Los archivos `.osrm.*` deben existir en `osrm-ecuador/` antes de iniciar OSRM.

3. **Base de datos**: Este setup usa PostgreSQL en Neon (cloud). Para DB local, agrega servicio postgres en docker-compose.

4. **RabbitMQ**: Es opcional. Si no lo necesitas, comenta el servicio en docker-compose.yml.

5. **Desarrollo**: Los cambios en código Python se reflejan automáticamente por el volumen montado.

## 🎯 Comandos Resumidos

```bash
# Setup inicial
cp .env.example .env
docker-compose build
docker-compose up -d

# Verificar
docker-compose ps
curl http://localhost:8081/health

# Ver logs
docker-compose logs -f

# Detener
docker-compose down
```

## 📚 Recursos Adicionales

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI in Docker](https://fastapi.tiangolo.com/deployment/docker/)
- [OSRM Backend](http://project-osrm.org/)
