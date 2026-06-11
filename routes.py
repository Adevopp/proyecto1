"""
Routes/Endpoints FastAPI para Sala
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from schemas import SalaCreate, SalaUpdate, SalaResponse, SalaListResponse
from service import SalaService

router = APIRouter(prefix="/api/salas", tags=["salas"])


@router.get("", response_model=SalaListResponse, status_code=200)
def obtener_salas(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(10, ge=1, le=100, description="Límite de registros"),
    db: Session = Depends(get_db)
):
    """
    Obtener todas las salas activas
    
    - **skip**: número de salas a omitir (default: 0)
    - **limit**: número máximo de salas a retornar (default: 10, máximo: 100)
    """
    try:
        service = SalaService(db)
        return service.obtener_todas_salas(skip=skip, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{sala_id}", response_model=SalaResponse, status_code=200)
def obtener_sala(
    sala_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtener una sala específica por su ID
    
    - **sala_id**: ID de la sala
    """
    service = SalaService(db)
    sala = service.obtener_sala(sala_id)
    
    if not sala:
        raise HTTPException(status_code=404, detail="Sala no encontrada")
    
    return sala


@router.post("", response_model=SalaResponse, status_code=201)
def crear_sala(
    sala_create: SalaCreate,
    db: Session = Depends(get_db)
):
    """
    Crear una nueva sala de reuniones
    
    - **nombre**: Nombre único de la sala (máximo 100 caracteres)
    - **capacidad**: Capacidad de personas (entre 1 y 500)
    - **ubicacion**: Ubicación de la sala (máximo 200 caracteres)
    - **descripcion**: Descripción opcional (máximo 500 caracteres)
    - **tiene_proyector**: ¿Tiene proyector? (default: False)
    - **tiene_videoconferencia**: ¿Tiene videoconferencia? (default: False)
    """
    try:
        service = SalaService(db)
        return service.crear_sala(sala_create)
    except ValueError as e:
        error_msg = str(e)
        if "nombre ya existe" in error_msg:
            raise HTTPException(status_code=409, detail=error_msg)
        raise HTTPException(status_code=400, detail=error_msg)


@router.put("/{sala_id}", response_model=SalaResponse, status_code=200)
def actualizar_sala(
    sala_id: int,
    sala_update: SalaUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualizar una sala existente
    
    - **sala_id**: ID de la sala a actualizar
    - Todos los campos son opcionales, solo se actualizan los proporcionados
    """
    try:
        service = SalaService(db)
        sala = service.actualizar_sala(sala_id, sala_update)
        
        if not sala:
            raise HTTPException(status_code=404, detail="Sala no encontrada")
        
        return sala
    except ValueError as e:
        error_msg = str(e)
        if "nombre ya existe" in error_msg:
            raise HTTPException(status_code=409, detail=error_msg)
        raise HTTPException(status_code=400, detail=error_msg)


@router.delete("/{sala_id}", status_code=204)
def eliminar_sala(
    sala_id: int,
    db: Session = Depends(get_db)
):
    """
    Eliminar una sala (soft delete - marca como inactiva)
    
    - **sala_id**: ID de la sala a eliminar
    """
    service = SalaService(db)
    success = service.eliminar_sala(sala_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Sala no encontrada")
    
    return None
