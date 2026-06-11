"""
Tests pytest para los endpoints de Sala
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from database import get_db, init_db
from models import Base

# Configurar base de datos de prueba
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="function")
def setup_database():
    """Crear y limpiar base de datos para cada test"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestObtenerSalas:
    """Tests para GET /api/salas"""

    def test_obtener_salas_vacio(self, setup_database):
        """Debe retornar lista vacía cuando no hay salas"""
        response = client.get("/api/salas")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []
        assert data["skip"] == 0
        assert data["limit"] == 10

    def test_obtener_salas_con_paginacion(self, setup_database):
        """Debe retornar salas con paginación correcta"""
        # Crear 15 salas
        for i in range(1, 16):
            client.post("/api/salas", json={
                "nombre": f"Sala {i}",
                "capacidad": 10,
                "ubicacion": f"Piso {i % 3}"
            })

        # Obtener primera página
        response = client.get("/api/salas?skip=0&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 15
        assert len(data["items"]) == 10

        # Obtener segunda página
        response = client.get("/api/salas?skip=10&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5

    def test_obtener_salas_validacion_parametros(self, setup_database):
        """Debe validar parámetros de query"""
        response = client.get("/api/salas?skip=-1")
        assert response.status_code == 422

        response = client.get("/api/salas?limit=0")
        assert response.status_code == 422

        response = client.get("/api/salas?limit=101")
        assert response.status_code == 422


class TestObtenerSalaPorId:
    """Tests para GET /api/salas/{id}"""

    def test_obtener_sala_existente(self, setup_database):
        """Debe obtener una sala por ID"""
        # Crear sala
        create_response = client.post("/api/salas", json={
            "nombre": "Sala A",
            "capacidad": 10,
            "ubicacion": "Piso 1"
        })
        sala_id = create_response.json()["id"]

        # Obtener sala
        response = client.get(f"/api/salas/{sala_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sala_id
        assert data["nombre"] == "Sala A"
        assert data["capacidad"] == 10
        assert data["ubicacion"] == "Piso 1"

    def test_obtener_sala_no_existente(self, setup_database):
        """Debe retornar 404 para sala no existente"""
        response = client.get("/api/salas/999")
        assert response.status_code == 404
        assert "no encontrada" in response.json()["detail"].lower()

    def test_obtener_sala_eliminada(self, setup_database):
        """Debe retornar 404 para sala inactiva"""
        # Crear sala
        create_response = client.post("/api/salas", json={
            "nombre": "Sala A",
            "capacidad": 10,
            "ubicacion": "Piso 1"
        })
        sala_id = create_response.json()["id"]

        # Eliminar sala
        client.delete(f"/api/salas/{sala_id}")

        # Intentar obtener sala eliminada
        response = client.get(f"/api/salas/{sala_id}")
        assert response.status_code == 404


class TestCrearSala:
    """Tests para POST /api/salas"""

    def test_crear_sala_valida(self, setup_database):
        """Debe crear una sala válida con código 201"""
        response = client.post("/api/salas", json={
            "nombre": "Sala A",
            "capacidad": 10,
            "ubicacion": "Piso 1"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None
        assert data["nombre"] == "Sala A"
        assert data["capacidad"] == 10
        assert data["ubicacion"] == "Piso 1"
        assert data["activa"] is True
        assert "fecha_creacion" in data
        assert "fecha_actualizacion" in data

    def test_crear_sala_con_todos_campos(self, setup_database):
        """Debe crear sala con todos los campos"""
        response = client.post("/api/salas", json={
            "nombre": "Sala Premium",
            "capacidad": 50,
            "ubicacion": "Piso 5",
            "descripcion": "Sala de conferencias con equipos modernos",
            "tiene_proyector": True,
            "tiene_videoconferencia": True
        })
        assert response.status_code == 201
        data = response.json()
        assert data["tiene_proyector"] is True
        assert data["tiene_videoconferencia"] is True
        assert data["descripcion"] == "Sala de conferencias con equipos modernos"

    def test_crear_sala_capacidad_cero(self, setup_database):
        """No debe permitir capacidad 0"""
        response = client.post("/api/salas", json={
            "nombre": "Sala A",
            "capacidad": 0,
            "ubicacion": "Piso 1"
        })
        assert response.status_code == 400
        assert "capacidad debe ser entre 1 y 500" in response.json()["detail"]

    def test_crear_sala_capacidad_negativa(self, setup_database):
        """No debe permitir capacidad negativa"""
        response = client.post("/api/salas", json={
            "nombre": "Sala A",
            "capacidad": -5,
            "ubicacion": "Piso 1"
        })
        assert response.status_code == 400

    def test_crear_sala_capacidad_mayor_500(self, setup_database):
        """No debe permitir capacidad mayor a 500"""
        response = client.post("/api/salas", json={
            "nombre": "Sala A",
            "capacidad": 501,
            "ubicacion": "Piso 1"
        })
        assert response.status_code == 400
        assert "capacidad debe ser entre 1 y 500" in response.json()["detail"]

    def test_crear_sala_nombre_duplicado(self, setup_database):
        """No debe permitir nombres duplicados - retorna 409"""
        # Crear primera sala
        client.post("/api/salas", json={
            "nombre": "Sala A",
            "capacidad": 10,
            "ubicacion": "Piso 1"
        })

        # Intentar crear sala con mismo nombre
        response = client.post("/api/salas", json={
            "nombre": "Sala A",
            "capacidad": 20,
            "ubicacion": "Piso 2"
        })
        assert response.status_code == 409
        assert "nombre ya existe" in response.json()["detail"].lower()

    def test_crear_sala_nombre_vacio(self, setup_database):
        """No debe permitir nombre vacío"""
        response = client.post("/api/salas", json={
            "nombre": "",
            "capacidad": 10,
            "ubicacion": "Piso 1"
        })
        assert response.status_code == 422

    def test_crear_sala_nombre_muy_largo(self, setup_database):
        """No debe permitir nombre mayor a 100 caracteres"""
        response = client.post("/api/salas", json={
            "nombre": "A" * 101,
            "capacidad": 10,
            "ubicacion": "Piso 1"
        })
        assert response.status_code == 422

    def test_crear_sala_ubicacion_requerida(self, setup_database):
        """Ubicación es requerida"""
        response = client.post("/api/salas", json={
            "nombre": "Sala A",
            "capacidad": 10
        })
        assert response.status_code == 422

    def test_crear_sala_descripcion_opcional(self, setup_database):
        """Descripción es opcional"""
        response = client.post("/api/salas", json={
            "nombre": "Sala A",
            "capacidad": 10,
            "ubicacion": "Piso 1"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["descripcion"] == ""

    def test_crear_sala_campos_opcionales_default(self, setup_database):
        """Los campos opcionales deben tener valores por defecto"""
        response = client.post("/api/salas", json={
            "nombre": "Sala A",
            "capacidad": 10,
            "ubicacion": "Piso 1"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["tiene_proyector"] is False
        assert data["tiene_videoconferencia"] is False
        assert data["activa"] is True


class TestActualizarSala:
    """Tests para PUT /api/salas/{id}"""

    def test_actualizar_sala_nombre(self, setup_database):
        """Debe actualizar el nombre de una sala"""
        # Crear sala
        create_response = client.post("/api/salas", json={
            "nombre": "Sala A",
            "capacidad": 10,
            "ubicacion": "Piso 1"
        })
        sala_id = create_response.json()["id"]

        # Actualizar nombre
        response = client.put(f"/api/salas/{sala_id}", json={
            "nombre": "Sala A Actualizada"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["nombre"] == "Sala A Actualizada"
        assert data["capacidad"] == 10  # Otros campos se mantienen

    def test_actualizar_sala_capacidad(self, setup_database):
        """Debe actualizar la capacidad de una sala"""
        # Crear sala
        create_response = client.post("/api/salas", json={
            "nombre": "Sala A",
            "capacidad": 10,
            "ubicacion": "Piso 1"
        })
        sala_id = create_response.json()["id"]

        # Actualizar capacidad
        response = client.put(f"/api/salas/{sala_id}", json={
            "capacidad": 50
        })
        assert response.status_code == 200
        data = response.json()
        assert data["capacidad"] == 50

    def test_actualizar_sala_multiples_campos(self, setup_database):
        """Debe actualizar múltiples campos"""
        # Crear sala
        create_response = client.post("/api/salas", json={
            "nombre": "Sala A",
            "capacidad": 10,
            "ubicacion": "Piso 1",
            "tiene_proyector": False
        })
        sala_id = create_response.json()["id"]

        # Actualizar múltiples campos
        response = client.put(f"/api/salas/{sala_id}", json={
            "nombre": "Sala A Premium",
            "capacidad": 30,
            "tiene_proyector": True,
            "tiene_videoconferencia": True
        })
        assert response.status_code == 200
        data = response.json()
        assert data["nombre"] == "Sala A Premium"
        assert data["capacidad"] == 30
        assert data["tiene_proyector"] is True
        assert data["tiene_videoconferencia"] is True

    def test_actualizar_sala_nombre_duplicado(self, setup_database):
        """No debe permitir cambiar a un nombre que ya existe"""
        # Crear dos salas
        resp1 = client.post("/api/salas", json={
            "nombre": "Sala A",
            "capacidad": 10,
            "ubicacion": "Piso 1"
        })
        sala_id_1 = resp1.json()["id"]

        client.post("/api/salas", json={
            "nombre": "Sala B",
            "capacidad": 20,
            "ubicacion": "Piso 2"
        })

        # Intentar cambiar nombre de Sala A a Sala B
        response = client.put(f"/api/salas/{sala_id_1}", json={
            "nombre": "Sala B"
        })
        assert response.status_code == 409
        assert "nombre ya existe" in response.json()["detail"].lower()

    def test_actualizar_sala_capacidad_invalida(self, setup_database):
        """No debe permitir capacidad inválida"""
        # Crear sala
        create_response = client.post("/api/salas", json={
            "nombre": "Sala A",
            "capacidad": 10,
            "ubicacion": "Piso 1"
        })
        sala_id = create_response.json()["id"]

        # Intentar actualizar con capacidad 0
        response = client.put(f"/api/salas/{sala_id}", json={
            "capacidad": 0
        })
        assert response.status_code == 400
        assert "capacidad debe ser entre 1 y 500" in response.json()["detail"]

        # Intentar actualizar con capacidad > 500
        response = client.put(f"/api/salas/{sala_id}", json={
            "capacidad": 501
        })
        assert response.status_code == 400

    def test_actualizar_sala_no_existente(self, setup_database):
        """Debe retornar 404 para sala no existente"""
        response = client.put("/api/salas/999", json={
            "nombre": "Nueva Sala"
        })
        assert response.status_code == 404

    def test_actualizar_sala_activa_flag(self, setup_database):
        """Debe permitir actualizar el flag activa"""
        # Crear sala
        create_response = client.post("/api/salas", json={
            "nombre": "Sala A",
            "capacidad": 10,
            "ubicacion": "Piso 1"
        })
        sala_id = create_response.json()["id"]

        # Desactivar
        response = client.put(f"/api/salas/{sala_id}", json={
            "activa": False
        })
        assert response.status_code == 200
        data = response.json()
        assert data["activa"] is False

    def test_actualizar_sala_sin_cambios(self, setup_database):
        """Debe permitir actualizar sin proporcionar cambios"""
        # Crear sala
        create_response = client.post("/api/salas", json={
            "nombre": "Sala A",
            "capacidad": 10,
            "ubicacion": "Piso 1"
        })
        sala_id = create_response.json()["id"]

        # Actualizar sin cambios
        response = client.put(f"/api/salas/{sala_id}", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sala_id


class TestEliminarSala:
    """Tests para DELETE /api/salas/{id}"""

    def test_eliminar_sala_exitoso(self, setup_database):
        """Debe eliminar (soft delete) una sala con código 204"""
        # Crear sala
        create_response = client.post("/api/salas", json={
            "nombre": "Sala A",
            "capacidad": 10,
            "ubicacion": "Piso 1"
        })
        sala_id = create_response.json()["id"]

        # Eliminar sala
        response = client.delete(f"/api/salas/{sala_id}")
        assert response.status_code == 204
        assert response.content == b""

    def test_eliminar_sala_marca_inactiva(self, setup_database):
        """Eliminación debe marcar como inactiva en lugar de eliminar registro"""
        # Crear sala
        create_response = client.post("/api/salas", json={
            "nombre": "Sala A",
            "capacidad": 10,
            "ubicacion": "Piso 1"
        })
        sala_id = create_response.json()["id"]

        # Eliminar sala
        client.delete(f"/api/salas/{sala_id}")

        # Intentar obtener sala eliminada
        response = client.get(f"/api/salas/{sala_id}")
        assert response.status_code == 404

    def test_eliminar_sala_no_existente(self, setup_database):
        """Debe retornar 404 para sala no existente"""
        response = client.delete("/api/salas/999")
        assert response.status_code == 404

    def test_no_listar_salas_eliminadas(self, setup_database):
        """Salas eliminadas no deben aparecer en listado"""
        # Crear dos salas
        resp1 = client.post("/api/salas", json={
            "nombre": "Sala A",
            "capacidad": 10,
            "ubicacion": "Piso 1"
        })
        sala_id_1 = resp1.json()["id"]

        client.post("/api/salas", json={
            "nombre": "Sala B",
            "capacidad": 20,
            "ubicacion": "Piso 2"
        })

        # Listar antes de eliminar
        response = client.get("/api/salas")
        assert response.json()["total"] == 2

        # Eliminar una sala
        client.delete(f"/api/salas/{sala_id_1}")

        # Listar después de eliminar
        response = client.get("/api/salas")
        assert response.json()["total"] == 1
        assert response.json()["items"][0]["nombre"] == "Sala B"


class TestIntegracion:
    """Tests de integración - escenarios completos"""

    def test_ciclo_completo_crud(self, setup_database):
        """Test de ciclo completo: crear, leer, actualizar, eliminar"""
        # CREATE
        create_response = client.post("/api/salas", json={
            "nombre": "Sala de Reuniones",
            "capacidad": 15,
            "ubicacion": "Piso 3",
            "descripcion": "Sala principal",
            "tiene_proyector": True
        })
        assert create_response.status_code == 201
        sala_id = create_response.json()["id"]

        # READ
        read_response = client.get(f"/api/salas/{sala_id}")
        assert read_response.status_code == 200
        sala = read_response.json()
        assert sala["nombre"] == "Sala de Reuniones"
        assert sala["tiene_proyector"] is True

        # UPDATE
        update_response = client.put(f"/api/salas/{sala_id}", json={
            "capacidad": 25,
            "tiene_videoconferencia": True
        })
        assert update_response.status_code == 200
        updated_sala = update_response.json()
        assert updated_sala["capacidad"] == 25
        assert updated_sala["tiene_videoconferencia"] is True

        # DELETE
        delete_response = client.delete(f"/api/salas/{sala_id}")
        assert delete_response.status_code == 204

        # Verificar que está eliminada
        final_read = client.get(f"/api/salas/{sala_id}")
        assert final_read.status_code == 404

    def test_multiples_salas_simultaneas(self, setup_database):
        """Test con múltiples salas simultáneamente"""
        salas_ids = []

        # Crear 5 salas
        for i in range(1, 6):
            response = client.post("/api/salas", json={
                "nombre": f"Sala {i}",
                "capacidad": i * 10,
                "ubicacion": f"Piso {i}"
            })
            assert response.status_code == 201
            salas_ids.append(response.json()["id"])

        # Listar todas
        list_response = client.get("/api/salas?limit=10")
        assert list_response.json()["total"] == 5

        # Actualizar algunas
        for sala_id in salas_ids[::2]:  # Actualizar cada 2da sala
            response = client.put(f"/api/salas/{sala_id}", json={
                "tiene_proyector": True
            })
            assert response.status_code == 200

        # Eliminar una
        client.delete(f"/api/salas/{salas_ids[0]}")

        # Verificar estado final
        list_response = client.get("/api/salas?limit=10")
        assert list_response.json()["total"] == 4
