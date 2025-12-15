"""
Router de Autenticación
Endpoints para login, logout y gestión de sesión
Fecha: 2025-12-13
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.conductores import (
    LoginRequest, TokenResponse, UsuarioMe, UsuarioResponse
)
from app.services.auth_service import AuthService
from app.models import Usuario, Conductor


router = APIRouter(prefix="/api/auth", tags=["Autenticación"])

# Esquema HTTPBearer para tokens (más simple en Swagger)
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Usuario:
    """
    Dependency para obtener el usuario actual desde el token JWT
    
    Args:
        credentials: Credenciales HTTP Bearer con el token
        db: Sesión de base de datos
        
    Returns:
        Usuario autenticado
        
    Raises:
        HTTPException: Si el token es inválido
    """
    return AuthService.get_current_user_from_token(db, credentials.credentials)


async def get_current_admin(
    current_user: Usuario = Depends(get_current_user)
) -> Usuario:
    """
    Dependency que verifica que el usuario sea administrador
    
    Args:
        current_user: Usuario autenticado
        
    Returns:
        Usuario administrador
        
    Raises:
        HTTPException: Si no es administrador
    """
    if current_user.tipo_usuario != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador"
        )
    return current_user


async def get_current_conductor(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Conductor:
    """
    Dependency que verifica que el usuario sea conductor y retorna su info
    
    Args:
        current_user: Usuario autenticado
        db: Sesión de base de datos
        
    Returns:
        Conductor autenticado
        
    Raises:
        HTTPException: Si no es conductor o no existe registro
    """
    if current_user.tipo_usuario != "conductor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo conductores pueden acceder a este recurso"
        )
    
    conductor = db.query(Conductor).filter(
        Conductor.usuario_id == current_user.id
    ).first()
    
    if not conductor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de conductor no encontrado"
        )
    
    return conductor


@router.post("/login", response_model=TokenResponse, summary="Iniciar sesión")
async def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint de login con username y contraseña
    
    **Usuarios de prueba:**
    - admin / admin123 (Administrador)
    - conductor1 / conductor123 (Conductor - Oriental)
    - conductor2 / conductor123 (Conductor - Occidental)
    
    Retorna un token JWT válido por 8 horas.
    """
    return AuthService.login(db, credentials)


@router.post("/login/form", response_model=TokenResponse, summary="Login con OAuth2")
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Endpoint de login compatible con OAuth2 (para Swagger UI)
    
    Mismo funcionamiento que /login pero usando el formato OAuth2.
    """
    credentials = LoginRequest(
        username=form_data.username,
        password=form_data.password
    )
    return AuthService.login(db, credentials)


@router.get("/me", response_model=UsuarioMe, summary="Obtener usuario actual")
async def get_me(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene información del usuario autenticado actual
    
    Incluye conductor_id si el usuario es de tipo conductor.
    """
    conductor_id = None
    
    if current_user.tipo_usuario == "conductor":
        conductor = db.query(Conductor).filter(
            Conductor.usuario_id == current_user.id
        ).first()
        if conductor:
            conductor_id = conductor.id
    
    return UsuarioMe(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        tipo_usuario=current_user.tipo_usuario,
        activo=current_user.activo,
        created_at=current_user.created_at,
        conductor_id=conductor_id
    )


@router.post("/logout", summary="Cerrar sesión")
async def logout(
    current_user: Usuario = Depends(get_current_user)
):
    """
    Cierra la sesión del usuario actual
    
    En esta implementación simple, el cliente debe eliminar el token.
    Para invalidación de tokens se necesitaría una lista negra o Redis.
    """
    return {
        "message": f"Sesión cerrada exitosamente para {current_user.username}",
        "detail": "El token seguirá siendo válido hasta su expiración. Elimínalo del cliente."
    }


@router.get("/verify-token", summary="Verificar token")
async def verify_token(
    current_user: Usuario = Depends(get_current_user)
):
    """
    Verifica que el token sea válido
    
    Útil para validar tokens antes de hacer operaciones críticas.
    """
    return {
        "valid": True,
        "user_id": current_user.id,
        "username": current_user.username,
        "tipo_usuario": current_user.tipo_usuario
    }
