"""
Router para Tareas
Endpoints para gestión de tareas de recolección
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.routers.auth import get_current_user
from app.models import Usuario

router = APIRouter(
    prefix="/api/tasks",
    tags=["Tareas"]
)


@router.get("/")
def listar_tareas(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    estado: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Listar tareas del conductor actual
    """
    # Placeholder - implementar según el modelo de datos
    return {
        "total": 0,
        "skip": skip,
        "limit": limit,
        "tareas": []
    }


@router.post("/")
def crear_tarea(
    tarea_data: dict,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crear una nueva tarea
    """
    return {
        "id": 1,
        "descripcion": tarea_data.get("descripcion", ""),
        "estado": "pendiente",
        "fecha_creacion": datetime.now()
    }


@router.put("/{task_id}")
def actualizar_tarea(
    task_id: int,
    tarea_data: dict,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Actualizar una tarea existente
    """
    return {
        "id": task_id,
        "estado": tarea_data.get("estado", "pendiente")
    }


@router.post("/{task_id}/complete")
def completar_tarea(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Marcar una tarea como completada
    """
    return {
        "id": task_id,
        "estado": "completada",
        "fecha_completacion": datetime.now()
    }
