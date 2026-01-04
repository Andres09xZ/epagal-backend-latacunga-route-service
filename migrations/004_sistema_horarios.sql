-- =====================================================
-- Migración: Sistema de Horarios de Recolección
-- Fecha: 2026-01-03
-- Descripción: Tablas para gestión de horarios,
--              sectores, ejecuciones y tracking
-- =====================================================

-- Habilitar extensión PostGIS si no está habilitada
CREATE EXTENSION IF NOT EXISTS postgis;

-- =====================================================
-- TABLA: sectores
-- Sectores geográficos de Latacunga
-- =====================================================
CREATE TABLE IF NOT EXISTS sectores (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    zona VARCHAR(10) NOT NULL CHECK (zona IN ('oriental', 'occidental')),
    poligono GEOMETRY(POLYGON, 4326) NOT NULL,
    coordenadas_centro GEOMETRY(POINT, 4326) NOT NULL,
    poblacion_estimada INTEGER,
    cantidad_viviendas INTEGER,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices espaciales para sectores
CREATE INDEX IF NOT EXISTS idx_sectores_poligono ON sectores USING GIST (poligono);
CREATE INDEX IF NOT EXISTS idx_sectores_centro ON sectores USING GIST (coordenadas_centro);
CREATE INDEX IF NOT EXISTS idx_sectores_zona ON sectores (zona);

-- =====================================================
-- TABLA: horarios_recoleccion
-- Horarios fijos de recolección por sector
-- =====================================================
CREATE TABLE IF NOT EXISTS horarios_recoleccion (
    id SERIAL PRIMARY KEY,
    sector_id INTEGER NOT NULL REFERENCES sectores(id) ON DELETE CASCADE,
    
    -- Días de la semana (1=Lun, 2=Mar, ..., 7=Dom)
    dias_semana VARCHAR(20) NOT NULL, -- "1,3,5" = Lun, Mié, Vie
    hora_inicio VARCHAR(5) NOT NULL,  -- "06:00"
    hora_fin VARCHAR(5) NOT NULL,     -- "08:00"
    
    -- Tipo de recolección
    tipo VARCHAR(20) DEFAULT 'domestica' CHECK (tipo IN ('domestica', 'comercial', 'barrido')),
    descripcion TEXT,
    
    -- Recursos asignados
    camion_tipo VARCHAR(15) CHECK (camion_tipo IN ('lateral', 'posterior')),
    conductor_id INTEGER REFERENCES conductores(id) ON DELETE SET NULL,
    camion_placa VARCHAR(20),
    
    -- Ruta predefinida
    ruta_optimizada GEOMETRY(LINESTRING, 4326),
    distancia_km FLOAT,
    duracion_estimada INTERVAL,
    
    -- Control de vigencia
    activo BOOLEAN DEFAULT TRUE,
    fecha_inicio_vigencia TIMESTAMP NOT NULL,
    fecha_fin_vigencia TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para horarios
CREATE INDEX IF NOT EXISTS idx_horarios_sector ON horarios_recoleccion (sector_id);
CREATE INDEX IF NOT EXISTS idx_horarios_conductor ON horarios_recoleccion (conductor_id);
CREATE INDEX IF NOT EXISTS idx_horarios_activo ON horarios_recoleccion (activo);
CREATE INDEX IF NOT EXISTS idx_horarios_ruta ON horarios_recoleccion USING GIST (ruta_optimizada);

-- =====================================================
-- TABLA: ejecuciones_horario
-- Registro de ejecución diaria de horarios
-- =====================================================
CREATE TABLE IF NOT EXISTS ejecuciones_horario (
    id SERIAL PRIMARY KEY,
    horario_id INTEGER NOT NULL REFERENCES horarios_recoleccion(id) ON DELETE CASCADE,
    
    -- Planificación
    fecha_programada TIMESTAMP NOT NULL,
    hora_inicio_programada VARCHAR(5) NOT NULL,
    hora_fin_programada VARCHAR(5) NOT NULL,
    
    -- Ejecución real
    fecha_inicio_real TIMESTAMP,
    fecha_fin_real TIMESTAMP,
    
    -- Asignación
    conductor_id INTEGER NOT NULL REFERENCES conductores(id),
    camion_placa VARCHAR(20) NOT NULL,
    
    -- Estado
    estado VARCHAR(15) DEFAULT 'programada' CHECK (estado IN ('programada', 'en_curso', 'completada', 'cancelada', 'atrasada')),
    porcentaje_cumplimiento FLOAT CHECK (porcentaje_cumplimiento >= 0 AND porcentaje_cumplimiento <= 100),
    
    -- Tracking GPS
    ruta_recorrida GEOMETRY(LINESTRING, 4326),
    
    -- Observaciones
    observaciones TEXT,
    incidentes TEXT,
    
    -- Métricas
    toneladas_recolectadas FLOAT CHECK (toneladas_recolectadas >= 0),
    viviendas_atendidas INTEGER CHECK (viviendas_atendidas >= 0),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para ejecuciones
CREATE INDEX IF NOT EXISTS idx_ejecuciones_horario ON ejecuciones_horario (horario_id);
CREATE INDEX IF NOT EXISTS idx_ejecuciones_conductor ON ejecuciones_horario (conductor_id);
CREATE INDEX IF NOT EXISTS idx_ejecuciones_fecha ON ejecuciones_horario (fecha_programada);
CREATE INDEX IF NOT EXISTS idx_ejecuciones_estado ON ejecuciones_horario (estado);
CREATE INDEX IF NOT EXISTS idx_ejecuciones_ruta ON ejecuciones_horario USING GIST (ruta_recorrida);

-- =====================================================
-- TABLA: puntos_tracking_horario
-- Puntos GPS de tracking en tiempo real
-- =====================================================
CREATE TABLE IF NOT EXISTS puntos_tracking_horario (
    id SERIAL PRIMARY KEY,
    ejecucion_id INTEGER NOT NULL REFERENCES ejecuciones_horario(id) ON DELETE CASCADE,
    
    punto GEOMETRY(POINT, 4326) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    velocidad FLOAT CHECK (velocidad >= 0) -- km/h
);

-- Índices para puntos de tracking
CREATE INDEX IF NOT EXISTS idx_tracking_ejecucion ON puntos_tracking_horario (ejecucion_id);
CREATE INDEX IF NOT EXISTS idx_tracking_punto ON puntos_tracking_horario USING GIST (punto);
CREATE INDEX IF NOT EXISTS idx_tracking_timestamp ON puntos_tracking_horario (timestamp);

-- =====================================================
-- TABLA: suspensiones_horario
-- Suspensiones temporales de horarios
-- =====================================================
CREATE TABLE IF NOT EXISTS suspensiones_horario (
    id SERIAL PRIMARY KEY,
    horario_id INTEGER NOT NULL REFERENCES horarios_recoleccion(id) ON DELETE CASCADE,
    
    fecha_suspension TIMESTAMP NOT NULL,
    motivo TEXT NOT NULL,
    fecha_recuperacion TIMESTAMP, -- Día alternativo
    
    notificado BOOLEAN DEFAULT FALSE,
    created_by INTEGER REFERENCES usuarios(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para suspensiones
CREATE INDEX IF NOT EXISTS idx_suspensiones_horario ON suspensiones_horario (horario_id);
CREATE INDEX IF NOT EXISTS idx_suspensiones_fecha ON suspensiones_horario (fecha_suspension);

-- =====================================================
-- TRIGGERS: Actualizar updated_at automáticamente
-- =====================================================

-- Función para actualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para sectores
DROP TRIGGER IF EXISTS update_sectores_updated_at ON sectores;
CREATE TRIGGER update_sectores_updated_at
    BEFORE UPDATE ON sectores
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger para horarios_recoleccion
DROP TRIGGER IF EXISTS update_horarios_updated_at ON horarios_recoleccion;
CREATE TRIGGER update_horarios_updated_at
    BEFORE UPDATE ON horarios_recoleccion
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger para ejecuciones_horario
DROP TRIGGER IF EXISTS update_ejecuciones_updated_at ON ejecuciones_horario;
CREATE TRIGGER update_ejecuciones_updated_at
    BEFORE UPDATE ON ejecuciones_horario
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- DATOS INICIALES: Sectores de ejemplo
-- =====================================================

-- Insertar sectores de ejemplo (La Matriz como ejemplo)
INSERT INTO sectores (nombre, zona, poligono, coordenadas_centro, poblacion_estimada, cantidad_viviendas)
VALUES (
    'La Matriz',
    'occidental',
    ST_GeomFromText('POLYGON((-78.6191 -0.9344, -78.6150 -0.9344, -78.6150 -0.9300, -78.6191 -0.9300, -78.6191 -0.9344))', 4326),
    ST_GeomFromText('POINT(-78.6170 -0.9322)', 4326),
    5000,
    1200
)
ON CONFLICT (nombre) DO NOTHING;

INSERT INTO sectores (nombre, zona, poligono, coordenadas_centro, poblacion_estimada, cantidad_viviendas)
VALUES (
    'San Felipe',
    'oriental',
    ST_GeomFromText('POLYGON((-78.6100 -0.9300, -78.6050 -0.9300, -78.6050 -0.9250, -78.6100 -0.9250, -78.6100 -0.9300))', 4326),
    ST_GeomFromText('POINT(-78.6075 -0.9275)', 4326),
    4500,
    1100
)
ON CONFLICT (nombre) DO NOTHING;

-- =====================================================
-- COMENTARIOS DE TABLAS
-- =====================================================

COMMENT ON TABLE sectores IS 'Sectores geográficos de Latacunga para organizar recolección';
COMMENT ON TABLE horarios_recoleccion IS 'Horarios fijos semanales de recolección por sector';
COMMENT ON TABLE ejecuciones_horario IS 'Registro diario de ejecución de horarios con métricas';
COMMENT ON TABLE puntos_tracking_horario IS 'Tracking GPS en tiempo real durante ejecuciones';
COMMENT ON TABLE suspensiones_horario IS 'Suspensiones temporales por feriados o mantenimiento';

-- =====================================================
-- VISTAS ÚTILES
-- =====================================================

-- Vista: Horarios activos con información del sector
CREATE OR REPLACE VIEW vista_horarios_activos AS
SELECT 
    h.id,
    h.sector_id,
    s.nombre AS sector_nombre,
    s.zona AS sector_zona,
    h.dias_semana,
    h.hora_inicio,
    h.hora_fin,
    h.tipo,
    h.camion_tipo,
    h.conductor_id,
    h.distancia_km,
    h.fecha_inicio_vigencia
FROM horarios_recoleccion h
JOIN sectores s ON h.sector_id = s.id
WHERE h.activo = TRUE
ORDER BY s.nombre, h.hora_inicio;

-- Vista: Ejecuciones de hoy
CREATE OR REPLACE VIEW vista_ejecuciones_hoy AS
SELECT 
    e.id,
    e.horario_id,
    s.nombre AS sector_nombre,
    e.hora_inicio_programada,
    e.hora_fin_programada,
    e.conductor_id,
    c.usuario_id,
    e.estado,
    e.porcentaje_cumplimiento
FROM ejecuciones_horario e
JOIN horarios_recoleccion h ON e.horario_id = h.id
JOIN sectores s ON h.sector_id = s.id
LEFT JOIN conductores c ON e.conductor_id = c.id
WHERE DATE(e.fecha_programada) = CURRENT_DATE
ORDER BY e.hora_inicio_programada;

-- =====================================================
-- FINALIZADO
-- =====================================================

-- Verificar tablas creadas
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) AS column_count
FROM information_schema.tables t
WHERE table_schema = 'public'
    AND table_name IN ('sectores', 'horarios_recoleccion', 'ejecuciones_horario', 'puntos_tracking_horario', 'suspensiones_horario')
ORDER BY table_name;
