from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os 


# Cargar variables 
load_dotenv()

# Intentar DB_URL primero, luego DATABASE_URL (compatibilidad)
DATABASE_URL = os.getenv("DB_URL") or os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("No se encontró DB_URL o DATABASE_URL en el archivo .env")

# Configuración optimizada para Neon PostgreSQL (serverless)
engine = create_engine(
    DATABASE_URL,
    pool_size=int(os.getenv("DB_POOL_SIZE", 5)),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", 10)),
    pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", 30)),
    pool_recycle=int(os.getenv("DB_POOL_RECYCLE", 3600)),  # 1 hora
    pool_pre_ping=True,  # IMPORTANTE: Reconecta después de autosuspensión de Neon
    echo=False  # True para debug SQL
)

# Configurar search_path para PostGIS
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

# Obtener la sesion de BD 
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally: 
        db.close()
    
