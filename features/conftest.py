# features/conftest.py
"""
Configuración de fixtures para los tests BDD de geofencing
"""
import pytest
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import *  # Importar todos los modelos
from app.models.geofencing import *  # Importar modelos de geofencing


# Desactivar restricciones de foreign keys para SQLite en tests
def _fk_pragma_on_connect(dbapi_con, con_record):
    dbapi_con.execute('pragma foreign_keys=OFF')


@pytest.fixture(scope="function")
def db_session():
    """
    Crea una base de datos en memoria para cada test
    """
    # Crear engine SQLite en memoria
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Desactivar foreign keys para SQLite
    event.listen(engine, "connect", _fk_pragma_on_connect)
    
    # Crear todas las tablas (ignorará las columnas Geometry que no son compatibles con SQLite)
    Base.metadata.create_all(bind=engine)
    
    # Crear sesión
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db():
    """
    Alias para db_session para compatibilidad
    """
    return db_session
