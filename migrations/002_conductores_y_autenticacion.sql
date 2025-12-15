-- Migración: Conductores y Autenticación
-- Descripción: Agrega tablas para usuarios, conductores y asignaciones
-- Fecha: 2025-12-13

-- Tabla de usuarios del sistema
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    tipo_usuario VARCHAR(15) NOT NULL DEFAULT 'ciudadano',
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_tipo_usuario CHECK (tipo_usuario IN ('admin', 'conductor', 'ciudadano'))
);

-- Índices para usuarios
CREATE INDEX idx_usuarios_username ON usuarios(username);
CREATE INDEX idx_usuarios_email ON usuarios(email);
CREATE INDEX idx_usuarios_tipo ON usuarios(tipo_usuario);

-- Tabla de conductores (información específica de conductores)
CREATE TABLE IF NOT EXISTS conductores (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER UNIQUE NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    nombre_completo VARCHAR(100) NOT NULL,
    cedula VARCHAR(10) UNIQUE NOT NULL,
    telefono VARCHAR(15),
    licencia_tipo VARCHAR(5),
    fecha_contratacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado VARCHAR(15) DEFAULT 'disponible',
    zona_preferida VARCHAR(15) DEFAULT 'ambas',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_conductor_estado CHECK (estado IN ('disponible', 'ocupado', 'inactivo')),
    CONSTRAINT check_conductor_zona CHECK (zona_preferida IN ('oriental', 'occidental', 'ambas')),
    CONSTRAINT check_licencia_tipo CHECK (licencia_tipo IN ('C', 'D', 'E'))
);

-- Índices para conductores
CREATE INDEX idx_conductores_cedula ON conductores(cedula);
CREATE INDEX idx_conductores_estado ON conductores(estado);
CREATE INDEX idx_conductores_zona ON conductores(zona_preferida);

-- Tabla de asignaciones de conductores a rutas
CREATE TABLE IF NOT EXISTS asignaciones_conductores (
    id SERIAL PRIMARY KEY,
    ruta_id INTEGER NOT NULL REFERENCES rutas_generadas(id) ON DELETE CASCADE,
    conductor_id INTEGER NOT NULL REFERENCES conductores(id) ON DELETE CASCADE,
    camion_tipo VARCHAR(10) NOT NULL,
    camion_id VARCHAR(20),
    fecha_asignacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_inicio TIMESTAMP,
    fecha_finalizacion TIMESTAMP,
    estado VARCHAR(15) DEFAULT 'asignado',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_asignacion_camion_tipo CHECK (camion_tipo IN ('lateral', 'posterior')),
    CONSTRAINT check_asignacion_estado CHECK (estado IN ('asignado', 'iniciado', 'completado', 'cancelado'))
);

-- Índices para asignaciones
CREATE INDEX idx_asignaciones_ruta ON asignaciones_conductores(ruta_id);
CREATE INDEX idx_asignaciones_conductor ON asignaciones_conductores(conductor_id);
CREATE INDEX idx_asignaciones_estado ON asignaciones_conductores(estado);

-- Función para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers para updated_at
CREATE TRIGGER update_usuarios_updated_at BEFORE UPDATE ON usuarios
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conductores_updated_at BEFORE UPDATE ON conductores
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_asignaciones_updated_at BEFORE UPDATE ON asignaciones_conductores
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insertar usuario administrador por defecto
-- Contraseña: admin123 (debe cambiarse en producción)
-- Hash generado con bcrypt
INSERT INTO usuarios (username, email, password_hash, tipo_usuario)
VALUES ('admin', 'admin@epagal.gob.ec', '$2b$12$iGOwGAo3eHkRO3dncaOHdeuEdRswIARrt2QZ805XKk5wS.z7vtRHG', 'admin')
ON CONFLICT (username) DO NOTHING;

-- Insertar conductores de prueba
-- Contraseña para todos: conductor123
-- Hash generado con bcrypt
INSERT INTO usuarios (username, email, password_hash, tipo_usuario)
VALUES 
    ('conductor1', 'juan.perez@epagal.gob.ec', '$2b$12$h3esIL5JWWqnLyMD/WBJHe7oV4uesJMKaaty1OHsZS.lH6OjVJx4.', 'conductor'),
    ('conductor2', 'maria.lopez@epagal.gob.ec', '$2b$12$h3esIL5JWWqnLyMD/WBJHe7oV4uesJMKaaty1OHsZS.lH6OjVJx4.', 'conductor'),
    ('conductor3', 'carlos.gomez@epagal.gob.ec', '$2b$12$h3esIL5JWWqnLyMD/WBJHe7oV4uesJMKaaty1OHsZS.lH6OjVJx4.', 'conductor'),
    ('conductor4', 'ana.torres@epagal.gob.ec', '$2b$12$h3esIL5JWWqnLyMD/WBJHe7oV4uesJMKaaty1OHsZS.lH6OjVJx4.', 'conductor')
ON CONFLICT (username) DO NOTHING;

-- Insertar información de conductores
INSERT INTO conductores (usuario_id, nombre_completo, cedula, telefono, licencia_tipo, zona_preferida)
SELECT u.id, 'Juan Pérez Martínez', '1803456789', '0987654321', 'C', 'oriental'
FROM usuarios u WHERE u.username = 'conductor1'
ON CONFLICT (cedula) DO NOTHING;

INSERT INTO conductores (usuario_id, nombre_completo, cedula, telefono, licencia_tipo, zona_preferida)
SELECT u.id, 'María López García', '1804567890', '0987654322', 'C', 'occidental'
FROM usuarios u WHERE u.username = 'conductor2'
ON CONFLICT (cedula) DO NOTHING;

INSERT INTO conductores (usuario_id, nombre_completo, cedula, telefono, licencia_tipo, zona_preferida)
SELECT u.id, 'Carlos Gómez Ruiz', '1805678901', '0987654323', 'D', 'ambas'
FROM usuarios u WHERE u.username = 'conductor3'
ON CONFLICT (cedula) DO NOTHING;

INSERT INTO conductores (usuario_id, nombre_completo, cedula, telefono, licencia_tipo, zona_preferida)
SELECT u.id, 'Ana Torres Vega', '1806789012', '0987654324', 'C', 'oriental'
FROM usuarios u WHERE u.username = 'conductor4'
ON CONFLICT (cedula) DO NOTHING;

-- Comentarios en las tablas
COMMENT ON TABLE usuarios IS 'Usuarios del sistema con autenticación';
COMMENT ON TABLE conductores IS 'Información específica de conductores de camiones';
COMMENT ON TABLE asignaciones_conductores IS 'Asignaciones de conductores a rutas y camiones';

COMMENT ON COLUMN usuarios.tipo_usuario IS 'Tipo de usuario: admin, conductor, ciudadano';
COMMENT ON COLUMN conductores.estado IS 'Estado del conductor: disponible, ocupado, inactivo';
COMMENT ON COLUMN conductores.licencia_tipo IS 'Tipo de licencia de conducir: C, D, E';
COMMENT ON COLUMN asignaciones_conductores.estado IS 'Estado de la asignación: asignado, iniciado, completado, cancelado';
