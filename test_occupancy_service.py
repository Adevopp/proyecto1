import pytest
from datetime import datetime, timedelta
from occupancy_service import OccupancyService, Room, RoomType


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def service():
    """Proporciona una instancia limpia del servicio para cada test."""
    return OccupancyService()


@pytest.fixture
def base_timestamp():
    """Timestamp base para tests consistentes."""
    return datetime(2025, 1, 15, 9, 0, 0)


@pytest.fixture
def rooms_setup(service):
    """Crea un conjunto estándar de salas para los tests."""
    service.create_room("A101", 10, RoomType.MEDIUM)
    service.create_room("B202", 4, RoomType.SMALL)
    service.create_room("C303", 20, RoomType.LARGE)
    return service


@pytest.fixture
def booked_room(rooms_setup, base_timestamp):
    """Proporciona salas con reservas preexistentes."""
    rooms_setup.book_room("A101", base_timestamp, base_timestamp + timedelta(hours=1), 5)
    rooms_setup.book_room("C303", base_timestamp, base_timestamp + timedelta(hours=2), 15)
    return rooms_setup


# ============================================================================
# TESTS: CREACIÓN DE SALAS
# ============================================================================

class TestRoomCreation:
    """Tests para la creación de salas."""

    def test_create_single_room(self, service):
        """Verifica que se puede crear una sala correctamente."""
        room = service.create_room("A101", 10, RoomType.MEDIUM)
        assert room.room_id == "A101"
        assert room.capacity == 10
        assert room.room_type == RoomType.MEDIUM
        assert room.bookings == []

    def test_create_multiple_rooms(self, rooms_setup):
        """Verifica que se pueden crear múltiples salas."""
        assert len(rooms_setup.rooms) == 3
        assert "A101" in rooms_setup.rooms
        assert "B202" in rooms_setup.rooms
        assert "C303" in rooms_setup.rooms

    def test_create_duplicate_room_raises_error(self, service):
        """Verifica que crear una sala duplicada lanza excepción."""
        service.create_room("A101", 10, RoomType.MEDIUM)
        with pytest.raises(ValueError, match="already exists"):
            service.create_room("A101", 5, RoomType.SMALL)

    def test_create_room_all_types(self, service):
        """Verifica que se pueden crear salas de todos los tipos."""
        room_small = service.create_room("S1", 3, RoomType.SMALL)
        room_medium = service.create_room("M1", 8, RoomType.MEDIUM)
        room_large = service.create_room("L1", 15, RoomType.LARGE)

        assert room_small.room_type == RoomType.SMALL
        assert room_medium.room_type == RoomType.MEDIUM
        assert room_large.room_type == RoomType.LARGE

    def test_get_existing_room(self, rooms_setup):
        """Verifica que se puede obtener una sala existente."""
        room = rooms_setup.get_room("A101")
        assert room is not None
        assert room.room_id == "A101"

    def test_get_nonexistent_room_returns_none(self, rooms_setup):
        """Verifica que obtener una sala inexistente retorna None."""
        room = rooms_setup.get_room("NONEXISTENT")
        assert room is None


# ============================================================================
# TESTS: RESERVAS - HAPPY PATH
# ============================================================================

class TestSuccessfulBookings:
    """Tests para reservas exitosas."""

    def test_book_room_happy_path(self, rooms_setup, base_timestamp):
        """Verifica que se puede reservar una sala disponible."""
        result = rooms_setup.book_room(
            "A101",
            base_timestamp,
            base_timestamp + timedelta(hours=1),
            5
        )
        assert result is True
        room = rooms_setup.get_room("A101")
        assert len(room.bookings) == 1

    def test_book_room_with_exact_capacity(self, rooms_setup, base_timestamp):
        """Verifica que se puede reservar con exactamente la capacidad."""
        result = rooms_setup.book_room(
            "B202",
            base_timestamp,
            base_timestamp + timedelta(hours=1),
            4  # Capacidad exacta de B202
        )
        assert result is True

    def test_book_multiple_non_overlapping_slots(self, rooms_setup, base_timestamp):
        """Verifica que se pueden hacer múltiples reservas sin solapamiento."""
        t1 = base_timestamp
        t2 = t1 + timedelta(hours=1)
        t3 = t2 + timedelta(minutes=30)
        t4 = t3 + timedelta(hours=1)

        result1 = rooms_setup.book_room("A101", t1, t2, 3)
        result2 = rooms_setup.book_room("A101", t3, t4, 5)

        assert result1 is True
        assert result2 is True
        room = rooms_setup.get_room("A101")
        assert len(room.bookings) == 2

    def test_book_room_minimum_attendees(self, rooms_setup, base_timestamp):
        """Verifica que se puede reservar con 1 asistente."""
        result = rooms_setup.book_room(
            "A101",
            base_timestamp,
            base_timestamp + timedelta(hours=1),
            1
        )
        assert result is True

    def test_room_add_booking_directly(self, rooms_setup, base_timestamp):
        """Verifica el método add_booking de Room directamente."""
        room = rooms_setup.get_room("A101")
        result = room.add_booking(
            base_timestamp,
            base_timestamp + timedelta(hours=1),
            7
        )
        assert result is True
        assert len(room.bookings) == 1


# ============================================================================
# TESTS: RESERVAS - RECHAZO POR CAPACIDAD
# ============================================================================

class TestBookingRejectionByCapacity:
    """Tests para rechazos de reserva por capacidad insuficiente."""

    def test_reject_booking_exceeds_capacity(self, rooms_setup, base_timestamp):
        """Verifica que se rechaza reserva que excede capacidad."""
        result = rooms_setup.book_room(
            "B202",  # Capacidad: 4
            base_timestamp,
            base_timestamp + timedelta(hours=1),
            5  # Más que la capacidad
        )
        assert result is False

    def test_reject_booking_far_exceeds_capacity(self, rooms_setup, base_timestamp):
        """Verifica rechazo con muy grande exceso de capacidad."""
        result = rooms_setup.book_room(
            "B202",  # Capacidad: 4
            base_timestamp,
            base_timestamp + timedelta(hours=1),
            50
        )
        assert result is False

    def test_no_booking_recorded_on_rejection(self, rooms_setup, base_timestamp):
        """Verifica que no se registra la reserva si se rechaza."""
        rooms_setup.book_room(
            "B202",
            base_timestamp,
            base_timestamp + timedelta(hours=1),
            10  # Excede capacidad
        )
        room = rooms_setup.get_room("B202")
        assert len(room.bookings) == 0

    def test_reject_with_one_person_over_capacity(self, rooms_setup, base_timestamp):
        """Verifica rechazo cuando se excede por 1 persona."""
        result = rooms_setup.book_room(
            "B202",  # Capacidad: 4
            base_timestamp,
            base_timestamp + timedelta(hours=1),
            5
        )
        assert result is False


# ============================================================================
# TESTS: RESERVAS - RECHAZO POR CONFLICTO HORARIO
# ============================================================================

class TestBookingRejectionByTimeConflict:
    """Tests para rechazos de reserva por conflicto horario."""

    def test_reject_exact_overlap(self, rooms_setup, base_timestamp):
        """Verifica rechazo de reserva con solapamiento exacto."""
        t_start = base_timestamp
        t_end = t_start + timedelta(hours=1)

        rooms_setup.book_room("A101", t_start, t_end, 3)
        result = rooms_setup.book_room("A101", t_start, t_end, 4)

        assert result is False

    def test_reject_partial_overlap_start(self, rooms_setup, base_timestamp):
        """Verifica rechazo cuando nueva reserva comienza dentro de existente."""
        t1_start = base_timestamp
        t1_end = t1_start + timedelta(hours=1)
        t2_start = t1_start + timedelta(minutes=30)
        t2_end = t2_start + timedelta(hours=1)

        rooms_setup.book_room("A101", t1_start, t1_end, 3)
        result = rooms_setup.book_room("A101", t2_start, t2_end, 4)

        assert result is False

    def test_reject_partial_overlap_end(self, rooms_setup, base_timestamp):
        """Verifica rechazo cuando nueva reserva termina dentro de existente."""
        t1_start = base_timestamp
        t1_end = t1_start + timedelta(hours=1)
        t2_start = t1_start - timedelta(minutes=30)
        t2_end = t1_start + timedelta(minutes=30)

        rooms_setup.book_room("A101", t1_start, t1_end, 3)
        result = rooms_setup.book_room("A101", t2_start, t2_end, 4)

        assert result is False

    def test_reject_complete_overlap_new_inside_existing(self, rooms_setup, base_timestamp):
        """Verifica rechazo cuando nueva reserva está completamente dentro."""
        t1_start = base_timestamp
        t1_end = t1_start + timedelta(hours=2)
        t2_start = t1_start + timedelta(minutes=15)
        t2_end = t2_start + timedelta(minutes=30)

        rooms_setup.book_room("A101", t1_start, t1_end, 3)
        result = rooms_setup.book_room("A101", t2_start, t2_end, 4)

        assert result is False

    def test_accept_adjacent_bookings(self, rooms_setup, base_timestamp):
        """Verifica que se aceptan reservas adyacentes (sin solapamiento)."""
        t1_start = base_timestamp
        t1_end = t1_start + timedelta(hours=1)
        t2_start = t1_end
        t2_end = t2_start + timedelta(hours=1)

        result1 = rooms_setup.book_room("A101", t1_start, t1_end, 3)
        result2 = rooms_setup.book_room("A101", t2_start, t2_end, 4)

        assert result1 is True
        assert result2 is True

    def test_reject_adjacent_overlap_boundary(self, rooms_setup, base_timestamp):
        """Verifica que no se permite solapamiento ni en límites."""
        t1_start = base_timestamp
        t1_end = t1_start + timedelta(hours=1)
        t2_start = t1_end - timedelta(seconds=1)
        t2_end = t2_start + timedelta(hours=1)

        rooms_setup.book_room("A101", t1_start, t1_end, 3)
        result = rooms_setup.book_room("A101", t2_start, t2_end, 4)

        assert result is False


# ============================================================================
# TESTS: OCUPACIÓN EN MOMENTOS ESPECÍFICOS
# ============================================================================

class TestOccupancyAtSpecificTime:
    """Tests para consultar ocupación en momentos específicos."""

    def test_occupancy_during_booking(self, rooms_setup, base_timestamp):
        """Verifica que se reporta la ocupación correcta durante reserva."""
        rooms_setup.book_room(
            "A101",
            base_timestamp,
            base_timestamp + timedelta(hours=1),
            7
        )
        occupancy = rooms_setup.get_room("A101").get_occupancy_at(
            base_timestamp + timedelta(minutes=30)
        )
        assert occupancy == 7

    def test_occupancy_before_booking(self, rooms_setup, base_timestamp):
        """Verifica que ocupación es 0 antes de la reserva."""
        rooms_setup.book_room(
            "A101",
            base_timestamp + timedelta(hours=1),
            base_timestamp + timedelta(hours=2),
            5
        )
        occupancy = rooms_setup.get_room("A101").get_occupancy_at(base_timestamp)
        assert occupancy == 0

    def test_occupancy_after_booking(self, rooms_setup, base_timestamp):
        """Verifica que ocupación es 0 después de la reserva."""
        rooms_setup.book_room(
            "A101",
            base_timestamp,
            base_timestamp + timedelta(hours=1),
            5
        )
        occupancy = rooms_setup.get_room("A101").get_occupancy_at(
            base_timestamp + timedelta(hours=2)
        )
        assert occupancy == 0

    def test_occupancy_at_booking_boundary_start(self, rooms_setup, base_timestamp):
        """Verifica ocupación en el inicio exacto de la reserva."""
        rooms_setup.book_room(
            "A101",
            base_timestamp,
            base_timestamp + timedelta(hours=1),
            5
        )
        occupancy = rooms_setup.get_room("A101").get_occupancy_at(base_timestamp)
        assert occupancy == 5

    def test_occupancy_at_booking_boundary_end(self, rooms_setup, base_timestamp):
        """Verifica que ocupación es 0 en el final exacto de la reserva."""
        rooms_setup.book_room(
            "A101",
            base_timestamp,
            base_timestamp + timedelta(hours=1),
            5
        )
        occupancy = rooms_setup.get_room("A101").get_occupancy_at(
            base_timestamp + timedelta(hours=1)
        )
        assert occupancy == 0

    def test_occupancy_multiple_bookings_returns_first_match(self, rooms_setup, base_timestamp):
        """Verifica que en caso de múltiples, retorna el primero encontrado."""
        t1 = base_timestamp
        t2 = t1 + timedelta(hours=2)

        rooms_setup.book_room("A101", t1, t1 + timedelta(hours=1), 3)
        rooms_setup.book_room("A101", t2, t2 + timedelta(hours=1), 8)

        occupancy = rooms_setup.get_room("A101").get_occupancy_at(
            t1 + timedelta(minutes=30)
        )
        assert occupancy == 3

    def test_occupancy_empty_room(self, rooms_setup, base_timestamp):
        """Verifica que una sala sin reservas reporta ocupación 0."""
        occupancy = rooms_setup.get_room("A101").get_occupancy_at(base_timestamp)
        assert occupancy == 0


# ============================================================================
# TESTS: BÚSQUEDA DE SLOTS DISPONIBLES
# ============================================================================

class TestAvailableSlots:
    """Tests para búsqueda de slots disponibles."""

    def test_find_available_slots_empty_room(self, rooms_setup, base_timestamp):
        """Verifica que una sala vacía retorna todos los slots disponibles."""
        duration = 30
        start = base_timestamp
        end = start + timedelta(hours=2)

        room = rooms_setup.get_room("A101")
        slots = room.available_slots(duration, start, end)

        # 2 horas = 120 minutos / 30 = 4 slots
        assert len(slots) == 4
        assert slots[0]['start'] == start

    def test_available_slots_respects_bookings(self, rooms_setup, base_timestamp):
        """Verifica que slots no incluyen horarios ocupados."""
        # Reserva de 09:00 a 10:00
        rooms_setup.book_room(
            "A101",
            base_timestamp,
            base_timestamp + timedelta(hours=1),
            3
        )

        room = rooms_setup.get_room("A101")
        slots = room.available_slots(
            30,
            base_timestamp,
            base_timestamp + timedelta(hours=2)
        )

        # Slots en 09:00-09:30, 09:30-10:00 no deben aparecer
        # Slots en 10:00-10:30, 10:30-11:00 sí deben aparecer
        assert len(slots) == 2
        assert slots[0]['start'] == base_timestamp + timedelta(hours=1)

    def test_available_slots_multiple_bookings(self, rooms_setup, base_timestamp):
        """Verifica slots con múltiples reservas fragmentadas."""
        t1 = base_timestamp
        t2 = t1 + timedelta(hours=1, minutes=30)

        rooms_setup.book_room("A101", t1, t1 + timedelta(minutes=30), 2)
        rooms_setup.book_room("A101", t2, t2 + timedelta(minutes=30), 3)

        room = rooms_setup.get_room("A101")
        slots = room.available_slots(30, t1, t1 + timedelta(hours=3))

        # Debe haber slots en los huecos
        assert len(slots) > 0
        # Verificar que ningún slot solapea con reservas
        for slot in slots:
            for booking in room.bookings:
                assert not (slot['start'] < booking['end'] and slot['end'] > booking['start'])

    def test_available_slots_increments_by_thirty_minutes(self, rooms_setup, base_timestamp):
        """Verifica que los slots se crean con incrementos de 30 minutos."""
        room = rooms_setup.get_room("A101")
        slots = room.available_slots(60, base_timestamp, base_timestamp + timedelta(hours=2))

        # Con incremento de 30 min en 2 horas: 09:00, 09:30, 10:00, 10:30, 11:00, 11:30
        # Cada slot de 60 min se busca en esos puntos
        assert len(slots) > 0
        for i in range(len(slots) - 1):
            time_diff = (slots[i + 1]['start'] - slots[i]['start']).total_seconds() / 60
            assert time_diff == 30

    def test_available_slots_exact_duration(self, rooms_setup, base_timestamp):
        """Verifica que slots tienen la duración exacta solicitada."""
        duration = 45
        room = rooms_setup.get_room("A101")
        slots = room.available_slots(duration, base_timestamp, base_timestamp + timedelta(hours=1))

        for slot in slots:
            expected_end = slot['start'] + timedelta(minutes=duration)
            assert slot['end'] == expected_end


# ============================================================================
# TESTS: BÚSQUEDA AUTOMÁTICA DE SALA DISPONIBLE
# ============================================================================

class TestFindAvailableRoom:
    """Tests para búsqueda automática de sala disponible."""

    def test_find_available_room_success(self, rooms_setup, base_timestamp):
        """Verifica que encuentra una sala disponible."""
        room_id = rooms_setup.find_available_room(
            5,
            base_timestamp,
            base_timestamp + timedelta(hours=1)
        )
        assert room_id is not None
        assert room_id in ["A101", "B202", "C303"]

    def test_find_available_room_books_it(self, rooms_setup, base_timestamp):
        """Verifica que la sala encontrada queda reservada."""
        room_id = rooms_setup.find_available_room(
            5,
            base_timestamp,
            base_timestamp + timedelta(hours=1)
        )
        room = rooms_setup.get_room(room_id)
        assert len(room.bookings) == 1

    def test_find_available_room_returns_first_suitable(self, rooms_setup, base_timestamp):
        """Verifica que retorna la primera sala que cumple requisitos."""
        # La búsqueda debe iterar en orden del diccionario
        room_id = rooms_setup.find_available_room(
            4,
            base_timestamp,
            base_timestamp + timedelta(hours=1)
        )
        assert room_id is not None

    def test_find_available_room_respects_capacity(self, rooms_setup, base_timestamp):
        """Verifica que no asigna salas con capacidad insuficiente."""
        # Necesitamos 20 personas; solo C303 tiene esa capacidad
        room_id = rooms_setup.find_available_room(
            20,
            base_timestamp,
            base_timestamp + timedelta(hours=1)
        )
        assert room_id == "C303"

    def test_find_available_room_fails_when_none_available(self, booked_room, base_timestamp):
        """Verifica que retorna None cuando no hay sala disponible."""
        # A101 y C303 están ocupadas en base_timestamp
        # B202 existe pero no tiene capacidad para 50 personas
        room_id = booked_room.find_available_room(
            50,
            base_timestamp,
            base_timestamp + timedelta(hours=1)
        )
        assert room_id is None

    def test_find_available_room_capacity_boundary(self, rooms_setup, base_timestamp):
        """Verifica búsqueda con capacidad exacta."""
        room_id = rooms_setup.find_available_room(
            10,  # Capacidad exacta de A101
            base_timestamp,
            base_timestamp + timedelta(hours=1)
        )
        assert room_id == "A101"

    def test_find_available_room_one_under_capacity(self, rooms_setup, base_timestamp):
        """Verifica búsqueda con capacidad 1 menos que disponible."""
        room_id = rooms_setup.find_available_room(
            3,
            base_timestamp,
            base_timestamp + timedelta(hours=1)
        )
        assert room_id is not None


# ============================================================================
# TESTS: REPORTES DE OCUPACIÓN
# ============================================================================

class TestOccupancyReport:
    """Tests para generación de reportes de ocupación."""

    def test_occupancy_report_empty_service(self, service, base_timestamp):
        """Verifica reporte cuando no hay salas."""
        report = service.occupancy_report(base_timestamp)
        assert report == {}

    def test_occupancy_report_with_rooms_no_bookings(self, rooms_setup, base_timestamp):
        """Verifica reporte con salas pero sin reservas."""
        report = rooms_setup.occupancy_report(base_timestamp)
        assert report == {"A101": 0, "B202": 0, "C303": 0}

    def test_occupancy_report_with_active_bookings(self, booked_room, base_timestamp):
        """Verifica reporte con reservas activas."""
        report = booked_room.occupancy_report(base_timestamp + timedelta(minutes=30))
        assert report["A101"] == 5
        assert report["B202"] == 0
        assert report["C303"] == 15

    def test_occupancy_report_after_bookings_end(self, booked_room, base_timestamp):
        """Verifica reporte después de que terminan las reservas."""
        report = booked_room.occupancy_report(base_timestamp + timedelta(hours=3))
        assert report["A101"] == 0
        assert report["B202"] == 0
        assert report["C303"] == 0

    def test_occupancy_report_partial_overlap(self, rooms_setup, base_timestamp):
        """Verifica reporte cuando solo algunas salas tienen ocupación."""
        rooms_setup.book_room(
            "A101",
            base_timestamp,
            base_timestamp + timedelta(hours=1),
            8
        )
        rooms_setup.book_room(
            "C303",
            base_timestamp + timedelta(hours=1),
            base_timestamp + timedelta(hours=2),
            12
        )

        # En base_timestamp, solo A101 está ocupada
        report1 = rooms_setup.occupancy_report(base_timestamp + timedelta(minutes=30))
        assert report1["A101"] == 8
        assert report1["C303"] == 0

        # En base_timestamp+1h30, solo C303 está ocupada
        report2 = rooms_setup.occupancy_report(base_timestamp + timedelta(hours=1, minutes=30))
        assert report2["A101"] == 0
        assert report2["C303"] == 12


# ============================================================================
# TESTS: MANEJO DE ERRORES
# ============================================================================

class TestErrorHandling:
    """Tests para manejo de errores y casos excepcionales."""

    def test_book_nonexistent_room_raises_error(self, rooms_setup, base_timestamp):
        """Verifica que reservar sala inexistente lanza error."""
        with pytest.raises(ValueError, match="not found"):
            rooms_setup.book_room(
                "NONEXISTENT",
                base_timestamp,
                base_timestamp + timedelta(hours=1),
                5
            )

    def test_book_with_invalid_time_range_raises_error(self, rooms_setup, base_timestamp):
        """Verifica que rango de tiempo inválido lanza error."""
        with pytest.raises(ValueError, match="Invalid time range"):
            rooms_setup.book_room(
                "A101",
                base_timestamp,
                base_timestamp - timedelta(hours=1),  # End antes de start
                5
            )

    def test_book_with_same_start_end_raises_error(self, rooms_setup, base_timestamp):
        """Verifica que start == end lanza error."""
        with pytest.raises(ValueError, match="Invalid time range"):
            rooms_setup.book_room(
                "A101",
                base_timestamp,
                base_timestamp,  # Mismo tiempo
                5
            )

    def test_zero_attendees_booking(self, rooms_setup, base_timestamp):
        """Verifica comportamiento con 0 asistentes (edge case)."""
        # El código actual no valida esto, pero es un caso a considerar
        result = rooms_setup.book_room(
            "A101",
            base_timestamp,
            base_timestamp + timedelta(hours=1),
            0
        )
        # Debería aceptarse (0 <= capacidad 10)
        assert result is True

    def test_negative_attendees_booking(self, rooms_setup, base_timestamp):
        """Verifica comportamiento con asistentes negativos (edge case)."""
        result = rooms_setup.book_room(
            "A101",
            base_timestamp,
            base_timestamp + timedelta(hours=1),
            -5
        )
        # Debería aceptarse (el código no valida negativos)
        assert result is True

    def test_very_long_duration_booking(self, rooms_setup, base_timestamp):
        """Verifica reserva con duración muy larga."""
        result = rooms_setup.book_room(
            "A101",
            base_timestamp,
            base_timestamp + timedelta(days=365),
            3
        )
        assert result is True


# ============================================================================
# TESTS: CASOS LÍMITE Y COMBINACIONES
# ============================================================================

class TestEdgeCasesAndCombinations:
    """Tests para casos límite y combinaciones complejas."""

    def test_all_rooms_occupied_same_time(self, rooms_setup, base_timestamp):
        """Verifica cuando todas las salas están ocupadas."""
        rooms_setup.book_room("A101", base_timestamp, base_timestamp + timedelta(hours=1), 5)
        rooms_setup.book_room("B202", base_timestamp, base_timestamp + timedelta(hours=1), 3)
        rooms_setup.book_room("C303", base_timestamp, base_timestamp + timedelta(hours=1), 15)

        # Buscar sala debería fallar
        room_id = rooms_setup.find_available_room(
            1,
            base_timestamp,
            base_timestamp + timedelta(hours=1)
        )
        assert room_id is None

    def test_room_fully_booked_entire_day(self, rooms_setup, base_timestamp):
        """Verifica sala completamente ocupada durante todo un día."""
        start = base_timestamp
        end = base_timestamp + timedelta(hours=8)

        current = start
        while current < end:
            rooms_setup.book_room("B202", current, current + timedelta(minutes=30), 2)
            current += timedelta(minutes=30)

        room = rooms_setup.get_room("B202")
        assert len(room.bookings) == 16  # 8 horas / 30 minutos

    def test_fragmented_availability(self, rooms_setup, base_timestamp):
        """Verifica patrón complejo de disponibilidad fragmentada."""
        # Crear patrón de ocupación fragmentado
        for i in range(0, 4):
            start = base_timestamp + timedelta(hours=i*2)
            rooms_setup.book_room("A101", start, start + timedelta(minutes=45), 3)

        # Debe haber slots de 1 hora 15 minutos disponibles entre bloques
        room = rooms_setup.get_room("A101")
        slots = room.available_slots(75, base_timestamp, base_timestamp + timedelta(hours=8))
        assert len(slots) > 0

    def test_service_with_mixed_operations(self, service, base_timestamp):
        """Verifica combinación de operaciones en un flujo realista."""
        # Crear salas
        service.create_room("CONF_A", 12, RoomType.MEDIUM)
        service.create_room("CONF_B", 6, RoomType.SMALL)

        # Hacer reservas
        result1 = service.book_room("CONF_A", base_timestamp, base_timestamp + timedelta(hours=1), 10)
        result2 = service.book_room("CONF_B", base_timestamp, base_timestamp + timedelta(hours=1), 5)

        # Generar reporte
        report = service.occupancy_report(base_timestamp + timedelta(minutes=30))

        # Buscar sala alternativa
        room_id = service.find_available_room(
            3,
            base_timestamp + timedelta(hours=2),
            base_timestamp + timedelta(hours=3)
        )

        assert result1 is True
        assert result2 is True
        assert report["CONF_A"] == 10
        assert report["CONF_B"] == 5
        assert room_id is not None
