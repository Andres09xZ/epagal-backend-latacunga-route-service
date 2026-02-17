# Historia de Usuario - Generación Automática de Rutas

## 📋 Historia de Usuario

**Como** administrador del sistema EPAGAL  
**Quiero** que el sistema genere automáticamente rutas optimizadas cuando se supere el umbral de gravedad, evitando solapamiento de rutas en la misma zona  
**Para** optimizar la recolección de residuos, maximizar la eficiencia de los camiones y evitar que múltiples rutas atiendan la misma área geográfica simultáneamente

---

## 🎯 Criterios de Aceptación (BDD - Gherkin)

### Feature: Generación Automática de Rutas por Umbral

```gherkin
Feature: Generación Automática de Rutas por Umbral de Gravedad
  Como administrador del sistema EPAGAL
  Quiero que el sistema genere rutas automáticamente cuando se supere el umbral
  Para optimizar la recolección y atención de incidencias

  Background:
    Given el umbral de gravedad está configurado en 20 puntos
    And la zona se divide en "oriental" y "occidental" según la longitud -78.6191
    And los tipos de incidencia tienen las siguientes gravedades:
      | Tipo           | Gravedad |
      | acopio         | 1        |
      | zona_critica   | 3        |
      | animal_muerto  | 5        |

  Scenario: Generar primera ruta cuando se supera el umbral
    Given no existen rutas planeadas en la zona "oriental"
    And existen las siguientes incidencias en estado "pendiente" en zona "oriental":
      | ID | Tipo           | Latitud  | Longitud  | Gravedad |
      | 1  | animal_muerto  | -0.9344  | -78.6000  | 5        |
      | 2  | animal_muerto  | -0.9350  | -78.6010  | 5        |
      | 3  | animal_muerto  | -0.9360  | -78.6020  | 5        |
      | 4  | animal_muerto  | -0.9370  | -78.6030  | 5        |
      | 5  | zona_critica   | -0.9380  | -78.6040  | 3        |
    When el administrador valida las incidencias 1, 2, 3, 4, 5
    Then la suma de gravedad en zona "oriental" debe ser 23 puntos
    And el umbral de 20 puntos debe ser superado
    And se debe generar automáticamente la ruta #1
    And la ruta #1 debe incluir las 5 incidencias
    And las incidencias deben cambiar a estado "asignada"
    And el sistema debe mostrar el mensaje "✅ Ruta #1 generada automáticamente"

  Scenario: No generar ruta cuando no se supera el umbral
    Given no existen rutas planeadas en la zona "occidental"
    And existen 3 incidencias tipo "acopio" validadas en zona "occidental"
    When el administrador valida una nueva incidencia tipo "acopio"
    Then la suma de gravedad en zona "occidental" debe ser 4 puntos
    And el umbral de 20 puntos NO debe ser superado
    And NO se debe generar ninguna ruta
    And el sistema debe mostrar "Faltan 16 puntos para generar ruta"
    And las incidencias deben permanecer en estado "validada"

  Scenario: Resetear umbral después de generar ruta
    Given existe la ruta #1 planeada en zona "oriental" con 5 incidencias asignadas
    And la suma de gravedad de incidencias "asignadas" es 25 puntos
    When ingresan 5 nuevas incidencias tipo "animal_muerto" en zona "oriental"
    And el administrador valida las 5 nuevas incidencias
    Then la suma de gravedad debe calcularse solo con incidencias "validadas" (25 puntos)
    And las incidencias "asignadas" NO deben contar para el umbral
    And el umbral debe superarse nuevamente
    And se debe generar la ruta #2
    And las nuevas incidencias deben asignarse a la ruta #2

  Scenario: Agregar incidencia cercana a ruta existente
    Given existe la ruta #1 planeada en zona "oriental" 
    And la ruta #1 incluye una incidencia en coordenadas (-0.9344, -78.6000)
    When ingresa una nueva incidencia en coordenadas (-0.9346, -78.6002)
    And el administrador valida la nueva incidencia
    Then el sistema debe calcular que la distancia es menor a 500 metros
    And la incidencia debe quedar en estado "validada"
    And NO se debe crear una nueva ruta
    And NO se debe recalcular la ruta existente
    And el sistema debe mostrar "📍 Incidencia cercana a Ruta #1. NO se genera nueva ruta para evitar solapamiento"
    And la incidencia queda disponible para futuras rutas cuando la Ruta #1 sea completada

  Scenario: Generar nueva ruta cuando incidencia está lejos de rutas existentes
    Given existe la ruta #1 planeada en zona "oriental" en el sector Norte
    And la ruta #1 tiene incidencias en coordenadas (-0.9344, -78.6000)
    When ingresan 5 nuevas incidencias en el sector Sur en coordenadas (-0.9500, -78.6000)
    And el administrador valida las 5 nuevas incidencias
    Then el sistema debe calcular que la distancia es mayor a 500 metros
    And la suma de gravedad de las nuevas incidencias debe ser 25 puntos
    And el umbral debe superarse
    And se debe generar la ruta #2 independiente
    And deben existir 2 rutas planeadas simultáneamente
    And el sistema debe mostrar "✅ Nueva Ruta #2 generada"

  Scenario: Evitar solapamiento de rutas en la misma zona
    Given existe la ruta #1 planeada en zona "oriental" con 5 incidencias (sector Norte)
    And las incidencias de la ruta #1 están en un radio de 1km
    When ingresan 3 nuevas incidencias dentro del radio de 500m de la ruta #1
    And el administrador valida las 3 nuevas incidencias
    Then cada incidencia debe verificarse contra los puntos de la ruta #1
    And las 3 incidencias deben detectarse como "cercanas" (< 500m)
    And las incidencias deben quedar en estado "validada" sin asignarse
    And NO se debe generar ninguna ruta nueva
    And el sistema debe mostrar "📍 Incidencia cercana. NO se genera nueva ruta para evitar solapamiento"
    And cuando la ruta #1 cambie a estado "en_ejecucion" o "completada"
    Then las incidencias validadas podrán ser incluidas en una nueva ruta si superan el umbral

  Scenario: Generar ruta con múltiples camiones según capacidad
    Given no existen rutas planeadas en zona "oriental"
    And existen 8 incidencias tipo "animal_muerto" validadas (40 puntos total)
    When el administrador valida la última incidencia
    Then el umbral de 20 puntos debe superarse ampliamente
    And se debe generar la ruta #1
    And la ruta debe asignar 2 camiones (capacidad: posterior=25, lateral=15)
    And el primer camión (posterior) debe tener carga de 25 puntos
    And el segundo camión (lateral) debe tener carga de 15 puntos
    And la ruta debe mostrar "Camiones Usados: 2"

  Scenario: Visualizar polilínea de ruta generada en dashboard
    Given existe la ruta #1 generada con 5 incidencias
    When el administrador accede al dashboard
    And hace clic en "Ver Detalles" de la ruta #1
    Then debe mostrarse un mapa interactivo con Leaflet
    And debe visualizarse la polilínea azul de la ruta optimizada
    And debe mostrarse el marcador verde 🏢 para el depósito (inicio)
    And deben mostrarse marcadores azules 📍 para cada incidencia
    And debe mostrarse el marcador rojo 🗑️ para el botadero (fin)
    And al hacer clic en un marcador debe mostrarse un popup con información

  Scenario: Mostrar umbrales en tiempo real en dashboard
    Given existen incidencias validadas en ambas zonas
    When el administrador accede al dashboard
    Then debe mostrarse la tarjeta de "Zona Oriental" con:
      | Campo                  | Valor Esperado |
      | Gravedad Acumulada     | 25             |
      | Umbral                 | 20             |
      | Porcentaje             | 125%           |
      | Estado                 | 🚨 UMBRAL SUPERADO |
      | Color de barra         | Rojo           |
    And debe mostrarse la tarjeta de "Zona Occidental" con:
      | Campo                  | Valor Esperado |
      | Gravedad Acumulada     | 10             |
      | Umbral                 | 20             |
      | Porcentaje             | 50%            |
      | Estado                 | ✅ NORMAL      |
      | Color de barra         | Verde          |

  Scenario: Auto-detección de zona por coordenadas
    Given el administrador crea una incidencia
    And proporciona las coordenadas (-0.9344, -78.6000)
    When el sistema procesa la incidencia
    Then debe detectar automáticamente zona "oriental" (longitud > -78.6191)
    And debe asignar gravedad automáticamente según el tipo
    And NO debe requerir que el administrador especifique la zona manualmente

  Scenario: Validación de límites geográficos de Latacunga
    Given el administrador intenta crear una incidencia
    When proporciona coordenadas fuera de los límites de Latacunga:
      | Latitud | Longitud |
      | -1.0000 | -78.6000 |
    Then el sistema debe rechazar la incidencia
    And debe mostrar el mensaje de error:
      """
      Latitud -1.0000 fuera del rango de Latacunga (-0.97 a -0.90)
      """
```

---

## 🔄 Flujo de Estados de Incidencia

```gherkin
Feature: Ciclo de Vida de Estados de Incidencia

  Scenario: Transición de estados durante el proceso de ruta
    Given una incidencia recién creada
    Then su estado inicial debe ser "pendiente"
    
    When el administrador valida la incidencia
    Then su estado debe cambiar a "validada"
    And debe comenzar a contar para el umbral
    
    When se genera una ruta que incluye la incidencia
    Then su estado debe cambiar a "asignada"
    And NO debe contar más para el umbral
    And debe quedar vinculada a la ruta generada
    
    When el conductor completa la recolección
    Then su estado debe cambiar a "completada"
    And debe registrarse la fecha de completación

  Scenario: Estados que cuentan para el umbral
    Given las siguientes incidencias con diferentes estados:
      | Estado      | Cuenta para Umbral |
      | pendiente   | NO                 |
      | validada    | SÍ                 |
      | asignada    | NO                 |
      | completada  | NO                 |
      | cancelada   | NO                 |
    Then solo las incidencias en estado "validada" deben sumar para el umbral
```

---

## 📊 Reglas de Negocio

### RN-001: Cálculo de Gravedad
```gherkin
Rule: La gravedad se asigna automáticamente según el tipo de incidencia
  Example: Incidencia tipo "acopio" → gravedad = 1
  Example: Incidencia tipo "zona_critica" → gravedad = 3
  Example: Incidencia tipo "animal_muerto" → gravedad = 5
```

### RN-002: División de Zonas
```gherkin
Rule: La zona se determina por la longitud de la coordenada
  Example: Longitud > -78.6191 → zona "oriental"
  Example: Longitud ≤ -78.6191 → zona "occidental"
```

### RN-003: Umbral de Generación
```gherkin
Rule: La ruta se genera cuando la suma de gravedad SUPERA el umbral
  Example: Umbral = 20, Suma = 21 → SE GENERA RUTA
  Example: Umbral = 20, Suma = 20 → NO SE GENERA RUTA
  Example: Umbral = 20, Suma = 19 → NO SE GENERA RUTA
```

### RN-004: Radio de Cercanía para Evitar Solapamiento
```gherkin
Rule: Una incidencia se considera cercana si está a menos de 500m de una ruta planeada
  Example: Distancia = 300m → NO SE GENERA NUEVA RUTA (evita solapamiento)
  Example: Distancia = 600m → SE CREA NUEVA RUTA (si supera umbral)
  
  Comportamiento cuando incidencia está cerca:
    - La incidencia queda en estado "validada"
    - NO se genera nueva ruta
    - NO se recalcula la ruta existente
    - La incidencia se acumula para futuras rutas
```

### RN-005: Capacidad de Camiones
```gherkin
Rule: Los camiones tienen capacidad limitada de puntos de gravedad
  Example: Camión posterior → capacidad = 25 puntos
  Example: Camión lateral → capacidad = 15 puntos
  Example: Gravedad total = 40 → Requiere 2 camiones (posterior + lateral)
```

---

## ✅ Casos de Prueba Técnicos

### Test Case 1: API - Validar Incidencia
```http
POST /api/incidencias/1/validate
Content-Type: application/json
Authorization: Bearer {token}

Expected Response (200 OK):
{
  "id": 1,
  "estado": "validada",
  "gravedad": 5,
  "zona": "oriental",
  "ruta_generada_id": 1  // Solo si se superó umbral
}
```

### Test Case 2: API - Obtener Umbrales
```http
GET /api/incidencias/umbrales

Expected Response (200 OK):
{
  "umbral": 20,
  "oriental": {
    "gravedad_acumulada": 25,
    "incidencias_validadas": 5,
    "porcentaje": 125.0,
    "supera_umbral": true
  },
  "occidental": {
    "gravedad_acumulada": 10,
    "incidencias_validadas": 2,
    "porcentaje": 50.0,
    "supera_umbral": false
  }
}
```

### Test Case 3: API - Obtener Ruta con Polilínea
```http
GET /api/rutas/1

Expected Response (200 OK):
{
  "id": 1,
  "zona": "oriental",
  "estado": "planeada",
  "suma_gravedad": 25,
  "camiones_usados": 1,
  "polyline": "abcxyzEncodedPolylineString...",
  "puntos": [
    {
      "secuencia": 1,
      "tipo_punto": "deposito",
      "lat": -0.9340,
      "lon": -78.6180
    },
    {
      "secuencia": 2,
      "tipo_punto": "incidencia",
      "incidencia_id": 1,
      "gravedad": 5
    }
  ]
}
```

---

## 🎨 Mockups / Wireframes

### Dashboard - Vista de Umbrales
```
┌─────────────────────────────────────────────────────────────┐
│ 🌅 Zona Oriental            🚨 UMBRAL SUPERADO              │
│                                                             │
│ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░  25 / 20 (125%)                      │
│                                                             │
│ Gravedad Acumulada: 25                                      │
│ Incidencias Validadas: 5                                    │
│ Exceso: 5 puntos                                            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 🌄 Zona Occidental          ✅ NORMAL                        │
│                                                             │
│ ▓▓▓▓▓░░░░░░░░░░░░░░░  10 / 20 (50%)                        │
│                                                             │
│ Gravedad Acumulada: 10                                      │
│ Incidencias Validadas: 2                                    │
│ Falta: 10 puntos                                            │
└─────────────────────────────────────────────────────────────┘
```

### Dashboard - Mapa de Ruta
```
┌─────────────────────────────────────────────────────────────┐
│ 🗺️ Visualización de Ruta #1                                │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                     │   │
│  │  🏢 ────📍────📍────📍────📍────📍──── 🗑️          │   │
│  │    Depósito  Incidencias (5)    Botadero           │   │
│  │                                                     │   │
│  │  [Mapa Interactivo OpenStreetMap con polilínea]    │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  📊 Distancia: 9.53 km                                      │
│  ⏱️ Duración: 0:13:48                                       │
│  🚛 Camiones: 1 (Posterior)                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 Notas Técnicas

### Tecnologías Utilizadas:
- **Backend**: FastAPI 0.115 (Python 3.13)
- **Base de Datos**: PostgreSQL con PostGIS 3.5
- **Motor de Rutas**: OSRM (Open Source Routing Machine)
- **Frontend**: Vanilla JavaScript con Leaflet.js
- **Formato de Polilínea**: Google Polyline Algorithm

### Fórmulas de Cálculo:
- **Distancia Haversine**: R * 2 * atan2(√a, √(1-a))
- **Umbral Superado**: suma_gravedad > umbral (estrictamente mayor)
- **Porcentaje**: (gravedad_acumulada / umbral) * 100

### Configuración:
- **Umbral por defecto**: 20 puntos
- **Radio de cercanía**: 500 metros
- **Capacidad camión posterior**: 25 puntos
- **Capacidad camión lateral**: 15 puntos
- **Longitud divisoria**: -78.6191

---

## 🚫 **Lógica Anti-Solapamiento de Rutas**

### **Problema que Resuelve:**
Evitar que múltiples rutas planeadas atiendan la misma área geográfica, lo cual causaría:
- ❌ Desperdicio de recursos (2 camiones para la misma zona)
- ❌ Confusión operativa (¿cuál camión atiende qué?)
- ❌ Ineficiencia en rutas (rutas que se cruzan)

### **Solución Implementada:**

#### **Paso 1: Detección de Proximidad**
```javascript
Cuando se valida una nueva incidencia:
  ↓
¿Hay rutas PLANEADAS en la zona?
  ↓
SÍ → Calcular distancia a TODOS los puntos de TODAS las rutas
  ↓
¿Distancia < 500m a algún punto?
  ↓
SÍ → Incidencia está CERCA → NO generar nueva ruta
NO → Incidencia está LEJOS → Acumular y verificar umbral
```

#### **Paso 2: Manejo de Incidencias Cercanas**
```javascript
Incidencia cercana detectada:
  ↓
Estado: "validada" (NO "asignada")
  ↓
La incidencia queda "en espera"
  ↓
Cuando la ruta planeada cambie de estado:
  - "en_ejecucion" → Incidencia sigue en espera
  - "completada" → Incidencia disponible para nuevas rutas
  ↓
Si nuevas incidencias lejanas superan umbral:
  → Se genera ruta independiente sin incluir las cercanas
```

#### **Paso 3: Generación de Rutas Múltiples**
```javascript
Ejemplo Práctico:

Zona Oriental inicial: Sin rutas
  ↓
Validar 5 incidencias en Sector Norte (25 pts)
  → Supera umbral (20)
  → Genera Ruta #1 (Sector Norte)
  → 5 incidencias pasan a "asignada"
  
Nueva incidencia en Sector Norte (a 300m de Ruta #1)
  → Detecta cercanía
  → NO genera ruta
  → Incidencia queda "validada"
  
5 incidencias en Sector Sur (a 2km de Ruta #1, 25 pts)
  → Detecta lejanía (> 500m)
  → Supera umbral
  → Genera Ruta #2 (Sector Sur) ✅
  
RESULTADO:
  - Ruta #1: Sector Norte (5 incidencias)
  - Ruta #2: Sector Sur (5 incidencias)
  - Incidencias cercanas no asignadas: 1 (en espera)
```

### **Ventajas del Sistema:**

✅ **Optimización de Recursos**
- Cada camión tiene su zona definida
- No hay duplicación de esfuerzos

✅ **Flexibilidad**
- Permite múltiples rutas en la misma zona geográfica
- Solo si están a > 500m de distancia

✅ **Gestión Inteligente**
- Incidencias cercanas no se desperdician
- Quedan disponibles para futuras rutas

✅ **Escalabilidad**
- Puede generar N rutas simultáneas
- Cada ruta independiente y optimizada

### **Casos de Uso:**

**Caso 1: Área Densa (Centro de la Ciudad)**
```
Incidencias concentradas en radio de 1km
  → Se genera 1 sola ruta
  → Todas las incidencias cercanas esperan
  → Eficiencia máxima
```

**Caso 2: Múltiples Sectores**
```
Sector Norte: 5 incidencias (25 pts)
Sector Sur: 5 incidencias (25 pts)
Distancia entre sectores: 3km
  → Se generan 2 rutas independientes
  → Cada camión optimiza su sector
```

**Caso 3: Crecimiento Gradual**
```
Día 1: Ruta #1 planeada (Sector A)
Día 2: 2 incidencias cercanas (< 500m)
  → Quedan en espera
Día 3: Ruta #1 ejecutada y completada
Día 4: Llegan más incidencias en Sector A
  → Se incluyen las 2 en espera + nuevas
  → Nueva ruta cuando supere umbral
```

---

## 🔗 Referencias

- **Repositorio**: `epagal-backend-latacunga-route-service`
- **Documentación**: `SOLUCION_RUTAS.md`
- **API Endpoints**: `API_ENDPOINTS.md`

---

**Autor**: Sistema EPAGAL - Gestión de Incidencias  
**Fecha**: 12 de enero de 2026  
**Versión**: 2.0.1
