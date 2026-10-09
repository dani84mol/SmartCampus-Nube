-- database/init.sql

DROP TABLE IF EXISTS reservas CASCADE;
DROP TABLE IF EXISTS aulas CASCADE;

-- 1. Tabla de Aulas
CREATE TABLE aulas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    edificio VARCHAR(50) NOT NULL,
    capacidad INT NOT NULL CHECK (capacidad > 0),
    equipamiento TEXT[] NOT NULL DEFAULT '{}'
);

-- 2. Tabla de Reservas
CREATE TABLE reservas (
    id SERIAL PRIMARY KEY,
    aula_id INT NOT NULL REFERENCES aulas(id) ON DELETE CASCADE,
    usuario VARCHAR(100) NOT NULL,
    fecha DATE NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    CONSTRAINT check_horario CHECK (hora_fin > hora_inicio)
);

-- 3. Datos iniciales
INSERT INTO aulas (nombre, edificio, capacidad, equipamiento) VALUES
('Laboratorio de Robótica', 'Edificio A', 30, ARRAY['ordenadores', 'robots', 'impresora 3D']),
('Aula Magna', 'Edificio Central', 150, ARRAY['proyector', 'sistema de sonido', 'microfonía']),
('Seminario 102', 'Edificio B', 15, ARRAY['pizarra digital', 'pantalla']);

INSERT INTO reservas (aula_id, usuario, fecha, hora_inicio, hora_fin) VALUES
(1, 'profesor.garcia@smartcampus.edu', '2026-10-15', '09:00:00', '11:00:00'),
(2, 'decanato@smartcampus.edu', '2026-10-16', '10:00:00', '13:00:00');