"""
Router para gestión de operadores
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated, List
from pydantic import BaseModel
from datetime import datetime
from app.database import get_db
from app.models import User

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
    operadores = db.query(User).filter(User.role == "operador").all()
    # Convertir UUID a string para compatibilidad con Pydantic
    return [{
        "id": str(op.id),
        "email": op.email,
        "username": op.username,
        "phone": op.phone,
        "display_name": op.display_name,
        "role": op.role,
        "status": op.status
    } for op in operadores]


@router.post("/", response_model=OperadorResponse)
async def crear_operador(operador: OperadorCreate, db: Annotated[Session, Depends(get_db)]):
    """Crear nuevo operador"""
    # Verificar si el email ya existe
    if db.query(User).filter(User.email == operador.email).first():
        raise HTTPException(status_code=400, detail="El email ya existe")
    
    # Hash de la contraseña (simplificado)
    import hashlib
    password_hash = hashlib.sha256(operador.password.encode()).hexdigest()
    
    nuevo_operador = User(
        email=operador.email,
        username=operador.username,
        password_hash=password_hash,
        phone=operador.phone,
        display_name=operador.display_name,
        role=operador.role,
        status="ACTIVE",
        is_active=True,
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
        "phone": nuevo_operador.phone,
        "display_name": nuevo_operador.display_name,
        "role": nuevo_operador.role,
        "status": nuevo_operador.status
    }


@router.get("/{operador_id}", response_model=OperadorResponse)
async def obtener_operador(operador_id: str, db: Annotated[Session, Depends(get_db)]):
    """Obtener operador por ID"""
    operador = db.query(User).filter(User.id == operador_id).first()
    if not operador:
        raise HTTPException(status_code=404, detail="Operador no encontrado")
    return {
        "id": str(operador.id),
        "email": operador.email,
        "username": operador.username,
        "phone": operador.phone,
        "display_name": operador.display_name,
        "role": operador.role,
        "status": operador.status
    }


@router.put("/{operador_id}", response_model=OperadorResponse)
async def actualizar_operador(operador_id: str, operador: OperadorCreate, db: Annotated[Session, Depends(get_db)]):
    """Actualizar operador"""
    op_actual = db.query(User).filter(User.id == operador_id).first()
    if not op_actual:
        raise HTTPException(status_code=404, detail="Operador no encontrado")
    
    op_actual.email = operador.email
    op_actual.username = operador.username
    op_actual.phone = operador.phone
    op_actual.display_name = operador.display_name
    op_actual.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(op_actual)
    return {
        "id": str(op_actual.id),
        "email": op_actual.email,
        "username": op_actual.username,
        "phone": op_actual.phone,
        "display_name": op_actual.display_name,
        "role": op_actual.role,
        "status": op_actual.status
    }


@router.delete("/{operador_id}")
async def eliminar_operador(operador_id: str, db: Annotated[Session, Depends(get_db)]):
    """Eliminar operador"""
    operador = db.query(User).filter(User.id == operador_id).first()
    if not operador:
        raise HTTPException(status_code=404, detail="Operador no encontrado")
    
    db.delete(operador)
    db.commit()
    return {"message": "Operador eliminado"}
