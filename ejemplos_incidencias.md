# Ejemplos de Incidencias para Pruebas Manuales

## 📍 Información General

- **API Base URL**: `http://localhost:8000`
- **Endpoint Crear Incidencia**: `POST /api/incidencias/`
- **Endpoint Validar**: `POST /api/incidencias/{id}/validate`
- **Endpoint Ver Rutas**: `GET /api/rutas/zona/{zona}`

## 🎯 Sistema de Puntos

- **animal_muerto** = 5 puntos
- **zona_critica** = 3 puntos
- **acopio** = 1 punto

**Umbral**: 20 puntos (debe ser **> 20**, no ≥ 20)

---

## 🧪 CASO 1: Generar Primera Ruta (Norte Oriental)

**Objetivo**: Superar umbral de 20 puntos y generar primera ruta  
**Puntos totales**: 22 (5+3+3+5+3+3)  
**Zona**: Oriental (lon < -78.6191)

### Incidencia 1 - Animal Muerto Norte 1
```json
{
  "tipo": "animal_muerto",
  "descripcion": "Animal muerto en vía principal - Norte 1",
  "lat": -0.9200,
  "lon": -78.6100,
  "usuario_id": 1
}
```

### Incidencia 2 - Zona Crítica Norte 2
```json
{
  "tipo": "zona_critica",
  "descripcion": "Acumulación de residuos - Norte 2",
  "lat": -0.9250,
  "lon": -78.6120,
  "usuario_id": 1
}
```

### Incidencia 3 - Zona Crítica Norte 3
```json
{
  "tipo": "zona_critica",
  "descripcion": "Área con basura - Norte 3",
  "lat": -0.9280,
  "lon": -78.6150,
  "usuario_id": 1
}
```

### Incidencia 4 - Animal Muerto Norte 4
```json
{
  "tipo": "animal_muerto",
  "descripcion": "Perro atropellado - Norte 4",
  "lat": -0.9300,
  "lon": -78.6080,
  "usuario_id": 1
}
```

### Incidencia 5 - Zona Crítica Norte 5
```json
{
  "tipo": "zona_critica",
  "descripcion": "Basura en esquina - Norte 5",
  "lat": -0.9320,
  "lon": -78.6140,
  "usuario_id": 1
}
```

### Incidencia 6 - Zona Crítica Norte 6
```json
{
  "tipo": "zona_critica",
  "descripcion": "Residuos acumulados - Norte 6",
  "lat": -0.9330,
  "lon": -78.6160,
  "usuario_id": 1
}
```

**✅ Resultado esperado**: Al validar la 6ta incidencia, se debe generar automáticamente la **Ruta 1**

---

## 🧪 CASO 2: Anti-Solapamiento (Cerca de Ruta 1)

**Objetivo**: Verificar que incidencias cercanas (<500m) NO generan nueva ruta  
**Puntos totales**: 7 (1+3+1)  
**Zona**: Oriental (cerca de las incidencias del Caso 1)

### Incidencia 7 - Acopio Cerca Norte 1
```json
{
  "tipo": "acopio",
  "descripcion": "Recolección puntual cerca Norte 1",
  "lat": -0.9210,
  "lon": -78.6110,
  "usuario_id": 1
}
```

### Incidencia 8 - Zona Crítica Cerca Norte 2
```json
{
  "tipo": "zona_critica",
  "descripcion": "Basura adicional cerca Norte 2",
  "lat": -0.9260,
  "lon": -78.6130,
  "usuario_id": 1
}
```

### Incidencia 9 - Acopio Cerca Norte 4
```json
{
  "tipo": "acopio",
  "descripcion": "Punto de recolección cerca Norte 4",
  "lat": -0.9290,
  "lon": -78.6090,
  "usuario_id": 1
}
```

**✅ Resultado esperado**: Se validan las 3 incidencias pero **NO se genera nueva ruta** (están a menos de 500m de la Ruta 1)

---

## 🧪 CASO 3: Nueva Ruta Independiente (Sur Oriental)

**Objetivo**: Incidencias LEJOS (>500m) de Ruta 1 generan nueva ruta independiente  
**Puntos totales**: 22 (5+3+3+5+3+3)  
**Zona**: Oriental (sur de la ciudad, lejos del Caso 1)

### Incidencia 10 - Animal Muerto Sur 1
```json
{
  "tipo": "animal_muerto",
  "descripcion": "Animal muerto - Sur 1",
  "lat": -0.9800,
  "lon": -78.6100,
  "usuario_id": 1
}
```

### Incidencia 11 - Zona Crítica Sur 2
```json
{
  "tipo": "zona_critica",
  "descripcion": "Basura acumulada - Sur 2",
  "lat": -0.9850,
  "lon": -78.6120,
  "usuario_id": 1
}
```

### Incidencia 12 - Zona Crítica Sur 3
```json
{
  "tipo": "zona_critica",
  "descripcion": "Residuos en vía - Sur 3",
  "lat": -0.9880,
  "lon": -78.6150,
  "usuario_id": 1
}
```

### Incidencia 13 - Animal Muerto Sur 4
```json
{
  "tipo": "animal_muerto",
  "descripcion": "Gato atropellado - Sur 4",
  "lat": -0.9900,
  "lon": -78.6080,
  "usuario_id": 1
}
```

### Incidencia 14 - Zona Crítica Sur 5
```json
{
  "tipo": "zona_critica",
  "descripcion": "Basura en esquina - Sur 5",
  "lat": -0.9920,
  "lon": -78.6140,
  "usuario_id": 1
}
```

### Incidencia 15 - Zona Crítica Sur 6
```json
{
  "tipo": "zona_critica",
  "descripcion": "Área con residuos - Sur 6",
  "lat": -0.9930,
  "lon": -78.6160,
  "usuario_id": 1
}
```

**✅ Resultado esperado**: Al validar la incidencia 15, se genera **Ruta 2** (independiente de Ruta 1)

---

## 🧪 CASO 4: Zona Occidental Independiente

**Objetivo**: Cada zona maneja su propio umbral de forma independiente  
**Puntos totales**: 22 (5+3+3+5+3+3)  
**Zona**: Occidental (lon ≥ -78.6191)

### Incidencia 16 - Animal Muerto Occidental 1
```json
{
  "tipo": "animal_muerto",
  "descripcion": "Animal muerto - Occidental 1",
  "lat": -0.9200,
  "lon": -78.6300,
  "usuario_id": 1
}
```

### Incidencia 17 - Zona Crítica Occidental 2
```json
{
  "tipo": "zona_critica",
  "descripcion": "Basura acumulada - Occidental 2",
  "lat": -0.9250,
  "lon": -78.6320,
  "usuario_id": 1
}
```

### Incidencia 18 - Zona Crítica Occidental 3
```json
{
  "tipo": "zona_critica",
  "descripcion": "Residuos en calle - Occidental 3",
  "lat": -0.9280,
  "lon": -78.6350,
  "usuario_id": 1
}
```

### Incidencia 19 - Animal Muerto Occidental 4
```json
{
  "tipo": "animal_muerto",
  "descripcion": "Perro atropellado - Occidental 4",
  "lat": -0.9300,
  "lon": -78.6280,
  "usuario_id": 1
}
```

### Incidencia 20 - Zona Crítica Occidental 5
```json
{
  "tipo": "zona_critica",
  "descripcion": "Basura en esquina - Occidental 5",
  "lat": -0.9320,
  "lon": -78.6340,
  "usuario_id": 1
}
```

### Incidencia 21 - Zona Crítica Occidental 6
```json
{
  "tipo": "zona_critica",
  "descripcion": "Área con basura - Occidental 6",
  "lat": -0.9330,
  "lon": -78.6360,
  "usuario_id": 1
}
```

**✅ Resultado esperado**: Al validar la incidencia 21, se genera **Ruta 3** (primera de zona occidental)

---

## 🔧 Comandos cURL para Pruebas

### Crear Incidencia
```bash
curl -X POST "http://localhost:8000/api/incidencias/" \
  -H "Content-Type: application/json" \
  -d '{
    "tipo": "animal_muerto",
    "descripcion": "Animal muerto en vía principal",
    "lat": -0.9200,
    "lon": -78.6100,
    "usuario_id": 1
  }'
```

### Validar Incidencia
```bash
curl -X POST "http://localhost:8000/api/incidencias/1/validate"
```

### Ver Rutas de una Zona
```bash
# Zona Oriental
curl "http://localhost:8000/api/rutas/zona/oriental"

# Zona Occidental
curl "http://localhost:8000/api/rutas/zona/occidental"
```

### Ver Detalles de una Ruta
```bash
curl "http://localhost:8000/api/rutas/1/detalles"
```

---

## 📊 Verificación de Resultados

Después de ejecutar todas las pruebas, deberías tener:

- **Zona Oriental**: 2 rutas generadas
  - Ruta 1: Norte (6 incidencias, 22 puntos)
  - Ruta 2: Sur (6 incidencias, 22 puntos)
  - 3 incidencias adicionales cercanas a Ruta 1 (NO generan nueva ruta)

- **Zona Occidental**: 1 ruta generada
  - Ruta 3: (6 incidencias, 22 puntos)

- **Total**: 3 rutas generadas automáticamente

---

## 🐛 Debugging

Si algo no funciona, revisa los logs en el terminal de uvicorn buscando:

```
🚨 ¡UMBRAL SUPERADO! Generando primera ruta en zona oriental...
✅ Ruta #X generada con Y camión(es)
Ruta generada exitosamente: ID=X, zona=..., camiones=..., distancia=..., duración=...
```

O mensajes de error:
```
❌ Error al generar nueva ruta
No se encontraron depósito o botadero activos
Error al calcular ruta con OSRM
```

---

## 📱 Usando Postman o Swagger

### Swagger UI
Abre: `http://localhost:8000/docs`

1. Ve a `POST /api/incidencias/`
2. Click en "Try it out"
3. Copia uno de los JSON de arriba
4. Click en "Execute"
5. Guarda el `id` que te devuelve
6. Ve a `POST /api/incidencias/{id}/validate`
7. Ingresa el `id` y ejecuta
8. Repite para cada incidencia

### Postman
1. Importa esta colección o crea requests manualmente
2. Usa el método POST para crear incidencias
3. Usa POST para validar
4. Usa GET para ver rutas generadas
