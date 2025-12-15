"""
Servicio de Autenticación con JWT y Bcrypt
Maneja login, registro y validación de tokens
Fecha: 2025-12-13
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models import Usuario, Conductor
from app.schemas.conductores import UsuarioCreate, LoginRequest, TokenResponse


# Configuración de seguridad
SECRET_KEY = "tu-clave-secreta-super-segura-cambiala-en-produccion-123456"  # ⚠️ Cambiar en producción
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 horas


class AuthService:
    """Servicio de autenticación y gestión de usuarios"""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Genera hash de contraseña con bcrypt
        
        Args:
            password: Contraseña en texto plano
            
        Returns:
            Hash bcrypt de la contraseña
        """
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password_bytes, salt).decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verifica si una contraseña coincide con su hash
        
        Args:
            plain_password: Contraseña en texto plano
            hashed_password: Hash bcrypt almacenado
            
        Returns:
            True si coinciden, False si no
        """
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Crea un token JWT con los datos proporcionados
        
        Args:
            data: Diccionario con datos a incluir en el token
            expires_delta: Tiempo de expiración personalizado
            
        Returns:
            Token JWT firmado
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        return encoded_jwt

    @staticmethod
    def decode_access_token(token: str) -> dict:
        """
        Decodifica y valida un token JWT
        
        Args:
            token: Token JWT a decodificar
            
        Returns:
            Payload del token decodificado
            
        Raises:
            HTTPException: Si el token es inválido o expiró
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token inválido o expirado: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[Usuario]:
        """
        Busca un usuario por username
        
        Args:
            db: Sesión de base de datos
            username: Nombre de usuario a buscar
            
        Returns:
            Usuario encontrado o None
        """
        return db.query(Usuario).filter(
            Usuario.username == username,
            Usuario.activo == True
        ).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[Usuario]:
        """
        Busca un usuario por email
        
        Args:
            db: Sesión de base de datos
            email: Email a buscar
            
        Returns:
            Usuario encontrado o None
        """
        return db.query(Usuario).filter(
            Usuario.email == email,
            Usuario.activo == True
        ).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[Usuario]:
        """
        Busca un usuario por ID
        
        Args:
            db: Sesión de base de datos
            user_id: ID del usuario
            
        Returns:
            Usuario encontrado o None
        """
        return db.query(Usuario).filter(
            Usuario.id == user_id,
            Usuario.activo == True
        ).first()

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[Usuario]:
        """
        Autentica un usuario verificando username y contraseña
        
        Args:
            db: Sesión de base de datos
            username: Nombre de usuario
            password: Contraseña en texto plano
            
        Returns:
            Usuario autenticado o None si las credenciales son inválidas
        """
        user = AuthService.get_user_by_username(db, username)
        
        if not user:
            return None
        
        if not AuthService.verify_password(password, user.password_hash):
            return None
        
        return user

    @staticmethod
    def login(db: Session, credentials: LoginRequest) -> TokenResponse:
        """
        Realiza el proceso de login completo
        
        Args:
            db: Sesión de base de datos
            credentials: Username y password
            
        Returns:
            Token de acceso y datos del usuario
            
        Raises:
            HTTPException: Si las credenciales son inválidas
        """
        # Autenticar usuario
        user = AuthService.authenticate_user(
            db, 
            credentials.username, 
            credentials.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Buscar información de conductor si es tipo conductor
        conductor_id = None
        if user.tipo_usuario == "conductor":
            conductor = db.query(Conductor).filter(
                Conductor.usuario_id == user.id
            ).first()
            if conductor:
                conductor_id = conductor.id
        
        # Crear token JWT
        access_token = AuthService.create_access_token(
            data={
                "sub": user.username,
                "user_id": user.id,
                "tipo_usuario": user.tipo_usuario,
                "conductor_id": conductor_id
            }
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user.id,
            username=user.username,
            tipo_usuario=user.tipo_usuario,
            conductor_id=conductor_id
        )

    @staticmethod
    def create_user(db: Session, user_data: UsuarioCreate) -> Usuario:
        """
        Crea un nuevo usuario en el sistema
        
        Args:
            db: Sesión de base de datos
            user_data: Datos del usuario a crear
            
        Returns:
            Usuario creado
            
        Raises:
            HTTPException: Si el username o email ya existen
        """
        # Verificar username único
        existing_user = AuthService.get_user_by_username(db, user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El username '{user_data.username}' ya está en uso"
            )
        
        # Verificar email único
        existing_email = AuthService.get_user_by_email(db, user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El email '{user_data.email}' ya está registrado"
            )
        
        # Hashear contraseña
        hashed_password = AuthService.hash_password(user_data.password)
        
        # Crear usuario
        new_user = Usuario(
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password,
            tipo_usuario=user_data.tipo_usuario
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return new_user

    @staticmethod
    def get_current_user_from_token(db: Session, token: str) -> Usuario:
        """
        Obtiene el usuario actual desde un token JWT
        
        Args:
            db: Sesión de base de datos
            token: Token JWT
            
        Returns:
            Usuario autenticado
            
        Raises:
            HTTPException: Si el token es inválido o el usuario no existe
        """
        payload = AuthService.decode_access_token(token)
        
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: no se encontró el username",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = AuthService.get_user_by_username(db, username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
