# Guía de Configuración: Neon PostgreSQL + Geofencing

## 🌐 Sobre Neon PostgreSQL

**Neon** es un servicio de PostgreSQL Serverless con las siguientes características:

- ✅ **Serverless**: Escala automáticamente a 0 cuando no hay conexiones
- ✅ **Branching**: Crea branches de BD como Git
- ✅ **PostgreSQL 15+**: Compatible con PostGIS 3.4+
- ✅ **Conexión directa**: Usa `psycopg2` o SQLAlchemy estándar
- ✅ **Pooling integrado**: Connection pooling automático
- ⚠️ **Limitaciones gratuitas**: 
  - 0.5 GB storage
  - 1 proyecto
  - Autosuspensión después de 5 min inactividad

## 🔧 Configuración Inicial

### 1. Habilitar PostGIS en Neon

**Opción A: Desde la Consola Web de Neon**
```
1. Ir a https://console.neon.tech
2. Seleccionar tu proyecto
3. Ir a "SQL Editor"
4. Ejecutar:
   CREATE EXTENSION IF NOT EXISTS postgis CASCADE;
5. Verificar:
   SELECT PostGIS_Version();
```

**Opción B: Desde tu Terminal Local**
```bash
# Usar el connection string de Neon
psql "postgresql://user:password@ep-xxx.region.aws.neon.tech/neondb?sslmode=require"

# Dentro de psql:
neondb=> CREATE EXTENSION IF NOT EXISTS postgis CASCADE;
neondb=> SELECT PostGIS_Version();
```

### 2. Configurar Variables de Entorno

Crea o actualiza tu archivo `.env`:

```bash
# .env
# Neon PostgreSQL Connection String
# Formato: postgresql://[user]:[password]@[endpoint]/[database]?sslmode=require
DATABASE_URL=postgresql://tu_usuario:tu_password@ep-xxx-xxx.region.aws.neon.tech/neondb?sslmode=require

# Opciones de pooling (Neon tiene pooler integrado)
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# Secret para JWT
SECRET_KEY=tu_secret_key_aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OSRM Service
OSRM_URL=http://router.project-osrm.org

# Redis (opcional, para caché)
REDIS_URL=redis://localhost:6379/0
```

### 3. Actualizar database.py para Neon

Tu archivo `app/database.py` debería verse así:

```python
# app/database.py
import os
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Obtener URL de Neon desde variable de entorno
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL no está configurada en .env")

# IMPORTANTE: Neon requiere SSL
# Asegurarse de que la URL tenga ?sslmode=require
if "sslmode" not in DATABASE_URL:
    DATABASE_URL += ("&" if "?" in DATABASE_URL else "?") + "sslmode=require"

# Configuración optimizada para Neon (serverless)
engine = create_engine(
    DATABASE_URL,
    pool_size=int(os.getenv("DB_POOL_SIZE", 5)),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", 10)),
    pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", 30)),
    pool_recycle=int(os.getenv("DB_POOL_RECYCLE", 3600)),  # 1 hora
    pool_pre_ping=True,  # Verificar conexión antes de usar
    echo=False  # True para debug SQL
)

# Configurar para trabajar con PostGIS
@event.listens_for(engine, "connect")
def set_search_path(dbapi_conn, connection_record):
    existing_autocommit = dbapi_conn.autocommit
    dbapi_conn.autocommit = True
    cursor = dbapi_conn.cursor()
    cursor.execute("SET search_path TO public")
    cursor.close()
    dbapi_conn.autocommit = existing_autocommit

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency para FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

## 🚀 Aplicar Migraciones

### Método 1: Usando psql (Recomendado para Neon)

```bash
# 1. Conectar a Neon
psql "postgresql://user:password@ep-xxx.region.aws.neon.tech/neondb?sslmode=require"

# 2. Ejecutar migración
\i 'D:/Octavo Semestre/Tesis/Backend-latacunga-clean/migrations/005_sistema_geofencing.sql'

# 3. Verificar tablas creadas
\dt

# Deberías ver:
# geofence_alerts
# geofence_config
# historial_posiciones
# zonas_geograficas
# estadisticas_geofencing

# 4. Verificar PostGIS
SELECT PostGIS_Version();

# 5. Verificar zonas cargadas
SELECT nombre, tipo, activa FROM zonas_geograficas;
```

### Método 2: Usando Python Script

Crea `aplicar_migracion_geofencing.py`:

```python
# aplicar_migracion_geofencing.py
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Leer archivo SQL
with open('migrations/005_sistema_geofencing.sql', 'r', encoding='utf-8') as f:
    sql = f.read()

# Conectar y ejecutar
conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
cursor = conn.cursor()

try:
    print("Ejecutando migración 005_sistema_geofencing.sql...")
    cursor.execute(sql)
    print("✅ Migración completada exitosamente")
    
    # Verificar tablas
    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE '%geofenc%'
        ORDER BY table_name;
    """)
    
    print("\nTablas creadas:")
    for table in cursor.fetchall():
        print(f"  - {table[0]}")
    
    # Verificar zonas
    cursor.execute("SELECT COUNT(*) FROM zonas_geograficas;")
    count = cursor.fetchone()[0]
    print(f"\nZonas geográficas insertadas: {count}")
    
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    cursor.close()
    conn.close()
```

Ejecutar:
```bash
python aplicar_migracion_geofencing.py
```

### Método 3: Desde SQL Editor de Neon

```
1. Ir a https://console.neon.tech
2. Seleccionar tu proyecto
3. Ir a "SQL Editor"
4. Copiar y pegar el contenido de migrations/005_sistema_geofencing.sql
5. Click en "Run" o Ctrl+Enter
6. Verificar que se ejecutó sin errores
```

## ⚡ Consideraciones de Rendimiento en Neon

### 1. Connection Pooling

Neon tiene **connection pooling integrado**, pero debes configurar correctamente:

```python
# Configuración recomendada para Neon
engine = create_engine(
    DATABASE_URL,
    pool_size=5,           # Conexiones en pool
    max_overflow=10,       # Conexiones extra bajo carga
    pool_timeout=30,       # Timeout para obtener conexión
    pool_recycle=3600,     # Reciclar conexiones cada 1h
    pool_pre_ping=True     # Verificar antes de usar (IMPORTANTE)
)
```

### 2. Auto-Suspensión

Neon se suspende después de **5 minutos de inactividad** en el plan gratuito:

- **Primera consulta después de suspensión**: ~1-2 segundos (cold start)
- **Solución**: Usar `pool_pre_ping=True` para detectar y reconectar automáticamente

### 3. Índices GIST

Los índices espaciales **GIST** son cruciales para rendimiento:

```sql
-- Ya incluidos en la migración
CREATE INDEX idx_zonas_geometria ON zonas_geograficas USING GIST (geometria);
CREATE INDEX idx_historial_geometria ON historial_posiciones USING GIST (geometria);
CREATE INDEX idx_alerts_geometria ON geofence_alerts USING GIST (geometria);
```

Verificar que se crearon:
```sql
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE indexname LIKE '%geometria%';
```

### 4. Límites del Plan Gratuito

| Recurso | Límite Gratuito | Notas |
|---------|-----------------|-------|
| Storage | 0.5 GB | ~500,000 posiciones GPS |
| Compute | 100h/mes | Suficiente para desarrollo |
| Connections | Ilimitadas | Usa pooling |
| Autosuspensión | 5 min | No configurable en free tier |

## 🔍 Verificación Post-Migración

### 1. Verificar PostGIS

```sql
-- Versión de PostGIS
SELECT PostGIS_Version();
-- Esperado: 3.4.x

-- Funciones PostGIS disponibles
SELECT proname FROM pg_proc WHERE proname LIKE 'st_%' LIMIT 10;
```

### 2. Verificar Tablas

```sql
-- Listar todas las tablas de geofencing
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as columnas
FROM information_schema.tables t
WHERE table_schema = 'public'
AND table_name IN (
    'geofence_config',
    'zonas_geograficas',
    'historial_posiciones',
    'geofence_alerts',
    'estadisticas_geofencing'
)
ORDER BY table_name;
```

### 3. Verificar Configuración

```sql
-- Parámetros de geofencing
SELECT parametro, valor, unidad, activo 
FROM geofence_config 
ORDER BY parametro;

-- Esperado: 10 parámetros
```

### 4. Verificar Zonas Geográficas

```sql
-- Zonas cargadas
SELECT 
    nombre,
    tipo,
    ST_AsText(geometria) as geometria_wkt,
    activa
FROM zonas_geograficas;

-- Esperado: 3 zonas (zona_occidental, zona_oriental, cobertura_epagal)
```

### 5. Test de Función PostGIS

```sql
-- Probar función punto_en_zona
SELECT punto_en_zona(-0.9360, -78.6216, 'zona_occidental') as esta_en_zona;
-- Esperado: true (si el punto está en zona occidental)

-- Probar ST_Contains directamente
SELECT ST_Contains(
    (SELECT geometria FROM zonas_geograficas WHERE nombre = 'cobertura_epagal'),
    ST_SetSRID(ST_MakePoint(-78.6216, -0.9360), 4326)
) as dentro_cobertura;
-- Esperado: true
```

## 🧪 Testing con Neon

### Configurar Test Database

Neon permite crear **branches** de tu BD:

```
1. En Neon Console → "Branches"
2. Crear branch "test" desde "main"
3. Obtener connection string del branch test
4. Usar en tests
```

Archivo `pytest.ini`:
```ini
[pytest]
env =
    DATABASE_URL=postgresql://user:pass@ep-xxx-test.neon.tech/neondb?sslmode=require
```

O en código:
```python
# conftest.py
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="session")
def db_engine():
    # Usar branch de test de Neon
    test_url = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")
    engine = create_engine(test_url, pool_pre_ping=True)
    yield engine
    engine.dispose()
```

## 🐛 Troubleshooting

### Error: "extension postgis does not exist"

```sql
-- Solución: Habilitar PostGIS con CASCADE
CREATE EXTENSION IF NOT EXISTS postgis CASCADE;

-- Verificar
SELECT extname, extversion FROM pg_extension WHERE extname = 'postgis';
```

### Error: "SSL connection required"

```python
# Asegurarse de incluir ?sslmode=require en la URL
DATABASE_URL = "postgresql://user:pass@host/db?sslmode=require"
```

### Error: "connection timeout"

```python
# Aumentar pool_timeout y habilitar pool_pre_ping
engine = create_engine(
    DATABASE_URL,
    pool_timeout=60,      # 60 segundos
    pool_pre_ping=True    # Verificar antes de usar
)
```

### Error: "too many connections"

```python
# Reducir pool_size para Neon free tier
engine = create_engine(
    DATABASE_URL,
    pool_size=3,          # Máximo 3 conexiones
    max_overflow=5
)
```

### Warning: "Neon database suspended"

```python
# Esto es normal después de 5 min de inactividad
# pool_pre_ping=True maneja automáticamente la reconexión
# Primera query después de suspensión tarda ~1-2 segundos
```

## 📊 Monitoreo en Neon

### Dashboard de Neon

```
1. Ir a https://console.neon.tech
2. Seleccionar proyecto
3. Ver métricas:
   - CPU usage
   - Storage used
   - Active connections
   - Queries per second
```

### Query desde Python

```python
# health_check_neon.py
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cursor = conn.cursor()

# Stats de conexiones
cursor.execute("""
    SELECT 
        COUNT(*) as total_connections,
        COUNT(*) FILTER (WHERE state = 'active') as active,
        COUNT(*) FILTER (WHERE state = 'idle') as idle
    FROM pg_stat_activity
    WHERE datname = current_database();
""")
print("Conexiones:", cursor.fetchone())

# Tamaño de BD
cursor.execute("""
    SELECT 
        pg_size_pretty(pg_database_size(current_database())) as size;
""")
print("Tamaño BD:", cursor.fetchone()[0])

# Tablas más grandes
cursor.execute("""
    SELECT 
        schemaname,
        tablename,
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
    FROM pg_tables
    WHERE schemaname = 'public'
    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
    LIMIT 5;
""")
print("\nTop 5 tablas más grandes:")
for row in cursor.fetchall():
    print(f"  {row[1]}: {row[2]}")

cursor.close()
conn.close()
```

## 🚀 Deploy a Producción

### Checklist Pre-Deploy

- [ ] PostGIS habilitado en Neon
- [ ] Migración 005 aplicada exitosamente
- [ ] Variables de entorno configuradas
- [ ] SSL habilitado (`?sslmode=require`)
- [ ] Connection pooling configurado
- [ ] Índices GIST creados
- [ ] Zonas geográficas insertadas
- [ ] Tests BDD pasando

### Variables de Entorno en Render/Vercel

```bash
DATABASE_URL=postgresql://user:pass@ep-xxx.aws.neon.tech/neondb?sslmode=require
SECRET_KEY=your_production_secret_key_here
OSRM_URL=http://router.project-osrm.org
```

## 📚 Referencias

- **Neon Docs**: https://neon.tech/docs
- **PostGIS + Neon**: https://neon.tech/docs/extensions/postgis
- **SQLAlchemy + Neon**: https://neon.tech/docs/guides/sqlalchemy
- **Connection Pooling**: https://neon.tech/docs/connect/connection-pooling

---

**Última actualización:** Enero 2025  
**Compatible con:** Neon PostgreSQL 15+, PostGIS 3.4+
