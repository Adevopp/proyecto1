"""
Modelos SQLAlchemy para la entidad Sala
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Sala(Base):
    """Modelo de base de datos para Sala de reuniones"""
    __tablename__ = "salas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), unique=True, nullable=False, index=True)
    capacidad = Column(Integer, nullable=False)
    ubicacion = Column(String(200), nullable=False)
    descripcion = Column(String(500), nullable=True, default="")
    tiene_proyector = Column(Boolean, default=False)
    tiene_videoconferencia = Column(Boolean, default=False)
    activa = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_actualizacion = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    def __repr__(self):
        return f"<Sala(id={self.id}, nombre='{self.nombre}', capacidad={self.capacidad})>"
