# API de Salas de Reuniones

Una API REST completa para gestionar salas de reuniones, construida con FastAPI y SQLAlchemy.

## Características

- ✅ CRUD completo de salas de reuniones
- ✅ Validación de datos con Pydantic
- ✅ Base de datos SQLite con SQLAlchemy ORM
- ✅ Paginación en listados
- ✅ Soft delete (marcar como inactiva)
- ✅ Tests completos con pytest
- ✅ Documentación automática con Swagger

## Requisitos

- Python 3.9+
- pip

## Instalación

1. Clonar el repositorio:
```bash
git clone <repository-url>
cd salas-reuniones-api
```

2. Crear entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

## Ejecutar la aplicación

```bash
python main.py
```

La aplicación estará disponible en `http://localhost:8000`

### Documentación interactiva

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Estructura del proyecto

```
├── models.py           # Modelos SQLAlchemy
├── schemas.py          # Schemas Pydantic
├── database.py         # Configuración de BD
├── repository.py       # Capa de acceso a datos
├── service.py          # Lógica de negocio
├── routes.py           # Endpoints FastAPI
├── main.py             # Aplicación principal
├── test_salas.py       # Tests pytest
├── requirements.txt    # Dependencias
└── README.md           # Este archivo
```

## Endpoints

### GET /api/salas
Obtener todas las salas activas con paginación.

**Parámetros query:**
- `skip`: número de registros a omitir (default: 0)
- `limit`: número máximo de registros (default: 10, máximo: 100)

**Respuesta 200:**
```json
{
  "total": 5,
  "skip": 0,
  "limit": 10,
  "items": [
    {
      "id": 1,
      "nombre": "Sala A",
      "capacidad": 10,
      "ubicacion": "Piso 1",
      "descripcion": "Sala de reuniones",
      "tiene_proyector": true,
      "tiene_videoconferencia": false,
      "activa": true,
      "fecha_creacion": "2024-01-15T10:30:00",
      "fecha_actualizacion": "2024-01-15T10:30:00"
    }
  ]
}
```

### GET /api/salas/{id}
Obtener una sala específica por ID.

**Parámetro path:**
- `id`: ID de la sala

**Respuesta 200:**
```json
{
  "id": 1,
  "nombre": "Sala A",
  "capacidad": 10,
  "ubicacion": "Piso 1",
  "descripcion": "Sala de reuniones",
  "tiene_proyector": true,
  "tiene_videoconferencia": false,
  "activa": true,
  "fecha_creacion": "2024-01-15T10:30:00",
  "fecha_actualizacion": "2024-01-15T10:30:00"
}
```

**Respuesta 404:**
```json
{
  "detail": "Sala no encontrada"
}
```

### POST /api/salas
Crear una nueva sala de reuniones.

**Body (requerido):**
```json
{
  "nombre": "Sala A",
  "capacidad": 10,
  "ubicacion": "Piso 1",
  "descripcion": "Descripción opcional",
  "tiene_proyector": true,
  "tiene_videoconferencia": false
}
```

**Respuesta 201:**
```json
{
  "id": 1,
  "nombre": "Sala A",
  "capacidad": 10,
  "ubicacion": "Piso 1",
  "descripcion": "Descripción opcional",
  "tiene_proyector": true,
  "tiene_videoconferencia": false,
  "activa": true,
  "fecha_creacion": "2024-01-15T10:30:00",
  "fecha_actualizacion": "2024-01-15T10:30:00"
}
```

**Respuesta 400 (Validación):**
```json
{
  "detail": "capacidad debe ser entre 1 y 500"
}
```

**Respuesta 409 (Conflicto - nombre duplicado):**
```json
{
  "detail": "Sala con este nombre ya existe"
}
```

### PUT /api/salas/{id}
Actualizar una sala existente.

**Parámetro path:**
- `id`: ID de la sala

**Body (todos los campos opcionales):**
```json
{
  "nombre": "Sala A Actualizada",
  "capacidad": 20,
  "ubicacion": "Piso 2",
  "descripcion": "Nueva descripción",
  "tiene_proyector": true,
  "tiene_videoconferencia": true,
  "activa": true
}
```

**Respuesta 200:**
```json
{
  "id": 1,
  "nombre": "Sala A Actualizada",
  "capacidad": 20,
  "ubicacion": "Piso 2",
  "descripcion": "Nueva descripción",
  "tiene_proyector": true,
  "tiene_videoconferencia": true,
  "activa": true,
  "fecha_creacion": "2024-01-15T10:30:00",
  "fecha_actualizacion": "2024-01-15T11:00:00"
}
```

**Respuesta 404:**
```json
{
  "detail": "Sala no encontrada"
}
```

### DELETE /api/salas/{id}
Eliminar una sala (soft delete - marca como inactiva).

**Parámetro path:**
- `id`: ID de la sala

**Respuesta 204:**
Sin contenido

**Respuesta 404:**
```json
{
  "detail": "Sala no encontrada"
}
```

## Validaciones

### Campo: nombre
- Mínimo: 1 carácter
- Máximo: 100 caracteres
- Requerido: Sí
- Único: Sí (no puede haber dos salas con el mismo nombre)

### Campo: capacidad
- Mínimo: 1 persona
- Máximo: 500 personas
- Requerido: Sí
- Tipo: Entero

### Campo: ubicacion
- Mínimo: 1 carácter
- Máximo: 200 caracteres
- Requerido: Sí

### Campo: descripcion
- Máximo: 500 caracteres
- Requerido: No
- Tipo: Texto

### Campo: tiene_proyector
- Requerido: No
- Default: False

### Campo: tiene_videoconferencia
- Requerido: No
- Default: False

### Campo: activa
- Requerido: No
- Default: True

## Ejecución de Tests

Ejecutar todos los tests:
```bash
pytest test_salas.py -v
```

Ejecutar con cobertura:
```bash
pytest test_salas.py --cov=. --cov-report=html
```

Ejecutar tests específicos:
```bash
pytest test_salas.py::TestCrearSala -v
pytest test_salas.py::TestCrearSala::test_crear_sala_valida -v
```

## Cobertura de Tests

Los tests cubren:
- ✅ Crear salas válidas
- ✅ Validación de capacidad (0, negativa, > 500)
- ✅ Validación de nombres únicos
- ✅ Validación de campos requeridos
- ✅ Obtener salas (listado y por ID)
- ✅ Paginación
- ✅ Actualizar salas (uno o múltiples campos)
- ✅ Soft delete (marcar como inactiva)
- ✅ Salas eliminadas no aparecen en listados
- ✅ Escenarios de integración completa

**Total de tests:** 40+

## Ejemplos de uso

### Crear una sala
```bash
curl -X POST "http://localhost:8000/api/salas" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Sala de Conferencias",
    "capacidad": 50,
    "ubicacion": "Piso 5",
    "descripcion": "Sala premium con equipos modernos",
    "tiene_proyector": true,
    "tiene_videoconferencia": true
  }'
```

### Obtener todas las salas
```bash
curl "http://localhost:8000/api/salas?skip=0&limit=10"
```

### Obtener una sala por ID
```bash
curl "http://localhost:8000/api/salas/1"
```

### Actualizar una sala
```bash
curl -X PUT "http://localhost:8000/api/salas/1" \
  -H "Content-Type: application/json" \
  -d '{
    "capacidad": 75,
    "tiene_proyector": true
  }'
```

### Eliminar una sala
```bash
curl -X DELETE "http://localhost:8000/api/salas/1"
```

## Patrón Arquitectónico

La aplicación sigue el patrón **Repository-Service**:

1. **Models** (`models.py`): Definición del modelo de datos con SQLAlchemy
2. **Schemas** (`schemas.py`): Validación y serialización con Pydantic
3. **Repository** (`repository.py`): Capa de acceso a datos (CRUD)
4. **Service** (`service.py`): Lógica de negocio y validaciones
5. **Routes** (`routes.py`): Endpoints y manejo de peticiones HTTP
6. **Database** (`database.py`): Configuración de conexión
7. **Main** (`main.py`): Aplicación FastAPI

## Características de seguridad

- ✅ Validación de entrada con Pydantic
- ✅ Restricción de campos requeridos y opcionales
- ✅ Validación de rangos y longitudes
- ✅ Soft delete para preservar datos históricos
- ✅ Manejo de excepciones y errores

## Notas de desarrollo

- La base de datos SQLite se crea automáticamente en `salas.db`
- Los tests usan una base de datos separada `test.db`
- Los timestamps se generan y actualizan automáticamente
- El soft delete no elimina registros, solo los marca como inactivos

## Licencia

MIT
