"""
Router para gestión de operadores
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated, List
from pydantic import BaseModel
from datetime import datetime
from app.database import get_db
from app.models import Usuario

router = APIRouter(prefix="/operadores", tags=["operadores"])


class OperadorCreate(BaseModel):
    email: str
    username: str
    password: str
    phone: str | None = None
    display_name: str
    role: str = "operador"


class OperadorResponse(BaseModel):
    id: str
    email: str
    username: str
    phone: str | None
    display_name: str
    role: str
    status: str

    class Config:
        from_attributes = True


@router.get("/", response_model=List[OperadorResponse])
async def listar_operadores(db: Annotated[Session, Depends(get_db)]):
    """Listar todos los operadores"""
    operadores = db.query(Usuario).filter(Usuario.tipo_usuario == "operador").all()
    # Convertir respuesta para compatibilidad
    return [{
        "id": str(op.id),
        "email": op.email,
        "username": op.username,
        "phone": None,  # Campo no existe en modelo
        "display_name": op.username,  # Usar username como display_name
        "role": op.tipo_usuario,
        "status": "ACTIVE" if op.activo else "INACTIVE"
    } for op in operadores]


@router.post("/", response_model=OperadorResponse)
async def crear_operador(operador: OperadorCreate, db: Annotated[Session, Depends(get_db)]):
    """Crear nuevo operador"""
    # Verificar si el email ya existe
    if db.query(Usuario).filter(Usuario.email == operador.email).first():
        raise HTTPException(status_code=400, detail="El email ya existe")
    
    # Hash de la contraseña (simplificado)
    import hashlib
    password_hash = hashlib.sha256(operador.password.encode()).hexdigest()
    
    nuevo_operador = Usuario(
        email=operador.email,
        username=operador.username,
        password_hash=password_hash,
        tipo_usuario=operador.role if operador.role else "operador",
        activo=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(nuevo_operador)
    db.commit()
    db.refresh(nuevo_operador)
    
    return {
        "id": str(nuevo_operador.id),
        "email": nuevo_operador.email,
        "username": nuevo_operador.username,
        "phone": operador.phone,
        "display_name": operador.display_name,
        "role": nuevo_operador.tipo_usuario,
        "status": "ACTIVE" if nuevo_operador.activo else "INACTIVE"
    }


@router.get("/{operador_id}", response_model=OperadorResponse)
async def obtener_operador(operador_id: str, db: Annotated[Session, Depends(get_db)]):
    """Obtener operador por ID"""
    operador = db.query(Usuario).filter(Usuario.id == operador_id).first()
    if not operador:
        raise HTTPException(status_code=404, detail="Operador no encontrado")
    return {
        "id": str(operador.id),
        "email": operador.email,
        "username": operador.username,
        "phone": None,
        "display_name": operador.username,
        "role": operador.tipo_usuario,
        "status": "ACTIVE" if operador.activo else "INACTIVE"
    }


@router.put("/{operador_id}", response_model=OperadorResponse)
async def actualizar_operador(operador_id: str, operador: OperadorCreate, db: Annotated[Session, Depends(get_db)]):
    """Actualizar operador"""
    op_actual = db.query(Usuario).filter(Usuario.id == operador_id).first()
    if not op_actual:
        raise HTTPException(status_code=404, detail="Operador no encontrado")
    
    op_actual.email = operador.email
    op_actual.username = operador.username
    op_actual.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(op_actual)
    return {
        "id": str(op_actual.id),
        "email": op_actual.email,
        "username": op_actual.username,
        "phone": operador.phone,
        "display_name": operador.display_name,
        "role": op_actual.tipo_usuario,
        "status": "ACTIVE" if op_actual.activo else "INACTIVE"
    }


@router.delete("/{operador_id}")
async def eliminar_operador(operador_id: str, db: Annotated[Session, Depends(get_db)]):
    """Eliminar operador"""
    operador = db.query(Usuario).filter(Usuario.id == operador_id).first()
    if not operador:
        raise HTTPException(status_code=404, detail="Operador no encontrado")
    
    db.delete(operador)
    db.commit()
    return {"message": "Operador eliminado"}
