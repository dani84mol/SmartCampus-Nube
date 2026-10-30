import os
import time
from datetime import date, time as time_type
from typing import List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI(
    title="SmartCampus API",
    version="1.0.0",
    description="API REST para la gestión de espacios y reservas universitarias"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "campus_db")
DB_USER = os.getenv("DB_USER", "campus_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "campus_pass")
DB_PORT = os.getenv("DB_PORT", "5432")


def get_db_connection():
    retries = 5
    while retries > 0:
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                port=DB_PORT,
                cursor_factory=RealDictCursor,
            )
            return conn
        except psycopg2.OperationalError:
            retries -= 1
            time.sleep(1)
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="No se pudo establecer conexión con la base de datos",
    )


# --- MODELOS PYDANTIC: AULAS ---
class RoomCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    edificio: str = Field(..., min_length=1, max_length=50)
    capacidad: int = Field(..., gt=0)
    equipamiento: List[str] = []


class RoomUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    edificio: Optional[str] = Field(None, min_length=1, max_length=50)
    capacidad: Optional[int] = Field(None, gt=0)
    equipamiento: Optional[List[str]] = None


# --- MODELOS PYDANTIC: RESERVAS ---
class BookingCreate(BaseModel):
    aula_id: int
    usuario: str = Field(..., min_length=1, max_length=100)
    fecha: date
    hora_inicio: time_type
    hora_fin: time_type

    @field_validator('hora_fin')
    def validate_horarios(cls, v, values):
        if 'hora_inicio' in values.data and v <= values.data['hora_inicio']:
            raise ValueError('La hora de fin debe ser posterior a la hora de inicio')
        return v


class BookingUpdate(BaseModel):
    aula_id: Optional[int] = None
    usuario: Optional[str] = Field(None, min_length=1, max_length=100)
    fecha: Optional[date] = None
    hora_inicio: Optional[time_type] = None
    hora_fin: Optional[time_type] = None


@app.get("/health")
def health_check():
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
        conn.close()
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "warning", "database": "disconnected", "error": str(e)}


# --- ENDPOINTS: AULAS ---
@app.get("/rooms")
def get_rooms():
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT id, nombre, edificio, capacidad, equipamiento FROM aulas ORDER BY id;")
        rooms = cur.fetchall()
    conn.close()
    return rooms


@app.get("/rooms/{room_id}")
def get_room(room_id: int):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT id, nombre, edificio, capacidad, equipamiento FROM aulas WHERE id = %s;", (room_id,))
        room = cur.fetchone()
    conn.close()
    if not room:
        raise HTTPException(status_code=404, detail="Aula no encontrada")
    return room


@app.post("/rooms", status_code=status.HTTP_201_CREATED)
def create_room(room: RoomCreate):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO aulas (nombre, edificio, capacidad, equipamiento)
            VALUES (%s, %s, %s, %s)
            RETURNING id, nombre, edificio, capacidad, equipamiento;
            """,
            (room.nombre, room.edificio, room.capacidad, room.equipamiento)
        )
        new_room = cur.fetchone()
        conn.commit()
    conn.close()
    return new_room


@app.put("/rooms/{room_id}")
def update_room(room_id: int, room: RoomUpdate):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM aulas WHERE id = %s;", (room_id,))
        existing_room = cur.fetchone()
        if not existing_room:
            conn.close()
            raise HTTPException(status_code=404, detail="Aula no encontrada")

        nombre = room.nombre if room.nombre is not None else existing_room["nombre"]
        edificio = room.edificio if room.edificio is not None else existing_room["edificio"]
        capacidad = room.capacidad if room.capacidad is not None else existing_room["capacidad"]
        equipamiento = room.equipamiento if room.equipamiento is not None else existing_room["equipamiento"]

        cur.execute(
            """
            UPDATE aulas
            SET nombre = %s, edificio = %s, capacidad = %s, equipamiento = %s
            WHERE id = %s
            RETURNING id, nombre, edificio, capacidad, equipamiento;
            """,
            (nombre, edificio, capacidad, equipamiento, room_id)
        )
        updated_room = cur.fetchone()
        conn.commit()
    conn.close()
    return updated_room


@app.delete("/rooms/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room(room_id: int):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM aulas WHERE id = %s;", (room_id,))
        if not cur.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Aula no encontrada")

        cur.execute("DELETE FROM aulas WHERE id = %s;", (room_id,))
        conn.commit()
    conn.close()
    return None


# --- FUNCION AUXILIAR: VALIDACIÓN DE SOLAPAMIENTO ---
def check_booking_overlap(cur, aula_id: int, fecha: date, hora_inicio: time_type, hora_fin: time_type, exclude_booking_id: Optional[int] = None):
    query = """
        SELECT id FROM reservas
        WHERE aula_id = %s
          AND fecha = %s
          AND hora_inicio < %s
          AND hora_fin > %s
    """
    params = [aula_id, fecha, hora_fin, hora_inicio]

    if exclude_booking_id is not None:
        query += " AND id != %s"
        params.append(exclude_booking_id)

    cur.execute(query, tuple(params))
    if cur.fetchone():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El aula ya se encuentra reservada en el rango horario seleccionado."
        )


# --- ENDPOINTS: RESERVAS ---
@app.get("/bookings")
def get_bookings():
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT r.id, r.aula_id, a.nombre AS aula_nombre, r.usuario,
                   r.fecha::text, r.hora_inicio::text, r.hora_fin::text
            FROM reservas r
            JOIN aulas a ON r.aula_id = a.id
            ORDER BY r.fecha, r.hora_inicio;
        """)
        bookings = cur.fetchall()
    conn.close()
    return bookings


@app.post("/bookings", status_code=status.HTTP_201_CREATED)
def create_booking(booking: BookingCreate):
    conn = get_db_connection()
    with conn.cursor() as cur:
        # 1. Verificar existencia del aula
        cur.execute("SELECT id FROM aulas WHERE id = %s;", (booking.aula_id,))
        if not cur.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="El aula especificada no existe")

        # 2. Verificar solapamientos
        check_booking_overlap(cur, booking.aula_id, booking.fecha, booking.hora_inicio, booking.hora_fin)

        # 3. Insertar reserva
        cur.execute(
            """
            INSERT INTO reservas (aula_id, usuario, fecha, hora_inicio, hora_fin)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, aula_id, usuario, fecha::text, hora_inicio::text, hora_fin::text;
            """,
            (booking.aula_id, booking.usuario, booking.fecha, booking.hora_inicio, booking.hora_fin)
        )
        new_booking = cur.fetchone()
        conn.commit()
    conn.close()
    return new_booking


@app.put("/bookings/{booking_id}")
def update_booking(booking_id: int, booking: BookingUpdate):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM reservas WHERE id = %s;", (booking_id,))
        existing = cur.fetchone()
        if not existing:
            conn.close()
            raise HTTPException(status_code=404, detail="Reserva no encontrada")

        aula_id = booking.aula_id if booking.aula_id is not None else existing["aula_id"]
        usuario = booking.usuario if booking.usuario is not None else existing["usuario"]
        fecha = booking.fecha if booking.fecha is not None else existing["fecha"]
        hora_inicio = booking.hora_inicio if booking.hora_inicio is not None else existing["hora_inicio"]
        hora_fin = booking.hora_fin if booking.hora_fin is not None else existing["hora_fin"]

        if hora_fin <= hora_inicio:
            conn.close()
            raise HTTPException(status_code=400, detail="La hora de fin debe ser posterior a la hora de inicio")

        # Verificar solapamiento excluyendo la propia reserva que estamos editando
        check_booking_overlap(cur, aula_id, fecha, hora_inicio, hora_fin, exclude_booking_id=booking_id)

        cur.execute(
            """
            UPDATE reservas
            SET aula_id = %s, usuario = %s, fecha = %s, hora_inicio = %s, hora_fin = %s
            WHERE id = %s
            RETURNING id, aula_id, usuario, fecha::text, hora_inicio::text, hora_fin::text;
            """,
            (aula_id, usuario, fecha, hora_inicio, hora_fin, booking_id)
        )
        updated_booking = cur.fetchone()
        conn.commit()
    conn.close()
    return updated_booking


@app.delete("/bookings/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(booking_id: int):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM reservas WHERE id = %s;", (booking_id,))
        if not cur.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Reserva no encontrada")

        cur.execute("DELETE FROM reservas WHERE id = %s;", (booking_id,))
        conn.commit()
    conn.close()
    return None