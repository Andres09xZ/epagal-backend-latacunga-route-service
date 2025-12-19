"""
Servicio de Gestión de Conductores y Asignaciones
Maneja conductores, asignaciones y disponibilidad
Fecha: 2025-12-13
"""
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from fastapi import HTTPException, status
from datetime import datetime

from app.models import Conductor, Usuario, AsignacionConductor, RutaGenerada
from app.schemas.conductores import (
    ConductorCreate, ConductorUpdate, ConductorResponse,
    ConductorDisponible, AsignacionCreate, AsignacionResponse,
    RutaConAsignaciones
)
from app.services.auth_service import AuthService


class ConductorService:
    """Servicio para gestión de conductores"""

    @staticmethod
    def crear_conductor(db: Session, data: ConductorCreate) -> Conductor:
        """
        Crea un nuevo conductor con su usuario asociado
        
        Args:
            db: Sesión de base de datos
            data: Datos del conductor a crear
            
        Returns:
            Conductor creado con su usuario
            
        Raises:
            HTTPException: Si hay errores de validación o duplicados
        """
        # Verificar cédula única
        conductor_existente = db.query(Conductor).filter(
            Conductor.cedula == data.cedula
        ).first()
        
        if conductor_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un conductor con cédula {data.cedula}"
            )
        
        try:
            # Crear usuario asociado
            from app.schemas.conductores import UsuarioCreate
            usuario_data = UsuarioCreate(
                username=data.username,
                email=data.email,
                password=data.password,
                tipo_usuario="conductor"
            )
            
            usuario = AuthService.create_user(db, usuario_data)
            
            # Crear conductor
            conductor = Conductor(
                usuario_id=usuario.id,
                nombre_completo=data.nombre_completo,
                cedula=data.cedula,
                telefono=data.telefono,
                licencia_tipo=data.licencia_tipo.value,
                zona_preferida=data.zona_preferida.value,
                estado='disponible'
            )
            
            db.add(conductor)
            db.commit()
            db.refresh(conductor)
            
            return conductor
            
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al crear conductor: {str(e)}"
            )

    @staticmethod
    def obtener_conductor(db: Session, conductor_id: int) -> Conductor:
        """
        Obtiene un conductor por ID con sus datos de usuario
        
        Args:
            db: Sesión de base de datos
            conductor_id: ID del conductor
            
        Returns:
            Conductor encontrado
            
        Raises:
            HTTPException: Si no se encuentra el conductor
        """
        conductor = db.query(Conductor).options(
            joinedload(Conductor.usuario)
        ).filter(Conductor.id == conductor_id).first()
        
        if not conductor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conductor con ID {conductor_id} no encontrado"
            )
        
        return conductor

    @staticmethod
    def listar_conductores(
        db: Session,
        estado: Optional[str] = None,
        zona: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Conductor]:
        """
        Lista conductores con filtros opcionales
        
        Args:
            db: Sesión de base de datos
            estado: Filtrar por estado (disponible, ocupado, inactivo)
            zona: Filtrar por zona preferida
            skip: Número de registros a saltar
            limit: Número máximo de registros
            
        Returns:
            Lista de conductores
        """
        query = db.query(Conductor).options(joinedload(Conductor.usuario))
        
        if estado:
            query = query.filter(Conductor.estado == estado)
        
        if zona:
            query = query.filter(
                or_(
                    Conductor.zona_preferida == zona,
                    Conductor.zona_preferida == 'ambas'
                )
            )
        
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def obtener_conductores_disponibles(
        db: Session,
        zona: Optional[str] = None
    ) -> List[ConductorDisponible]:
        """
        Obtiene conductores disponibles para asignación
        
        Args:
            db: Sesión de base de datos
            zona: Filtrar por zona (opcional)
            
        Returns:
            Lista de conductores disponibles
        """
        query = db.query(Conductor).filter(
            Conductor.estado == 'disponible'
        )
        
        if zona:
            query = query.filter(
                or_(
                    Conductor.zona_preferida == zona,
                    Conductor.zona_preferida == 'ambas'
                )
            )
        
        conductores = query.all()
        
        return [
            ConductorDisponible(
                id=c.id,
                nombre_completo=c.nombre_completo,
                cedula=c.cedula,
                telefono=c.telefono,
                licencia_tipo=c.licencia_tipo,
                zona_preferida=c.zona_preferida
            )
            for c in conductores
        ]

    @staticmethod
    def actualizar_conductor(
        db: Session,
        conductor_id: int,
        data: ConductorUpdate
    ) -> Conductor:
        """
        Actualiza información de un conductor
        
        Args:
            db: Sesión de base de datos
            conductor_id: ID del conductor
            data: Datos a actualizar
            
        Returns:
            Conductor actualizado
        """
        conductor = ConductorService.obtener_conductor(db, conductor_id)
        
        # Actualizar solo campos proporcionados
        update_data = data.model_dump(exclude_unset=True)
        
        for campo, valor in update_data.items():
            if hasattr(conductor, campo):
                if isinstance(valor, str):
                    setattr(conductor, campo, valor)
                else:
                    setattr(conductor, campo, valor.value if hasattr(valor, 'value') else valor)
        
        db.commit()
        db.refresh(conductor)
        
        return conductor

    @staticmethod
    def cambiar_estado_conductor(
        db: Session,
        conductor_id: int,
        nuevo_estado: str
    ) -> Conductor:
        """
        Cambia el estado de un conductor
        
        Args:
            db: Sesión de base de datos
            conductor_id: ID del conductor
            nuevo_estado: Nuevo estado (disponible, ocupado, inactivo)
            
        Returns:
            Conductor actualizado
        """
        conductor = ConductorService.obtener_conductor(db, conductor_id)
        conductor.estado = nuevo_estado
        
        db.commit()
        db.refresh(conductor)
        
        return conductor


class AsignacionService:
    """Servicio para gestión de asignaciones conductor-ruta"""

    @staticmethod
    def asignar_conductor(
        db: Session,
        data: AsignacionCreate
    ) -> AsignacionConductor:
        """
        Asigna un conductor a una ruta específica
        
        Args:
            db: Sesión de base de datos
            data: Datos de la asignación
            
        Returns:
            Asignación creada
            
        Raises:
            HTTPException: Si hay conflictos o validaciones fallidas
        """
        # Verificar que la ruta existe
        ruta = db.query(RutaGenerada).filter(
            RutaGenerada.id == data.ruta_id
        ).first()
        
        if not ruta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ruta {data.ruta_id} no encontrada"
            )
        
        # Verificar que el conductor existe y está disponible
        conductor = db.query(Conductor).filter(
            Conductor.id == data.conductor_id
        ).first()
        
        if not conductor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conductor {data.conductor_id} no encontrado"
            )
        
        if conductor.estado != 'disponible':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Conductor {conductor.nombre_completo} no está disponible (estado: {conductor.estado})"
            )
        
        # Verificar que no haya asignación duplicada
        asignacion_existente = db.query(AsignacionConductor).filter(
            and_(
                AsignacionConductor.ruta_id == data.ruta_id,
                AsignacionConductor.conductor_id == data.conductor_id,
                AsignacionConductor.estado.in_(['asignado', 'iniciado'])
            )
        ).first()
        
        if asignacion_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El conductor ya está asignado a esta ruta"
            )
        
        # Crear asignación
        asignacion = AsignacionConductor(
            ruta_id=data.ruta_id,
            conductor_id=data.conductor_id,
            camion_tipo=data.camion_tipo,
            camion_id=data.camion_id,
            fecha_inicio=getattr(data, 'fecha_inicio', None),
            estado='asignado'
        )
        
        db.add(asignacion)
        db.commit()
        db.refresh(asignacion)
        
        return asignacion

    @staticmethod
    def obtener_asignaciones_ruta(
        db: Session,
        ruta_id: int
    ) -> List[AsignacionConductor]:
        """
        Obtiene todas las asignaciones de una ruta
        
        Args:
            db: Sesión de base de datos
            ruta_id: ID de la ruta
            
        Returns:
            Lista de asignaciones con datos de conductores
        """
        return db.query(AsignacionConductor).options(
            joinedload(AsignacionConductor.conductor).joinedload(Conductor.usuario)
        ).filter(
            AsignacionConductor.ruta_id == ruta_id
        ).all()

    @staticmethod
    def obtener_asignaciones_conductor(
        db: Session,
        conductor_id: int,
        estado: Optional[str] = None
    ) -> List[AsignacionConductor]:
        """
        Obtiene todas las asignaciones de un conductor
        
        Args:
            db: Sesión de base de datos
            conductor_id: ID del conductor
            estado: Filtrar por estado de asignación (opcional)
            
        Returns:
            Lista de asignaciones
        """
        query = db.query(AsignacionConductor).options(
            joinedload(AsignacionConductor.ruta)
        ).filter(
            AsignacionConductor.conductor_id == conductor_id
        )
        
        if estado:
            query = query.filter(AsignacionConductor.estado == estado)
        
        return query.order_by(AsignacionConductor.fecha_asignacion.desc()).all()

    @staticmethod
    def iniciar_ruta(
        db: Session,
        asignacion_id: int
    ) -> AsignacionConductor:
        """
        Marca una asignación como iniciada
        
        Args:
            db: Sesión de base de datos
            asignacion_id: ID de la asignación
            
        Returns:
            Asignación actualizada
        """
        asignacion = db.query(AsignacionConductor).filter(
            AsignacionConductor.id == asignacion_id
        ).first()
        
        if not asignacion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asignación {asignacion_id} no encontrada"
            )
        
        if asignacion.estado != 'asignado':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La asignación no está en estado 'asignado' (estado actual: {asignacion.estado})"
            )
        
        asignacion.estado = 'iniciado'
        asignacion.fecha_inicio = datetime.utcnow()
        
        # Cambiar estado del conductor a ocupado
        conductor = db.query(Conductor).filter(
            Conductor.id == asignacion.conductor_id
        ).first()
        if conductor:
            conductor.estado = 'ocupado'
        
        # Cambiar estado de la ruta a en_ejecucion
        ruta = db.query(RutaGenerada).filter(
            RutaGenerada.id == asignacion.ruta_id
        ).first()
        if ruta and ruta.estado == 'planeada':
            ruta.estado = 'en_ejecucion'
        
        db.commit()
        db.refresh(asignacion)
        
        return asignacion

    @staticmethod
    def finalizar_ruta(
        db: Session,
        asignacion_id: int
    ) -> AsignacionConductor:
        """
        Marca una asignación como completada
        
        Args:
            db: Sesión de base de datos
            asignacion_id: ID de la asignación
            
        Returns:
            Asignación actualizada
        """
        asignacion = db.query(AsignacionConductor).filter(
            AsignacionConductor.id == asignacion_id
        ).first()
        
        if not asignacion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asignación {asignacion_id} no encontrada"
            )
        
        if asignacion.estado != 'iniciado':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La asignación no está en estado 'iniciado' (estado actual: {asignacion.estado})"
            )
        
        asignacion.estado = 'completado'
        asignacion.fecha_finalizacion = datetime.utcnow()
        
        # Cambiar estado del conductor a disponible
        conductor = db.query(Conductor).filter(
            Conductor.id == asignacion.conductor_id
        ).first()
        if conductor:
            conductor.estado = 'disponible'
        
        # Verificar si todas las asignaciones de la ruta están completadas
        ruta_id = asignacion.ruta_id
        asignaciones_pendientes = db.query(AsignacionConductor).filter(
            and_(
                AsignacionConductor.ruta_id == ruta_id,
                AsignacionConductor.estado.in_(['asignado', 'iniciado'])
            )
        ).count()
        
        # Si no hay asignaciones pendientes, marcar ruta como completada
        if asignaciones_pendientes == 0:
            ruta = db.query(RutaGenerada).filter(
                RutaGenerada.id == ruta_id
            ).first()
            if ruta:
                ruta.estado = 'completada'
        
        db.commit()
        db.refresh(asignacion)
        
        return asignacion
