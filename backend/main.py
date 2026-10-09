import os
import time
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI(
    title="SmartCampus API",
    version="1.0.0",
    description="API REST para la gestión de espacios y reservas universitarias"
)

# Configuración de CORS para permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variables de entorno con valores por defecto
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "campus_db")
DB_USER = os.getenv("DB_USER", "campus_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "campus_pass")
DB_PORT = os.getenv("DB_PORT", "5432")


def get_db_connection():
    """Conexión resiliente a PostgreSQL con reintentos para soportar arranques asíncronos."""
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


@app.get("/health")
def health_check():
    """Endpoint obligatorio para comprobar el estado del servicio y su conexión con la BD."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
        conn.close()
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "warning", "database": "disconnected", "error": str(e)}


@app.get("/rooms")
def get_rooms():
    """Listar todas las aulas registradas."""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT id, nombre, edificio, capacidad, equipamiento FROM aulas ORDER BY id;")
        rooms = cur.fetchall()
    conn.close()
    return rooms


@app.get("/rooms/{room_id}")
def get_room(room_id: int):
    """Obtener el detalle de un aula por su identificador."""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, nombre, edificio, capacidad, equipamiento FROM aulas WHERE id = %s;",
            (room_id,)
        )
        room = cur.fetchone()
    conn.close()
    if not room:
        raise HTTPException(status_code=404, detail="Aula no encontrada")
    return room


@app.get("/bookings")
def get_bookings():
    """Listar todas las reservas junto con el nombre del aula."""
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