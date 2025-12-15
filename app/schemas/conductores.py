"""
Schemas de Pydantic para Autenticación y Conductores
Fecha: 2025-12-13
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class TipoUsuario(str, Enum):
    """Tipos de usuario en el sistema"""
    admin = "admin"
    conductor = "conductor"
    ciudadano = "ciudadano"


class EstadoConductor(str, Enum):
    """Estados posibles de un conductor"""
    disponible = "disponible"
    ocupado = "ocupado"
    inactivo = "inactivo"


class ZonaPreferida(str, Enum):
    """Zonas de operación del conductor"""
    oriental = "oriental"
    occidental = "occidental"
    ambas = "ambas"


class LicenciaTipo(str, Enum):
    """Tipos de licencia de conducir"""
    C = "C"
    D = "D"
    E = "E"


class EstadoAsignacion(str, Enum):
    """Estados de asignación conductor-ruta"""
    asignado = "asignado"
    iniciado = "iniciado"
    completado = "completado"
    cancelado = "cancelado"


# ================== SCHEMAS DE AUTENTICACIÓN ==================

class LoginRequest(BaseModel):
    """Request para login de usuarios"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "conductor1",
                "password": "conductor123"
            }
        }
    }


class TokenResponse(BaseModel):
    """Response con token de autenticación"""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    tipo_usuario: TipoUsuario
    conductor_id: Optional[int] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user_id": 2,
                "username": "conductor1",
                "tipo_usuario": "conductor",
                "conductor_id": 1
            }
        }
    }


class UsuarioBase(BaseModel):
    """Base para Usuario"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    tipo_usuario: TipoUsuario = TipoUsuario.ciudadano


class UsuarioCreate(UsuarioBase):
    """Schema para crear usuario"""
    password: str = Field(..., min_length=6, description="Contraseña (mínimo 6 caracteres)")


class UsuarioResponse(UsuarioBase):
    """Response de Usuario"""
    id: int
    activo: bool
    created_at: datetime
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 2,
                "username": "conductor1",
                "email": "juan.perez@epagal.gob.ec",
                "tipo_usuario": "conductor",
                "activo": True,
                "created_at": "2025-12-13T10:30:00"
            }
        }
    }


class UsuarioMe(UsuarioResponse):
    """Usuario actual autenticado"""
    conductor_id: Optional[int] = None


# ================== SCHEMAS DE CONDUCTORES ==================

class ConductorBase(BaseModel):
    """Base para Conductor"""
    nombre_completo: str = Field(..., min_length=5, max_length=100)
    cedula: str = Field(..., pattern=r'^\d{10}$', description="Cédula ecuatoriana de 10 dígitos")
    telefono: Optional[str] = Field(None, pattern=r'^\d{9,10}$')
    licencia_tipo: LicenciaTipo
    zona_preferida: ZonaPreferida = ZonaPreferida.ambas
    
    @field_validator('cedula')
    @classmethod
    def validar_cedula(cls, v: str) -> str:
        """Valida que la cédula sea ecuatoriana"""
        if len(v) != 10:
            raise ValueError("La cédula debe tener 10 dígitos")
        if not v.isdigit():
            raise ValueError("La cédula debe contener solo números")
        # Validación de provincia (primeros 2 dígitos)
        provincia = int(v[:2])
        if provincia < 1 or provincia > 24:
            raise ValueError("Código de provincia inválido (01-24)")
        return v


class ConductorCreate(ConductorBase):
    """Schema para crear conductor (incluye datos de usuario)"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, description="Contraseña inicial")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "conductor5",
                "email": "pedro.ramirez@epagal.gob.ec",
                "password": "conductor123",
                "nombre_completo": "Pedro Ramírez Flores",
                "cedula": "1807890123",
                "telefono": "0987654325",
                "licencia_tipo": "C",
                "zona_preferida": "occidental"
            }
        }
    }


class ConductorUpdate(BaseModel):
    """Schema para actualizar conductor"""
    nombre_completo: Optional[str] = Field(None, min_length=5, max_length=100)
    telefono: Optional[str] = Field(None, pattern=r'^\d{9,10}$')
    licencia_tipo: Optional[LicenciaTipo] = None
    estado: Optional[EstadoConductor] = None
    zona_preferida: Optional[ZonaPreferida] = None


class ConductorResponse(ConductorBase):
    """Response de Conductor"""
    id: int
    usuario_id: int
    estado: EstadoConductor
    fecha_contratacion: datetime
    created_at: datetime
    
    # Datos del usuario relacionado
    username: Optional[str] = None
    email: Optional[str] = None
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "usuario_id": 2,
                "nombre_completo": "Juan Pérez Martínez",
                "cedula": "1803456789",
                "telefono": "0987654321",
                "licencia_tipo": "C",
                "estado": "disponible",
                "zona_preferida": "oriental",
                "fecha_contratacion": "2025-01-15T08:00:00",
                "created_at": "2025-01-15T08:00:00",
                "username": "conductor1",
                "email": "juan.perez@epagal.gob.ec"
            }
        }
    }


class ConductorDisponible(BaseModel):
    """Conductor disponible para asignación"""
    id: int
    nombre_completo: str
    cedula: str
    telefono: Optional[str]
    licencia_tipo: LicenciaTipo
    zona_preferida: ZonaPreferida
    
    model_config = {"from_attributes": True}


# ================== SCHEMAS DE ASIGNACIONES ==================

class AsignacionCreate(BaseModel):
    """Schema para crear asignación"""
    ruta_id: int = Field(..., gt=0)
    conductor_id: int = Field(..., gt=0)
    camion_tipo: str = Field(..., pattern=r'^(lateral|posterior)$')
    camion_id: Optional[str] = Field(None, max_length=20, description="Placa del camión")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "ruta_id": 1,
                "conductor_id": 1,
                "camion_tipo": "posterior",
                "camion_id": "LAT-001"
            }
        }
    }


class AsignacionResponse(BaseModel):
    """Response de Asignación"""
    id: int
    ruta_id: int
    conductor_id: int
    camion_tipo: str
    camion_id: Optional[str]
    fecha_asignacion: datetime
    fecha_inicio: Optional[datetime]
    fecha_finalizacion: Optional[datetime]
    estado: EstadoAsignacion
    
    # Datos del conductor
    conductor_nombre: Optional[str] = None
    conductor_cedula: Optional[str] = None
    conductor_telefono: Optional[str] = None
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "ruta_id": 1,
                "conductor_id": 1,
                "camion_tipo": "posterior",
                "camion_id": "LAT-001",
                "fecha_asignacion": "2025-12-13T10:00:00",
                "fecha_inicio": None,
                "fecha_finalizacion": None,
                "estado": "asignado",
                "conductor_nombre": "Juan Pérez Martínez",
                "conductor_cedula": "1803456789",
                "conductor_telefono": "0987654321"
            }
        }
    }


class IniciarRutaRequest(BaseModel):
    """Request para iniciar una ruta"""
    ruta_id: int = Field(..., gt=0)


class FinalizarRutaRequest(BaseModel):
    """Request para finalizar una ruta"""
    ruta_id: int = Field(..., gt=0)
    notas: Optional[str] = Field(None, max_length=500, description="Observaciones al finalizar")


# ================== SCHEMAS COMBINADOS ==================

class RutaConAsignaciones(BaseModel):
    """Ruta con sus conductores asignados"""
    id: int
    zona: str
    estado: str
    suma_gravedad: int
    camiones_usados: int
    fecha_generacion: datetime
    asignaciones: List[AsignacionResponse] = []
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "zona": "oriental",
                "estado": "planeada",
                "suma_gravedad": 25,
                "camiones_usados": 2,
                "fecha_generacion": "2025-12-13T10:00:00",
                "asignaciones": [
                    {
                        "id": 1,
                        "conductor_id": 1,
                        "camion_tipo": "posterior",
                        "camion_id": "LAT-001",
                        "estado": "asignado",
                        "conductor_nombre": "Juan Pérez Martínez"
                    },
                    {
                        "id": 2,
                        "conductor_id": 2,
                        "camion_tipo": "lateral",
                        "camion_id": "LAT-002",
                        "estado": "asignado",
                        "conductor_nombre": "María López García"
                    }
                ]
            }
        }
    }


class MisRutasResponse(BaseModel):
    """Rutas asignadas a un conductor"""
    total: int
    asignado: int
    iniciado: int
    completado: int
    rutas: List[RutaConAsignaciones] = []
