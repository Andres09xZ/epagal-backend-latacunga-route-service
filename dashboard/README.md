# 🎯 Dashboard Administrativo EPAGAL

Dashboard web para la gestión de incidencias, rutas y conductores del sistema EPAGAL Latacunga.

## 📋 Características

### ✅ Gestión de Incidencias
- Ver todas las incidencias reportadas
- Filtrar por estado (pendiente, validada, asignada, completada, cancelada)
- Filtrar por zona (oriental, occidental)
- **Validar incidencias pendientes** (genera ruta automáticamente si se supera el umbral)
- Rechazar incidencias (cambiar a estado cancelada)
- Ver detalles completos de cada incidencia
- Ver fotos adjuntas

### 🗺️ Gestión de Rutas
- Ver todas las rutas generadas
- Filtrar por zona y estado
- **Asignar conductores a rutas con horario programado**
- Ver detalles completos de cada ruta
- Ver puntos de recorrido
- Ver asignaciones actuales

### 👷 Gestión de Conductores
- Ver lista completa de conductores
- **Crear nuevos conductores**
- Ver información de cada conductor (cédula, teléfono, licencia, zona)
- Ver estado de conductores (activo/inactivo)

### 📊 Estadísticas
- Total de incidencias por estado
- Total de rutas por estado
- Métricas en tiempo real

## 🚀 Cómo Usar

### 1. Abrir el Dashboard

Simplemente abre el archivo `index.html` en tu navegador:

```powershell
# Opción 1: Desde VS Code
# Click derecho en index.html → Open with Live Server

# Opción 2: Abrir directamente
start dashboard/index.html
```

### 2. Iniciar Sesión

**Credenciales por defecto:**
- **Usuario:** `admin`
- **Contraseña:** `admin123`

> ⚠️ Las credenciales se guardan en localStorage para no tener que iniciar sesión cada vez.

### 3. Navegar por las Secciones

Usa las pestañas superiores para cambiar entre:
- 📋 **Incidencias**: Gestionar reportes ciudadanos
- 🗺️ **Rutas**: Ver y asignar rutas
- 👷 **Conductores**: Gestionar personal
- 📊 **Estadísticas**: Ver métricas del sistema

## 📖 Flujo de Trabajo Típico

### Flujo 1: Validar una Incidencia

1. Ir a la pestaña **Incidencias**
2. Filtrar por `estado = pendiente`
3. Revisar cada incidencia
4. Click en **✅ Validar** para aprobar
5. Si se supera el umbral, se generará automáticamente una ruta
6. O click en **❌ Rechazar** para cancelar

### Flujo 2: Asignar Conductor a Ruta

1. Ir a la pestaña **Rutas**
2. Filtrar por `estado = planeada`
3. Click en **👷 Asignar Conductor** en la ruta deseada
4. Seleccionar:
   - Conductor disponible
   - Tipo de camión (posterior/lateral)
   - ID del camión
   - **Fecha y hora de inicio** (opcional, para programar)
5. Click en **Asignar**

### Flujo 3: Crear un Nuevo Conductor

1. Ir a la pestaña **Conductores**
2. Click en **➕ Crear Conductor**
3. Llenar el formulario:
   - Nombre completo
   - Cédula (10 dígitos)
   - Teléfono (10 dígitos)
   - Email
   - Tipo de licencia (C, D, E)
   - Zona preferida
   - Usuario y contraseña para login
4. Click en **Crear Conductor**

## 🔧 Configuración

### Cambiar URL del Backend

Edita el archivo `app.js` línea 2:

```javascript
const API_URL = 'http://localhost:9000';  // Cambiar aquí si es necesario
```

### Personalizar Estilos

Edita el archivo `styles.css` para cambiar colores, fuentes, etc.

Las variables CSS están en la raíz:

```css
:root {
    --primary: #2563eb;
    --success: #10b981;
    --danger: #ef4444;
    /* ... */
}
```

## 📱 Responsive

El dashboard es completamente responsive y funciona en:
- 💻 Desktop (1400px+)
- 📱 Tablet (768px - 1400px)
- 📱 Mobile (< 768px)

## 🔒 Seguridad

- El token de autenticación se guarda en `localStorage`
- Se envía en cada petición mediante header `Authorization: Bearer {token}`
- El token expira según la configuración del backend
- Click en **Cerrar Sesión** para limpiar el token

## 🎨 Tecnologías Usadas

- **HTML5**: Estructura semántica
- **CSS3**: Estilos modernos con Grid y Flexbox
- **JavaScript ES6+**: Lógica del dashboard
- **Fetch API**: Comunicación con el backend
- **localStorage**: Persistencia de sesión

## 📝 Notas Importantes

1. **CORS**: El backend debe tener CORS habilitado para `*` o el origen del dashboard
2. **Backend**: Debe estar corriendo en `http://localhost:9000`
3. **Navegadores**: Funciona en Chrome, Firefox, Edge, Safari modernos

## 🐛 Solución de Problemas

### Error: "Failed to fetch"

- Verifica que el backend esté corriendo: `docker ps`
- Verifica la URL en `app.js`
- Verifica que el backend tenga CORS habilitado

### Error: "Credenciales inválidas"

- Usa las credenciales por defecto: `admin / admin123`
- Verifica que el usuario exista en la base de datos

### No se ven las incidencias/rutas

- Verifica que haya datos en la base de datos
- Revisa la consola del navegador (F12) para ver errores
- Verifica que el token sea válido

## 🚀 Mejoras Futuras

- [ ] Integración con Google Maps para visualizar rutas
- [ ] Notificaciones en tiempo real (WebSockets)
- [ ] Exportar reportes a PDF/Excel
- [ ] Modo oscuro
- [ ] Gráficos interactivos con Chart.js

## 📄 Licencia

Este dashboard es parte del sistema EPAGAL Latacunga - Gestión de Incidencias y Rutas.

---

Última actualización: 2025-12-18
