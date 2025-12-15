from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os 


# Cargar variables 
load_dotenv()

# Intentar DB_URL primero, luego DATABASE_URL
DATABASE_URL = os.getenv("DB_URL") or os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("No se encontró DB_URL o DATABASE_URL en el archivo .env")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Obtener la sesion de BD 
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally: db.close()
    
