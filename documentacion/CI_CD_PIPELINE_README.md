# 🚀 EPAGAL Backend - CI/CD Pipeline Documentation

## 📋 Tabla de Contenidos

1. [Descripción General](#descripción-general)
2. [Arquitectura del Pipeline](#arquitectura-del-pipeline)
3. [Flujo de Trabajo Detallado](#flujo-de-trabajo-detallado)
4. [Configuración Requerida](#configuración-requerida)
5. [Jobs del Workflow](#jobs-del-workflow)
6. [Troubleshooting](#troubleshooting)
7. [Monitoreo y Logs](#monitoreo-y-logs)
8. [Mejores Prácticas](#mejores-prácticas)
9. [Métricas del Pipeline](#métricas-del-pipeline)
10. [Enlaces Útiles](#enlaces-útiles)

---

## 📌 Descripción General

El sistema **EPAGAL Backend** utiliza un pipeline **CI/CD (Continuous Integration/Continuous Deployment)** completamente automatizado que:

- 🔄 Detecta cambios en el repositorio GitHub
- 🐳 Construye una imagen Docker optimizada
- 📦 Empuja la imagen a Docker Hub
- 🚀 Despliega automáticamente en Render
- ✅ Verifica la salud de la aplicación

### Información del Pipeline

| Aspecto | Valor |
|---------|-------|
| **Estado** | ✅ Producción Activo |
| **Plataformas** | GitHub Actions → Docker Hub → Render |
| **Tiempo Promedio** | 5-10 minutos por ciclo |
| **Archivo de Configuración** | `.github/workflows/deploy.yml` |
| **Imagen Docker** | `mrengineer09/epagal-backend-routing:latest` |
| **Producción** | `https://epagal-backend-routing-latest.onrender.com` |

---

## 🏗️ Arquitectura del Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│ DEVELOPER PUSH A MAIN                                           │
│ (git push origin main)                                          │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
         ┌────────────────────┐
         │ GitHub Actions     │
         │ Detecta evento     │
         │ (push/PR/manual)   │
         └────────┬───────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
    ▼             ▼             ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│ PR       │ │ Push     │ │ Manual   │
│ a main   │ │ a main   │ │ trigger  │
└─────┬────┘ └────┬─────┘ └────┬─────┘
      │           │            │
      └─────┬─────┴────────────┘
            │
            ▼
┌───────────────────────────────────────┐
│ JOB 1: BUILD AND PUSH (3-5 min)       │
│ ├─ Checkout código                    │
│ ├─ Setup Docker Buildx                │
│ ├─ Login Docker Hub                   │
│ ├─ Extract metadata                   │
│ └─ Build & Push imagen                │
└───────────┬───────────────────────────┘
            │
            ├─ PR o Manual? → STOP
            │
            ├─ Push a main? → DEPLOY
            │
            ▼
┌───────────────────────────────────────┐
│ JOB 2: DEPLOY TO RENDER (2-5 min)     │
│ ├─ Validar secretos                   │
│ ├─ Deploy a Render                    │
│ ├─ Recolectar logs                    │
│ └─ Health check (5 reintentos)        │
└───────────┬───────────────────────────┘
            │
            ▼
┌───────────────────────────────────────┐
│ JOB 3: NOTIFY (~5 seg)                │
│ └─ Mostrar resumen final              │
└───────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────┐
│ APLICACIÓN EN PRODUCCIÓN              │
│ https://epagal-backend-routing-...    │
└───────────────────────────────────────┘
```

---

## 🔄 Flujo de Trabajo Detallado

### 1. Triggers (Activadores)

El workflow se activa en tres casos:

```yaml
on:
  push:
    branches:
      - main           # ✅ Build + Push + Deploy
  pull_request:
    branches:
      - main           # ✅ Build + Push (NO Deploy)
  workflow_dispatch:   # ✅ Manual trigger: Build + Push (NO Deploy)
```

| Evento | Build | Push | Deploy |
|--------|-------|------|--------|
| Push a main | ✅ | ✅ | ✅ |
| PR a main | ✅ | ✅ | ❌ |
| Manual trigger | ✅ | ✅ | ❌ |

### 2. Variables de Entorno Globales

```yaml
env:
  DOCKER_IMAGE: mrengineer09/epagal-backend-routing
  DOCKER_TAG: latest
```

Estas variables se usan en todo el pipeline para referenciar la imagen Docker.

---

## 💼 Jobs del Workflow

### JOB 1: Build Docker Image and Push to Docker Hub

**Nombre:** `build-and-push`  
**Runner:** `ubuntu-latest`  
**Duración:** ~3-5 minutos  
**Archivo:** `.github/workflows/deploy.yml` líneas 9-64

#### Paso 1: Checkout code

```yaml
- name: Checkout code
  uses: actions/checkout@v4
```

**¿Qué hace?**
- Descarga el código del repositorio al runner
- Prepara el ambiente para el build

**Salida esperada:**
```
✓ Fetched code from main branch
✓ Code ready for build
```

---

#### Paso 2: Set up Docker Buildx

```yaml
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3
```

**¿Qué hace?**
- Instala Docker Buildx (herramienta avanzada de construcción)
- Prepara builder para soportar múltiples plataformas

**Beneficios:**
- ✅ Construcción más rápida (2-3 minutos)
- ✅ Caché de capas Docker
- ✅ Soporte multi-arquitectura (AMD64, ARM64, etc)

---

#### Paso 3: Login to Docker Hub

```yaml
- name: Login to Docker Hub
  uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKER_USERNAME }}
    password: ${{ secrets.DOCKER_PASSWORD }}
```

**¿Qué hace?**
- Autentica con Docker Hub usando credenciales
- Permite empujar imágenes al repositorio privado

**Secretos requeridos:**
- `DOCKER_USERNAME` - Tu usuario de Docker Hub
- `DOCKER_PASSWORD` - Token de acceso (NO contraseña real)

**Cómo obtener el token:**
```
Docker Hub → Account Settings → Security → New Access Token
```

---

#### Paso 4: Extract Docker Metadata

```yaml
- name: Extract Docker metadata
  id: meta
  uses: docker/metadata-action@v5
  with:
    images: ${{ env.DOCKER_IMAGE }}
    tags: |
      type=raw,value=latest
      type=sha,prefix={{branch}}-
      type=ref,event=branch
      type=ref,event=pr
```

**¿Qué hace?**
- Genera múltiples tags para la imagen Docker
- Crea identificadores únicos para cada build

**Tags generados:**

| Tipo | Ejemplo | Uso |
|------|---------|-----|
| `latest` | `mrengineer09/epagal-backend-routing:latest` | Última versión (producción) |
| SHA | `mrengineer09/epagal-backend-routing:main-abc123` | Revertir a commit específico |
| Branch | `mrengineer09/epagal-backend-routing:main` | Por rama |
| PR | `mrengineer09/epagal-backend-routing:123` | Por número de PR (testing) |

---

#### Paso 5: Build and Push Docker Image

```yaml
- name: Build and push Docker image
  uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: ${{ steps.meta.outputs.tags }}
    labels: ${{ steps.meta.outputs.labels }}
    cache-from: type=registry,ref=${{ env.DOCKER_IMAGE }}:buildcache
    cache-to: type=registry,ref=${{ env.DOCKER_IMAGE }}:buildcache,mode=max
    platforms: linux/amd64
```

**¿Qué hace?**

| Parámetro | Descripción |
|-----------|------------|
| `context: .` | Usa el Dockerfile desde raíz del repo |
| `push: true` | Sube imagen a Docker Hub |
| `tags` | Etiqueta con todos los tags generados |
| `cache-from/to` | Usa caché anterior para acelerar builds |
| `platforms: linux/amd64` | Arquitectura soportada |

**Proceso:**
1. Lee `Dockerfile` desde raíz del repo
2. Construye imagen capa por capa
3. Usa caché anterior para capas sin cambios
4. Empuja todas las versiones a Docker Hub

**Salida esperada:**
```
✓ Building...
✓ Pushing docker image to registry
✓ Built and pushed: mrengineer09/epagal-backend-routing:latest
✓ Built and pushed: mrengineer09/epagal-backend-routing:main-abc123def456
✓ Built and pushed: mrengineer09/epagal-backend-routing:main
```

---

#### Paso 6: Image uploaded successfully

```yaml
- name: Image uploaded successfully
  run: |
    echo "Image uploaded to Docker Hub"
    echo "Image: ${{ env.DOCKER_IMAGE }}:${{ env.DOCKER_TAG }}"
```

**Resultado final:**
```
Image uploaded to Docker Hub
Image: mrengineer09/epagal-backend-routing:latest
```

---

### JOB 2: Deploy to Render

**Nombre:** `deploy-to-render`  
**Runner:** `ubuntu-latest`  
**Dependencias:** `build-and-push` (debe completarse exitosamente)  
**Condición:** Solo si es push a main  
**Duración:** ~2-5 minutos  
**Archivo:** `.github/workflows/deploy.yml` líneas 66-413

#### Condiciones de Ejecución

```yaml
needs: build-and-push
if: github.ref == 'refs/heads/main' && github.event_name == 'push'
```

**Solo ejecuta si:**
- ✅ Job `build-and-push` fue exitoso
- ✅ Es un push (NO pull request)
- ✅ Es a la rama `main`

---

#### Paso 1: Validate Secrets Configuration

Verifica que todos los secretos están configurados y son válidos.

**Validaciones:**
1. ✅ `RENDER_SERVICE_ID` existe
2. ✅ `RENDER_API_KEY` existe
3. ✅ Conexión a Render API funciona (HTTP 200)
4. ✅ Autenticación válida

**Secretos requeridos:**

| Secreto | Descripción | Dónde obtener |
|---------|------------|--------------|
| `RENDER_SERVICE_ID` | ID del servicio en Render | Render Dashboard → Service Settings |
| `RENDER_API_KEY` | Token para API de Render | Render Dashboard → Account → API tokens |

**Cómo agregar secretos en GitHub:**
```
GitHub → Settings → Secrets and variables → Actions → New repository secret
```

---

#### Paso 2: Deploy to Render with Automatic Retry

```yaml
- name: Deploy to Render with automatic retry and monitoring
  id: render_deploy
  uses: JorgeLNJunior/render-deploy@v1.4.7
  continue-on-error: true
  with:
    service_id: ${{ secrets.RENDER_SERVICE_ID }}
    api_key: ${{ secrets.RENDER_API_KEY }}
    clear_cache: true
    wait_deploy: true
    github_deployment: true
    deployment_environment: 'production'
    github_token: ${{ secrets.GITHUB_TOKEN }}
```

**¿Qué hace?**
1. Se conecta a Render API
2. Dispara el deployment del servicio
3. Espera a que la nueva imagen se descargue
4. Reinicia el servicio
5. Crea un registro en GitHub Deployments

**Salida esperada:**
```
✓ Deploy triggered successfully
✓ Waiting for deployment to complete...
✓ Deployment completed
✓ Service ID: srv_xxx
✓ Deployment ID: deploy_xxx
```

---

#### Paso 3: Retrieve Service Logs and Deployment Information

Este es el paso **MÁS importante** para diagnosticar problemas.

**¿Qué hace?**

1. **Service Information** - Obtiene información del servicio
2. **Recent Deploys** - Últimos 3 deployments
3. **Service Logs** - Intenta obtener logs de múltiples fuentes
4. **Health Check** - Verifica que endpoints responden
5. **Docker Hub Verification** - Verifica que imagen existe
6. **Summary** - Resumen final con diagnóstico

**Intenta obtener logs de:**
1. Logs endpoint → Si funciona, muestra últimos 200 logs
2. Events endpoint → Si 1 falla, intenta events
3. Deploy-specific logs → Si 2 falla, intenta deploy logs
4. Health check directo → Si 3 falla, prueba conectividad

**Filtra y destaca errores críticos:**
- `ModuleNotFoundError` → Falta dependencia Python
- `ImportError` → Error en import de módulos
- `Database connection errors` → Problema BD
- `Port binding errors` → Puerto en uso

---

#### Paso 4: Verify Application Health

```yaml
- name: Verify application health
  if: steps.render_deploy.outcome == 'success'
  run: |
    # 5 reintentos con 10 segundos entre intentos
    # Total: máximo 50 segundos de espera
```

**¿Qué hace?**
1. Espera 10 segundos (tiempo para que Render inicie)
2. Realiza 5 intentos de health check con 10 segundos entre intentos
3. Si recibe HTTP 200: ✅ ÉXITO
4. Si no responde después de 5 intentos: ❌ FALLO

**Tests ejecutados:**
- `GET /health` → Debe retornar HTTP 200
- `GET /api/incidencias/` → Debe retornar HTTP 200
- `GET /docs` → Debe retornar HTTP 200 (Swagger)
- Base de datos → Verifica que API retorna JSON válido

---

### JOB 3: Deployment Notification

**Nombre:** `notify`  
**Runner:** `ubuntu-latest`  
**Dependencias:** `build-and-push`, `deploy-to-render`  
**Condición:** Siempre (incluso si falla)  
**Duración:** ~5 segundos  
**Archivo:** `.github/workflows/deploy.yml` líneas 415-445

**¿Qué hace?**
Muestra un resumen final del pipeline con:
- Estado de build
- Estado de deploy
- URLs útiles
- Instrucciones si algo falló

**Ejemplo de output exitoso:**
```
============================================
PIPELINE SUMMARY
============================================
Docker Build: success
Render Deploy: success
============================================

PIPELINE COMPLETED SUCCESSFULLY

Application updated on Render

Useful links:
============================================
URL: https://epagal-backend-routing-latest.onrender.com
Health: https://epagal-backend-routing-latest.onrender.com/health
API Docs: https://epagal-backend-routing-latest.onrender.com/docs
Docker Hub: https://hub.docker.com/r/mrengineer09/epagal-backend-routing
============================================
```

---

## ⚙️ Configuración Requerida

### Paso 1: Obtener Credenciales Docker Hub

1. Ve a [hub.docker.com](https://hub.docker.com)
2. Login en tu cuenta
3. Click en tu avatar → **Account Settings**
4. Click en **Security** → **New Access Token**
5. Dale nombre: `github-actions`
6. Dale permisos de **Read, Write, Delete**
7. Copia el token (único, no podrás verlo después)

**Guardar en notas temporales (no en código):**
```
DOCKER_USERNAME: tuusername
DOCKER_PASSWORD: dckr_pat_xxxxxxxxxxxxxx
```

### Paso 2: Obtener Credenciales Render

1. Ve a [render.com](https://render.com) Dashboard
2. Crea o selecciona tu servicio
3. Copia el `Service ID` (en URL: `srv_xxx`)
4. Ve a **Account Settings** → **API tokens**
5. Crea nuevo token: `github-ci-cd`
6. Copia el token

**Guardar en notas temporales:**
```
RENDER_SERVICE_ID: srv_xxx
RENDER_API_KEY: rnd_xxxxxxxxxxxxxxxxxxxx
```

### Paso 3: Agregar Secretos a GitHub

1. Ve a tu repo → **Settings** → **Secrets and variables** → **Actions**
2. Agrega los siguientes secretos:

**Opción A: Usando GitHub UI**
```
Click "New repository secret" para cada uno:
```

| Nombre | Valor | Ejemplo |
|--------|-------|---------|
| `DOCKER_USERNAME` | Tu usuario Docker Hub | `mrengineer09` |
| `DOCKER_PASSWORD` | Token Docker Hub | `dckr_pat_xxx` |
| `RENDER_API_KEY` | Token Render | `rnd_xxx` |
| `RENDER_SERVICE_ID` | ID del servicio | `srv_xxx` |

**Opción B: Usando CLI de GitHub (si tienes gh instalado)**
```bash
gh secret set DOCKER_USERNAME --body "mrengineer09"
gh secret set DOCKER_PASSWORD --body "dckr_pat_xxx"
gh secret set RENDER_API_KEY --body "rnd_xxx"
gh secret set RENDER_SERVICE_ID --body "srv_xxx"
```

### Paso 4: Verificar Dockerfile

Tu proyecto debe tener un `Dockerfile` en la raíz:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Exponer puerto (IMPORTANTE)
EXPOSE 8000

# Comando para iniciar (IMPORTANTE)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Paso 5: Verificar Archivo de Workflow

El archivo debe estar en: `.github/workflows/deploy.yml`

```bash
# Verificar que existe
ls -la .github/workflows/deploy.yml
```

---

## 🐛 Troubleshooting

### Error: "RENDER_SERVICE_ID is not configured"

**Causa:** Falta agregar el secreto en GitHub  
**Solución:**
```
GitHub → Settings → Secrets → Add RENDER_SERVICE_ID
```

---

### Error: "DOCKER_PASSWORD authentication failed"

**Causa:** Token Docker Hub incorrecto o expirado  
**Solución:**
1. Regenera token en Docker Hub
2. Actualiza secreto `DOCKER_PASSWORD` en GitHub
3. Verifica que copiaste correctamente (sin espacios)

---

### Error: "Docker image push failed"

**Causa:** Username incorrecto o permisos insuficientes  
**Solución:**
1. Verifica `DOCKER_USERNAME` coincida con Docker Hub
2. Regenera Access Token con permisos de **Read, Write, Delete**
3. Prueba login local:
```bash
docker login -u username
# Ingresa password (token)
```

---

### Error: "API connection failed (HTTP 401)"

**Causa:** Token Render API inválido  
**Solución:**
1. Regenera token en Render Dashboard
2. Copia exactamente sin espacios
3. Verifica que no esté expirado

---

### Error: "update_failed" en Render

**Causa:** Aplicación no inicia correctamente  
**Solución:** Revisa los logs (mostrados en el workflow) para:
- `ModuleNotFoundError` → Falta instalar dependencia en `requirements.txt`
- `ImportError` → Error en imports
- `Database errors` → Verificar `DATABASE_URL`
- `Port binding` → Puerto 8000 ya en uso

**Para testear localmente:**
```bash
# Build imagen local
docker build -t test:latest .

# Run contenedor
docker run -p 8000:8000 -e PORT=8000 test:latest

# Probar health
curl http://localhost:8000/health
```

---

### Error: "Health check failed"

**Causa:** Endpoint `/health` no existe o no responde  
**Solución:**
1. Verifica que existe en tu código:
```python
@router.get("/health")
def health():
    return {"status": "healthy"}
```
2. Espera a que Render inicie completamente (puede tardar 1-2 minutos)
3. Revisa logs en Render Dashboard

---

### Aplicación respondió pero endpoints no funcionan

**Causa:** Problema de conexión a base de datos  
**Solución:**
1. Verifica `DATABASE_URL` en variables de entorno de Render
2. Verifica que PostGIS está configurado
3. Revisa logs para errores de BD

---

## 📊 Monitoreo y Logs

### Ver Logs en GitHub

1. Ve a tu repo → **Actions**
2. Selecciona el workflow más reciente
3. Expande cada job para ver logs detallados
4. Busca en los logs con `Ctrl+F`

### Ver Logs en Render

1. Ve a [render.com](https://render.com) Dashboard
2. Selecciona tu servicio
3. Click en **Logs** en la barra superior
4. Verás logs en tiempo real
5. Puedes descargar logs completos

### Ver Deployment History

**En Render Dashboard:**
1. Tu servicio → **Events** o **Deployments**
2. Verás historial de todos los deployments
3. Puedes revertir a versión anterior si es necesario

**En GitHub:**
1. Repo → **Actions** → Selecciona workflow
2. Verás todos los runs (ejecutadas del workflow)
3. Puedes ver detalles de cada uno

### Monitorear Docker Hub

**En Docker Hub:**
1. Repo → **Tags**
2. Verás todas las versiones (latest, main-sha, etc)
3. Puedes ver cuándo se subió cada una
4. Puedes eliminar tags antiguos (si quieres liberar espacio)

---

## ✅ Mejores Prácticas

### 1. Versionamiento de Imágenes

Siempre mantén múltiples tags:
```bash
latest              # Última versión (producción)
main-abc123         # Revertible a commit específico
main                # Rama actual
1.0.0              # Versión semántica (opcional)
```

**Ventajas:**
- Puedes revertir a versión anterior rápidamente
- Rastrabilidad de qué código está en producción
- Testing en versiones específicas

---

### 2. Monitoreo Continuo

Después del deploy:
1. ✅ Revisa health endpoint
2. ✅ Prueba endpoints críticos
3. ✅ Revisa logs en Render
4. ✅ Monitorea uso de recursos

---

### 3. Rollback Rápido

Si algo falla en producción:
```bash
# En Render Dashboard
Services → tu-servicio → Previous Deployments → Redeploy
```

Esto redeploya la versión anterior automáticamente (30 segundos típicamente).

---

### 4. Caché Efectivo

El workflow usa caché de Docker:
- Primera build: ~5 minutos
- Builds posteriores: ~2-3 minutos (si no hay cambios base)

**Cómo optimizar:**
- Cambios en código Python → Build rápido (usa caché)
- Cambios en requirements.txt → Build lento (reconstruye capas)
- Cambios en Dockerfile → Build lento (reconstruye todo)

---

### 5. Secretos Seguros

✅ **NUNCA** commits secretos en el repo  
✅ Usa GitHub Secrets para todo sensible  
✅ Rota tokens regularmente (cada 90 días)  
✅ Usa tokens específicos (NO contraseña principal)  
✅ Limita permisos del token (solo necesarios)  

---

### 6. Testing Antes de Push

Antes de hacer push:
```bash
# Build local
docker build -t test:latest .

# Run local
docker run -p 8000:8000 test:latest

# Test endpoints en otra terminal
curl http://localhost:8000/health
curl http://localhost:8000/api/incidencias/
curl http://localhost:8000/docs
```

---

### 7. Documentación de Cambios

En cada commit:
```bash
git commit -m "feat: Add new endpoint /api/rutas/new

- Descripción del cambio
- Qué pruebas ejecutaste
- Posibles efectos secundarios"
```

---

## 📈 Métricas del Pipeline

| Métrica | Valor | Notas |
|---------|-------|-------|
| Tiempo Build Docker | 2-5 min | 3-5 min si es primera vez, 1-2 min con caché |
| Tiempo Deploy Render | 1-3 min | Incluye descargar imagen y reiniciar |
| Tiempo Health Check | 0.5-1 min | 5 reintentos máximo |
| Tiempo Total | 5-10 min | Típicamente 7-8 minutos |
| Éxito Rate | >95% | Solo falla si hay error de código |
| Retries Automáticos | 5 | Para health check |

---

## 🔗 Enlaces Útiles

| Recurso | URL |
|---------|-----|
| **Repo GitHub** | https://github.com/Andres09xZ/Backend-latacunga-clean |
| **Docker Hub** | https://hub.docker.com/r/mrengineer09/epagal-backend-routing |
| **Render Dashboard** | https://dashboard.render.com |
| **Aplicación Producción** | https://epagal-backend-routing-latest.onrender.com |
| **API Docs (Swagger)** | https://epagal-backend-routing-latest.onrender.com/docs |
| **Health Check** | https://epagal-backend-routing-latest.onrender.com/health |

---

## 📝 Resumen

Este workflow CI/CD automatiza completamente el ciclo de desarrollo:

```
1. Desarrollo Local
   ↓ Escribes código
   
2. Git Push a Main
   ↓ git push origin main
   
3. GitHub Actions
   ↓ Detecta el push
   
4. Build Docker
   ↓ Construye imagen (3-5 min)
   
5. Push a Docker Hub
   ↓ Sube imagen (30 seg)
   
6. Deploy a Render
   ↓ Descarga imagen (1 min)
   
7. Health Check
   ↓ Verifica que funciona (30 seg)
   
8. Producción
   ↓ ✅ Cambios en vivo (5-10 min total)
```

**Resultado:** Cambios en producción en 5-10 minutos sin intervención manual ✅

---

## 📞 Soporte

Si tienes problemas:

1. **Revisa los logs en GitHub Actions**
2. **Revisa los logs en Render Dashboard**
3. **Busca el error específico en Troubleshooting**
4. **Verifica que todos los secretos están configurados**
5. **Prueba localmente con Docker**

---

**Última actualización:** Enero 30, 2026  
**Versión:** 1.0.0  
**Autor:** EPAGAL Development Team  
**Estado:** ✅ Producción Activo
