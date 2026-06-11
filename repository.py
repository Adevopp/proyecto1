"""
Repository para la entidad Sala - Capa de acceso a datos
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from models import Sala


class SalaRepository:
    """Repositorio para operaciones CRUD de Sala"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, sala: Sala) -> Sala:
        """Crear una nueva sala"""
        self.db.add(sala)
        self.db.commit()
        self.db.refresh(sala)
        return sala

    def get_by_id(self, sala_id: int) -> Optional[Sala]:
        """Obtener sala por ID"""
        return self.db.query(Sala).filter(Sala.id == sala_id).first()

    def get_by_nombre(self, nombre: str) -> Optional[Sala]:
        """Obtener sala por nombre (exacto)"""
        return self.db.query(Sala).filter(Sala.nombre == nombre).first()

    def get_all(self, skip: int = 0, limit: int = 10, only_active: bool = True) -> tuple[List[Sala], int]:
        """Obtener todas las salas con paginación"""
        query = self.db.query(Sala)
        
        if only_active:
            query = query.filter(Sala.activa == True)
        
        total = query.count()
        salas = query.offset(skip).limit(limit).all()
        
        return salas, total

    def update(self, sala: Sala) -> Sala:
        """Actualizar una sala existente"""
        self.db.commit()
        self.db.refresh(sala)
        return sala

    def delete(self, sala: Sala) -> bool:
        """Soft delete: marcar como inactiva"""
        sala.activa = False
        self.db.commit()
        self.db.refresh(sala)
        return True

    def exists_nombre(self, nombre: str, exclude_id: Optional[int] = None) -> bool:
        """Verificar si existe una sala con ese nombre"""
        query = self.db.query(Sala).filter(Sala.nombre == nombre)
        
        if exclude_id:
            query = query.filter(Sala.id != exclude_id)
        
        return query.first() is not None
