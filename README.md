# 🗺️ EPAGAL Smart Routing Engine

> *"El camino más corto entre dos puntos es... nuestra API calculándolo por ti"* 🚛💨

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker)](https://docker.com)
[![OSRM](https://img.shields.io/badge/OSRM-Powered-00897B?style=for-the-badge)](http://project-osrm.org/)
[![Deploy](https://github.com/Andres09xZ/epagal-backend-latacunga-route-service/actions/workflows/deploy.yml/badge.svg)](https://github.com/Andres09xZ/epagal-backend-latacunga-route-service/actions/workflows/deploy.yml)

---

## 🎯 ¿Qué es esto?

Imagina que tienes **decenas de camiones recolectores**, **cientos de puntos de basura** y **miles de calles** en Latacunga, Ecuador. ¿Cómo decides qué camión va a dónde? ¿Cómo optimizas el combustible? ¿Cómo evitas que un camión dé 3 vueltas innecesarias?

**¡BOOM!** 💥 Ahí entramos nosotros.

Este servicio es el **cerebro detrás de las rutas** de recolección de EPAGAL. Usando algoritmos de optimización y el poder de OSRM (Open Source Routing Machine), transformamos el caos urbano en **rutas eficientes, rápidas y ecológicas**.

### 🌟 Lo que hacemos (en modo épico):

```
🗑️ Incidencia reportada
    ↓
📍 Geolocalización automática
    ↓
🧮 Cálculo de gravedad (1, 3 o 5 puntos)
    ↓
⚡ Acumulación hasta umbral (>20 pts)
    ↓
🚀 ¡RUTA GENERADA AUTOMÁTICAMENTE!
    ↓
🗺️ Polyline codificado para navegación
    ↓
👨‍✈️ Asignación a conductores disponibles
    ↓
📱 Envío a app móvil del operador
    ↓
✅ Ejecución en campo
```

---

## 🚀 Quick Start (Speedrun Mode)

### Opción 1: Docker (Recomendado para humanos ocupados)

```bash
# Un solo comando para gobernarlos a todos
docker-compose up -d

# ¿Funcionó? Visita http://localhost:8081/docs
# Spoiler: Sí funcionó 😎
```

### Opción 2: Local (Para los valientes)

```bash
# Clona el repo
git clone <tu-repo-url>
cd Backend-latacunga-clean

# Crea tu ambiente virtual (como un adulto responsable)
python -m venv venv
venv\Scripts\activate  # Windows gang
# source venv/bin/activate  # Linux/Mac gang

# Instala las dependencias
pip install -r requirements.txt

# Configura tu .env (copia .env.example y edítalo)
cp .env.example .env

# ¡Despegue!
uvicorn app.main:app --reload --port 8081
```

---

## 🎮 Probando el Sistema (Modo Playground)

### 1️⃣ Prepara datos de prueba

```bash
python preparar_datos_app.py
```

Esto creará:
- ✅ 3 operadores listos para trabajar
- ✅ ~12 incidencias realistas en Latacunga
- ✅ 2 rutas optimizadas (oriental + occidental)
- ✅ Asignaciones de conductores
- ✅ Todo conectado y funcionando

### 2️⃣ Login como operador

```bash
curl -X POST http://localhost:8081/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"operador1","password":"operador123"}'

# 💡 Copia el access_token que te devuelve
```

### 3️⃣ Ver tus rutas asignadas

```bash
curl http://localhost:8081/api/conductores/mis-rutas/todas \
  -H "Authorization: Bearer TU_TOKEN_AQUI"

# Verás tus rutas con toda la info: zona, gravedad, duración, etc.
```

### 4️⃣ Obtener detalles de navegación

```bash
curl http://localhost:8081/api/rutas/18 \
  -H "Authorization: Bearer TU_TOKEN_AQUI"

# Boom! 💥 Polyline codificado listo para tu mapa
```

---

## 🗺️ El Corazón del Sistema: Rutas Inteligentes

### ¿Cómo calculamos las rutas?

1. **Clustering Inteligente** 🧠
   - Agrupamos incidencias por zona (oriental/occidental)
   - Dividimos por el meridiano -78.615°

2. **Optimización Multi-Vehículo** 🚛🚛
   - Algoritmo greedy + OSRM routing
   - Capacidad por gravedad: Lateral=15pts, Posterior=25pts

3. **Ruta Completa** 📍
   ```
   Depósito → Incidencia 1 → Incidencia 2 → ... → Botadero → Depósito
   ```

4. **Polyline Encoding** 🎨
   - Compresión Google Polyline para eficiencia
   - ¡Reduce datos de MB a KB!

### Ejemplo Real:

```json
{
  "id": 18,
  "zona": "oriental",
  "puntos": 7,
  "distancia": "16.1 km",
  "duracion": "33 minutos",
  "polyline": "m~nlFtmzbNmAbB_@nA...",
  "incidencias": [
    {
      "tipo": "acopio",
      "ubicacion": "Barrio La Merced",
      "gravedad": 5,
      "lat": -0.9350,
      "lon": -78.6100
    }
  ]
}
```

---

## 🎯 Endpoints Estrella

| Método | Endpoint | Descripción | 🔥 Factor |
|--------|----------|-------------|----------|
| `POST` | `/api/auth/login` | Login del operador | ⭐⭐⭐ |
| `GET` | `/api/conductores/mis-rutas/todas` | Tus rutas asignadas | ⭐⭐⭐⭐ |
| `GET` | `/api/rutas/{id}` | **Ruta con polyline** | ⭐⭐⭐⭐⭐ |
| `GET` | `/api/rutas/{id}/detalles` | **Incidencias detalladas** | ⭐⭐⭐⭐⭐ |
| `POST` | `/api/conductores/iniciar-ruta` | Arranca tu recorrido | ⭐⭐⭐⭐ |
| `POST` | `/api/conductores/finalizar-ruta` | Misión cumplida | ⭐⭐⭐⭐ |
| `POST` | `/api/rutas/generar/{zona}` | Genera ruta nueva | ⭐⭐⭐⭐⭐ |

📚 **Docs completas:** [API_ENDPOINTS.md](API_ENDPOINTS.md)

---

## 🛠️ Stack Tecnológico

```
┌─────────────────────────────────────────┐
│  🎨 Frontend (Tu App)                   │
│  React/Flutter/Ionic/Lo que sea         │
└────────────┬────────────────────────────┘
             │ HTTP/REST
┌────────────▼────────────────────────────┐
│  ⚡ FastAPI Backend                     │
│  Python 3.11 + Pydantic + JWT           │
└────┬────────┬────────────┬──────────────┘
     │        │            │
     │        │            │
┌────▼────┐ ┌─▼────────┐ ┌▼──────────────┐
│ 🗄️ DB   │ │ 🗺️ OSRM  │ │ 🐰 RabbitMQ  │
│ Neon    │ │ Routing  │ │ (Opcional)    │
│ Postgres│ │ Engine   │ │               │
└─────────┘ └──────────┘ └───────────────┘
```

### Ingredientes principales:

- **FastAPI** 🚀 - El framework más rápido del oeste
- **OSRM** 🗺️ - Motor de rutas basado en OpenStreetMap
- **PostgreSQL** 🐘 - Base de datos geoespacial (PostGIS ready)
- **SQLAlchemy** 🔗 - ORM que no te hace llorar
- **JWT** 🔐 - Tokens seguros para auth
- **Docker** 🐳 - Porque "en mi máquina funciona"

---

## 📊 Estructura del Proyecto

```
Backend-latacunga-clean/
│
├── 🎯 app/
│   ├── routers/           # Los endpoints (la cara del sistema)
│   │   ├── rutas.py       # ⭐ EL JEFE - Gestión de rutas
│   │   ├── conductores.py # Operadores y asignaciones
│   │   ├── incidencias.py # Reportes ciudadanos
│   │   └── auth.py        # Login & JWT
│   │
│   ├── services/          # La lógica (el cerebro)
│   │   ├── ruta_service.py      # ⭐ Algoritmos de optimización
│   │   ├── conductor_service.py # Gestión de personal
│   │   └── incidencia_service.py# Procesamiento de reportes
│   │
│   ├── models.py          # Modelos de DB (SQLAlchemy)
│   ├── schemas.py         # Validaciones (Pydantic)
│   ├── database.py        # Conexión a PostgreSQL
│   ├── osrm_service.py    # ⭐ Cliente OSRM
│   └── main.py            # El punto de entrada
│
├── 🗺️ osrm-ecuador/      # Datos de mapas de Ecuador
│   └── ecuador-latest.osrm.*
│
├── 🐳 Docker files
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── docker-compose.prod.yml
│
├── 📚 Docs
│   ├── README.md                    # Estás aquí 👋
│   ├── API_ENDPOINTS.md             # Referencia completa de API
│   ├── GUIA_INTEGRACION_APP.md      # Para integrar con tu app
│   └── README_DOCKER.md             # Deployment guide
│
└── 🧪 Scripts útiles
    ├── preparar_datos_app.py        # Genera datos de prueba
    ├── health-check.py              # Verifica que todo funciona
    └── test_*.py                    # Tests BDD
```

---

## 🎨 Casos de Uso

### 🌅 Caso 1: "Es lunes por la mañana..."

```
1. El sistema acumula 25 reportes de basura del fin de semana
2. Umbral alcanzado (>20 puntos de gravedad)
3. 💥 Ruta generada automáticamente
4. 2 camiones asignados (posterior + lateral)
5. Conductores reciben notificación en su app
6. Rutas optimizadas: 16km en 33 minutos
7. ✅ Ciudad limpia antes del mediodía
```

### 🚨 Caso 2: "Animal muerto en vía principal"

```
1. Ciudadano reporta incidencia (gravedad: 5 pts)
2. Geolocalización automática
3. Agregado a zona occidental
4. Sistema espera más incidencias para optimizar
5. Al alcanzar umbral → Nueva ruta generada
6. Prioridad por gravedad: animal_muerto primero
7. ✅ Atendido en menos de 2 horas
```

### 📱 Caso 3: "Operador en campo"

```
1. Operador abre app móvil
2. Login → GET /api/auth/login
3. Ve sus rutas → GET /mis-rutas/todas
4. Selecciona ruta del día → GET /rutas/18
5. App decodifica polyline y muestra mapa
6. Inicia ruta → POST /iniciar-ruta
7. Navega punto por punto
8. Actualiza incidencias → PATCH /incidencias/{id}
9. Finaliza ruta → POST /finalizar-ruta
10. ✅ Sistema marca conductor como disponible
```

---

## 🔐 Seguridad

- ✅ JWT con expiración configurable
- ✅ Passwords hasheados con bcrypt
- ✅ CORS configurado por ambiente
- ✅ Variables sensibles en `.env` (nunca en git)
- ✅ HTTPs en producción (TLS 1.2+)

---

## 🌍 CORS & Integración

Configurado para trabajar con:
- 📱 Apps móviles (Capacitor, Ionic)
- 🖥️ Web apps (React, Vue, Angular)
- 🔧 Herramientas de desarrollo

```python
# En desarrollo: permite todo
ALLOWED_ORIGINS=*

# En producción: específica tus dominios
ALLOWED_ORIGINS=https://app.epagal.gob.ec,capacitor://localhost
```

---

## 🐛 Troubleshooting

### "No puedo conectar a la API"
```bash
# Verifica que el servidor esté corriendo
curl http://localhost:8081/

# Deberías ver: {"message": "API Sistema de..."}
```

### "Error de CORS"
```bash
# Verifica tu .env
ENV=development  # Esto permite todos los orígenes

# O agrega tu origen específico
ALLOWED_ORIGINS=http://localhost:3000
```

### "No genera rutas"
```bash
# Verifica OSRM
curl http://localhost:5000/route/v1/driving/-78.613,-0.936;-78.614,-0.937

# Debe devolver un JSON con "code": "Ok"
```

---

## 📚 Aprende Más

- 📖 [API_ENDPOINTS.md](API_ENDPOINTS.md) - Referencia completa de endpoints
- 🚀 [GUIA_INTEGRACION_APP.md](GUIA_INTEGRACION_APP.md) - Integra con tu frontend
- 🐳 [README_DOCKER.md](README_DOCKER.md) - Deploy en producción
- 💻 [Swagger UI](http://localhost:8081/docs) - Prueba interactiva

---

## 🎯 Roadmap

- [ ] WebSockets para tracking en tiempo real
- [ ] Machine Learning para predicción de puntos críticos
- [ ] Integración con IoT (sensores en contenedores)
- [ ] Reportes y analytics avanzados
- [ ] App móvil ciudadana para reportes

---

## 🤝 Contribuir

¿Tienes ideas? ¿Encontraste un bug? ¡Abre un issue o manda un PR!

---

## 📄 Licencia

[Tu licencia aquí]

---

## 👨‍💻 Autor

Desarrollado con ☕ y 💻 para EPAGAL Latacunga

---

<div align="center">

**¿Preguntas? ¿Sugerencias?**

⭐ Dale una estrella si este proyecto te ayudó

🐛 Reporta bugs en Issues

📧 Contacto: [tu-email]

</div>

---

> *"La basura no se recolecta sola... pero con este sistema, casi."* 🚛✨
