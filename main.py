"""
Aplicación FastAPI principal
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from database import init_db
from routes import router as salas_router

# Inicializar base de datos
init_db()

# Crear aplicación
app = FastAPI(
    title="API de Salas de Reuniones",
    description="CRUD API para gestionar salas de reuniones",
    version="1.0.0"
)

# Incluir routers
app.include_router(salas_router)


@app.get("/", tags=["health"])
def root():
    """Endpoint de bienvenida"""
    return {
        "mensaje": "Bienvenido a la API de Salas de Reuniones",
        "documentacion": "/docs",
        "swagger": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["health"])
def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


# Manejador global de excepciones
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Manejador global de excepciones"""
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
