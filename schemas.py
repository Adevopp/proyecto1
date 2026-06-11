"""
Schemas Pydantic para validación y serialización de Sala
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator


class SalaBase(BaseModel):
    """Schema base con campos comunes"""
    nombre: str = Field(..., min_length=1, max_length=100, description="Nombre de la sala")
    capacidad: int = Field(..., ge=1, le=500, description="Capacidad de personas")
    ubicacion: str = Field(..., min_length=1, max_length=200, description="Ubicación de la sala")
    descripcion: Optional[str] = Field(None, max_length=500, description="Descripción opcional")
    tiene_proyector: bool = Field(default=False, description="¿Tiene proyector?")
    tiene_videoconferencia: bool = Field(default=False, description="¿Tiene videoconferencia?")

    @validator("nombre")
    def nombre_no_vacio(cls, v):
        if not v.strip():
            raise ValueError("El nombre no puede estar vacío")
        return v.strip()

    @validator("descripcion")
    def descripcion_no_vacio(cls, v):
        if v is not None and not v.strip():
            return None
        return v


class SalaCreate(SalaBase):
    """Schema para crear una sala"""
    pass


class SalaUpdate(BaseModel):
    """Schema para actualizar una sala"""
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    capacidad: Optional[int] = Field(None, ge=1, le=500)
    ubicacion: Optional[str] = Field(None, min_length=1, max_length=200)
    descripcion: Optional[str] = Field(None, max_length=500)
    tiene_proyector: Optional[bool] = None
    tiene_videoconferencia: Optional[bool] = None
    activa: Optional[bool] = None

    @validator("nombre")
    def nombre_no_vacio(cls, v):
        if v is not None and not v.strip():
            raise ValueError("El nombre no puede estar vacío")
        return v.strip() if v else None


class SalaResponse(SalaBase):
    """Schema para respuestas de API"""
    id: int
    activa: bool
    fecha_creacion: datetime
    fecha_actualizacion: datetime

    class Config:
        from_attributes = True


class SalaListResponse(BaseModel):
    """Schema para respuesta de listado"""
    total: int
    skip: int
    limit: int
    items: list[SalaResponse]
