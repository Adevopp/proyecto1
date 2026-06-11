"""
Service para la entidad Sala - Lógica de negocio
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from models import Sala
from repository import SalaRepository
from schemas import SalaCreate, SalaUpdate, SalaResponse, SalaListResponse


class SalaService:
    """Servicio de lógica de negocio para Sala"""

    def __init__(self, db: Session):
        self.repository = SalaRepository(db)

    def crear_sala(self, sala_create: SalaCreate) -> SalaResponse:
        """
        Crear una nueva sala
        
        Raises:
            ValueError: Si el nombre ya existe o validación falla
        """
        # Validar que el nombre sea único
        if self.repository.exists_nombre(sala_create.nombre):
            raise ValueError("Sala con este nombre ya existe")

        # Validar capacidad
        if not (1 <= sala_create.capacidad <= 500):
            raise ValueError("capacidad debe ser entre 1 y 500")

        # Crear la sala
        nueva_sala = Sala(
            nombre=sala_create.nombre,
            capacidad=sala_create.capacidad,
            ubicacion=sala_create.ubicacion,
            descripcion=sala_create.descripcion or "",
            tiene_proyector=sala_create.tiene_proyector,
            tiene_videoconferencia=sala_create.tiene_videoconferencia,
            activa=True
        )

        sala_guardada = self.repository.create(nueva_sala)
        return SalaResponse.model_validate(sala_guardada)

    def obtener_sala(self, sala_id: int) -> Optional[SalaResponse]:
        """Obtener una sala por ID"""
        sala = self.repository.get_by_id(sala_id)
        
        if not sala:
            return None
        
        if not sala.activa:
            return None
            
        return SalaResponse.model_validate(sala)

    def obtener_todas_salas(self, skip: int = 0, limit: int = 10) -> SalaListResponse:
        """Obtener todas las salas activas con paginación"""
        if skip < 0 or limit < 1:
            raise ValueError("skip debe ser >= 0 y limit debe ser >= 1")
        
        if limit > 100:
            limit = 100  # Máximo 100 items por página

        salas, total = self.repository.get_all(skip=skip, limit=limit, only_active=True)
        
        items = [SalaResponse.model_validate(sala) for sala in salas]
        
        return SalaListResponse(
            total=total,
            skip=skip,
            limit=limit,
            items=items
        )

    def actualizar_sala(self, sala_id: int, sala_update: SalaUpdate) -> Optional[SalaResponse]:
        """
        Actualizar una sala existente
        
        Raises:
            ValueError: Si validación falla (nombre duplicado, capacidad inválida)
        """
        sala = self.repository.get_by_id(sala_id)
        
        if not sala:
            return None

        # Validar nombre único si se proporciona
        if sala_update.nombre is not None and sala_update.nombre != sala.nombre:
            if self.repository.exists_nombre(sala_update.nombre, exclude_id=sala_id):
                raise ValueError("Sala con este nombre ya existe")
        
        # Validar capacidad si se proporciona
        if sala_update.capacidad is not None:
            if not (1 <= sala_update.capacidad <= 500):
                raise ValueError("capacidad debe ser entre 1 y 500")

        # Actualizar campos
        update_data = sala_update.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if value is not None or field in update_data:
                setattr(sala, field, value)

        sala_actualizada = self.repository.update(sala)
        return SalaResponse.model_validate(sala_actualizada)

    def eliminar_sala(self, sala_id: int) -> bool:
        """
        Eliminar una sala (soft delete)
        
        Returns:
            True si se eliminó correctamente, False si no existe
        """
        sala = self.repository.get_by_id(sala_id)
        
        if not sala:
            return False

        self.repository.delete(sala)
        return True
