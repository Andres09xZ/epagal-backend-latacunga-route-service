# 🚀 Pipeline CI/CD - GitHub Actions

Este repositorio utiliza GitHub Actions para automatizar el proceso de build, push a Docker Hub y deploy en Render.

## 📋 Configuración de Secrets

Para que el pipeline funcione, necesitas configurar los siguientes **secrets** en tu repositorio de GitHub:

### Paso 1: Ir a Settings del Repositorio

1. Ve a tu repositorio en GitHub
2. Click en **Settings** (⚙️)
3. En el menú lateral izquierdo, click en **Secrets and variables** → **Actions**
4. Click en **New repository secret**

### Paso 2: Agregar los Secrets

Debes agregar **3 secrets**:

#### 1. `DOCKER_USERNAME`
- **Valor:** `mrengineer09` (tu usuario de Docker Hub)
- Este es tu nombre de usuario de Docker Hub

#### 2. `DOCKER_PASSWORD`
- **Valor:** Tu contraseña o **Personal Access Token** de Docker Hub
- **Recomendado:** Usar un Access Token en lugar de la contraseña
- Para crear un token:
  1. Ve a https://hub.docker.com/settings/security
  2. Click en **New Access Token**
  3. Dale un nombre (ej: "GitHub Actions")
  4. Copia el token (solo se muestra una vez)
  5. Úsalo como valor del secret

#### 3. `RENDER_DEPLOY_HOOK_URL`
- **Valor:** URL del Deploy Hook de Render
- Para obtenerla:
  1. Ve a tu servicio en Render Dashboard
  2. Click en **Settings**
  3. Scroll hasta **Deploy Hook**
  4. Click en **Create Deploy Hook** si no existe
  5. Copia la URL (ejemplo: `https://api.render.com/deploy/srv-xxxxx?key=xxxxxx`)
  6. Pégala como valor del secret

## 🔄 Cómo Funciona el Pipeline

### Trigger Automático
El pipeline se ejecuta automáticamente cuando:
- ✅ Se hace **push** a la rama `main`
- ✅ Se crea un **Pull Request** hacia `main`
- ✅ Manualmente desde la pestaña **Actions** en GitHub

### Flujo del Pipeline

```
1. 📥 Checkout del código
   ↓
2. 🐳 Build de imagen Docker
   ↓
3. ⬆️  Push a Docker Hub (latest)
   ↓
4. 🚀 Trigger de deploy en Render
   ↓
5. ✅ Notificación de resultado
```

### Jobs del Pipeline

#### 1. **build-and-push**
- Construye la imagen Docker
- La sube a Docker Hub con tag `latest`
- Usa caché para acelerar builds futuros

#### 2. **deploy-to-render**
- Solo se ejecuta después de `build-and-push` exitoso
- Solo se ejecuta en push a `main` (no en PRs)
- Llama al webhook de Render para iniciar el deploy

#### 3. **notify**
- Muestra un resumen del resultado del pipeline
- Se ejecuta siempre, incluso si hay fallos

## 👥 Trabajo en Equipo

### Para tus Compañeros

Ahora tus amigos pueden:

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/Andres09xZ/epagal-backend-latacunga-route-service.git
   ```

2. **Crear una rama para sus cambios**
   ```bash
   git checkout -b feature/nueva-funcionalidad
   ```

3. **Hacer sus cambios y commit**
   ```bash
   git add .
   git commit -m "feat: agregar nueva funcionalidad"
   git push origin feature/nueva-funcionalidad
   ```

4. **Crear un Pull Request en GitHub**
   - El pipeline se ejecutará automáticamente
   - Construirá la imagen para verificar que funciona
   - **NO** hará deploy a Render (solo builds de prueba)

5. **Cuando el PR sea aprobado y merged a `main`**
   - El pipeline se ejecutará nuevamente
   - Construirá la imagen
   - La subirá a Docker Hub
   - Actualizará Render automáticamente
   - ✨ **Sin necesidad de credenciales**

### Ventajas

✅ **Sin compartir credenciales** - Los secrets solo están en GitHub
✅ **Deploy automático** - Solo hacer push a main
✅ **Historial de deploys** - En la pestaña Actions de GitHub
✅ **Rollback fácil** - Puedes reejecutar un workflow anterior
✅ **Testing en PRs** - Verifica que la imagen se construya antes de mergear

## 📊 Ver el Estado del Pipeline

1. Ve a la pestaña **Actions** en GitHub
2. Verás todos los workflows ejecutados
3. Click en cualquiera para ver los detalles
4. Cada job muestra logs en tiempo real

## 🔧 Ejecutar Manualmente

Si necesitas hacer deploy sin hacer push:

1. Ve a **Actions** en GitHub
2. Selecciona **Build and Deploy to Render**
3. Click en **Run workflow**
4. Selecciona la rama `main`
5. Click en **Run workflow**

## 🐛 Troubleshooting

### ❌ "Error: Login to Docker Hub failed"
- Verifica que `DOCKER_USERNAME` y `DOCKER_PASSWORD` estén configurados correctamente
- Si usas contraseña, considera usar un Access Token

### ❌ "Error: Deploy to Render failed"
- Verifica que `RENDER_DEPLOY_HOOK_URL` esté configurado correctamente
- Asegúrate de que la URL sea la correcta desde Render Dashboard

### ❌ "Error: Docker build failed"
- Revisa los logs del job `build-and-push`
- Puede ser un error en el código o Dockerfile

## 📝 Notas Importantes

1. **Solo push a `main` hace deploy a Render**
2. Los PRs solo construyen la imagen (sin deploy)
3. El pipeline tarda ~3-5 minutos en completarse
4. Render puede tardar ~2-3 minutos adicionales en actualizar

## 🔐 Seguridad

- ✅ Los secrets nunca se exponen en los logs
- ✅ Solo los colaboradores del repo pueden ver los secrets
- ✅ Los secrets no se comparten entre forks
- ✅ Puedes rotar los secrets cuando quieras

---

**¿Preguntas?** Abre un issue en el repositorio o contacta al administrador.
