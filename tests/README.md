# Scripts de Prueba - EPAGAL Backend

Esta carpeta contiene todos los scripts de prueba para validar el funcionamiento del backend.

## 📋 Índice de Tests

### 🏥 Health Check
- **`test_health_check.py`** - Verifica el estado del servicio
  - Prueba local (localhost:9000) y producción (Render)
  - Valida conexiones a base de datos y OSRM
  - Muestra información del sistema y versión
  
  ```bash
  python tests/test_health_check.py
  ```

### 👷 Conductores
- **`test_conductores_bdd.py`** - Pruebas de base de datos de conductores
  - Verifica datos de conductores en PostgreSQL
  - Valida estructura de tablas
  
  ```bash
  python tests/test_conductores_bdd.py
  ```

- **`test_endpoints_josue.py`** - Pruebas con usuario conductor específico
  - Autenticación con conductor josue/josue123
  - Prueba endpoints de rutas activas
  - Valida operaciones de conductor
  
  ```bash
  python tests/test_endpoints_josue.py
  ```

### 🗺️ Rutas y OSRM
- **`test_osrm_connection.py`** - Verifica conexión con servicio OSRM
  - Prueba cálculo de rutas entre puntos
  - Valida tiempo y distancia estimados
  
  ```bash
  python tests/test_osrm_connection.py
  ```

- **`test_rutas_api.py`** - Pruebas de API de rutas
  - Generación de rutas optimizadas
  - Asignación de conductores
  - Estados de rutas
  
  ```bash
  python tests/test_rutas_api.py
  ```

### 🆕 Nuevos Endpoints
- **`test_nuevos_endpoints.py`** - Pruebas de endpoints recientes
  - GET /api/rutas/historial/estado
  - GET /api/rutas/calendario/activas
  - GET /api/rutas/{id}/navegacion
  - POST /api/conductores/iniciar-ruta
  - POST /api/conductores/finalizar-ruta
  
  ```bash
  python tests/test_nuevos_endpoints.py
  ```

### ✅ Validación de Flujo
- **`test_validacion_flujo.py`** - Pruebas de flujo completo del sistema
  - Flujo: Crear incidencia → Generar ruta → Asignar conductor → Completar
  - Validación de estados y transiciones
  - Prueba integración completa
  
  ```bash
  python tests/test_validacion_flujo.py
  ```

## 🚀 Ejecutar Todos los Tests

Para ejecutar todos los tests de una vez:

```bash
# PowerShell
Get-ChildItem tests\test_*.py | ForEach-Object { python $_.FullName }

# Bash/Linux
for test in tests/test_*.py; do python "$test"; done
```

## 📝 Requisitos

Todos los tests requieren:
- Python 3.11+
- Biblioteca `requests` instalada
- Variables de entorno configuradas (si es necesario)

```bash
pip install requests
```

## 🌐 URLs de Prueba

### Local
- Backend: http://localhost:9000
- Dashboard: http://localhost:8000
- OSRM: http://localhost:5000

### Producción
- Backend: https://epagal-backend-routing-latest.onrender.com
- Health Check: https://epagal-backend-routing-latest.onrender.com/health
- Documentación: https://epagal-backend-routing-latest.onrender.com/docs

## 🔐 Credenciales de Prueba

Conductores para testing:
- **Usuario**: josue | **Password**: josue123
- **Usuario**: pedro | **Password**: pedro123

## 📊 Interpretación de Resultados

- ✅ **Verde/Success** - Test pasó correctamente
- ❌ **Rojo/Error** - Test falló, revisar detalles
- ⚠️ **Amarillo/Warning** - Test parcialmente exitoso
- 🔌 **Error de conexión** - Servicio no disponible

## 🛠️ Troubleshooting

### Error: "No se puede establecer una conexión"
- Verifica que el backend esté corriendo
- Para local: ejecuta `docker-compose up`
- Para producción: verifica que Render esté activo

### Error: "401 Unauthorized"
- Las credenciales de conductor son incorrectas
- Verifica que el conductor exista en la base de datos
- Revisa el token JWT

### Error: "OSRM Service: error"
- Verifica que el contenedor OSRM esté corriendo
- Asegúrate de que los datos de Ecuador estén cargados
- Revisa la variable de entorno OSRM_URL

## 📚 Documentación Adicional

Para más información sobre los endpoints, consulta:
- [API_ENDPOINTS.md](../API_ENDPOINTS.md)
- [ENDPOINTS_RUTAS_MOVIL.md](../ENDPOINTS_RUTAS_MOVIL.md)
- [EJEMPLOS_API.md](../EJEMPLOS_API.md)
