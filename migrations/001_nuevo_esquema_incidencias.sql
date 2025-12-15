-- ============================================================================
-- MIGRACIÓN: Nuevo esquema de base de datos para sistema de incidencias
-- Fecha: 2025-12-13
-- Descripción: Implementa tablas para gestión de incidencias, rutas optimizadas
--              y configuración del sistema
-- ============================================================================

-- Verificar que PostGIS esté habilitado
CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================================================
-- 1. TABLA: incidencias (reportes de los ciudadanos)
-- ============================================================================
CREATE TABLE IF NOT EXISTS incidencias (
    id                  SERIAL PRIMARY KEY,
    tipo                VARCHAR(20) NOT NULL CHECK (tipo IN ('acopio', 'zona_critica', 'animal_muerto')),
    gravedad            SMALLINT NOT NULL CHECK (gravedad IN (1, 3, 5)),  -- 1=acopio, 3=zona, 5=animal
    descripcion         TEXT,
    foto_url            VARCHAR(255),                 -- opcional, foto subida
    lat                 DOUBLE PRECISION NOT NULL,
    lon                 DOUBLE PRECISION NOT NULL,
    geom                GEOMETRY(Point, 4326) NOT NULL,  -- PostGIS: punto en WGS84
    utm_easting         DOUBLE PRECISION,               -- calculado al insertar
    utm_northing        DOUBLE PRECISION,
    zona                VARCHAR(10) CHECK (zona IN ('oriental', 'occidental')),  -- calculado automáticamente
    ventana_inicio      TIMESTAMP,                      -- opcional: hora estimada inicio atención
    ventana_fin         TIMESTAMP,                      -- opcional: hora límite (ej. +4h desde reporte)
    estado              VARCHAR(15) DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'asignada', 'completada', 'cancelada')),
    reportado_en        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_id          INTEGER,                        -- FK a usuarios (opcional)
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices geo importantes para incidencias
CREATE INDEX IF NOT EXISTS idx_incidencias_geom ON incidencias USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_incidencias_zona ON incidencias (zona);
CREATE INDEX IF NOT EXISTS idx_incidencias_estado ON incidencias (estado);
CREATE INDEX IF NOT EXISTS idx_incidencias_tipo ON incidencias (tipo);
CREATE INDEX IF NOT EXISTS idx_incidencias_reportado_en ON incidencias (reportado_en);

-- Trigger para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_incidencias_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_incidencias_updated_at
    BEFORE UPDATE ON incidencias
    FOR EACH ROW
    EXECUTE FUNCTION update_incidencias_updated_at();

-- ============================================================================
-- 2. TABLA: rutas_generadas (cada vez que se calcula una ruta óptima)
-- ============================================================================
CREATE TABLE IF NOT EXISTS rutas_generadas (
    id                  SERIAL PRIMARY KEY,
    zona                VARCHAR(10) NOT NULL CHECK (zona IN ('oriental', 'occidental')),
    fecha_generacion    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    suma_gravedad       INTEGER NOT NULL,               -- suma de gravedad que disparó la ruta
    costo_total         DOUBLE PRECISION,               -- distancia o tiempo total optimizado
    duracion_estimada   INTERVAL,                       -- ej. 2 hours 30 minutes
    camiones_usados     SMALLINT,                       -- cuántos camiones se asignaron
    estado              VARCHAR(15) DEFAULT 'planeada' CHECK (estado IN ('planeada', 'en_ejecucion', 'completada')),
    notas               TEXT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para rutas_generadas
CREATE INDEX IF NOT EXISTS idx_rutas_generadas_zona ON rutas_generadas (zona);
CREATE INDEX IF NOT EXISTS idx_rutas_generadas_estado ON rutas_generadas (estado);
CREATE INDEX IF NOT EXISTS idx_rutas_generadas_fecha ON rutas_generadas (fecha_generacion);

-- Trigger para actualizar updated_at
CREATE OR REPLACE FUNCTION update_rutas_generadas_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_rutas_generadas_updated_at
    BEFORE UPDATE ON rutas_generadas
    FOR EACH ROW
    EXECUTE FUNCTION update_rutas_generadas_updated_at();

-- ============================================================================
-- 3. TABLA: rutas_detalle (secuencia de puntos por camión en cada ruta generada)
-- ============================================================================
CREATE TABLE IF NOT EXISTS rutas_detalle (
    id                  SERIAL PRIMARY KEY,
    ruta_id             INTEGER REFERENCES rutas_generadas(id) ON DELETE CASCADE,
    camion_tipo         VARCHAR(10) CHECK (camion_tipo IN ('lateral', 'posterior')),
    camion_id           VARCHAR(20),                    -- placa o identificador real (opcional)
    orden               SMALLINT NOT NULL,              -- orden en la ruta: 1=base, 2..n=incidencias, último=botadero
    incidencia_id       INTEGER REFERENCES incidencias(id) ON DELETE SET NULL,  -- NULL para base/botadero
    tipo_punto          VARCHAR(15) CHECK (tipo_punto IN ('deposito', 'incidencia', 'botadero')),
    lat                 DOUBLE PRECISION,
    lon                 DOUBLE PRECISION,
    llegada_estimada    TIMESTAMP,                      -- calculada por el solver
    tiempo_servicio     INTERVAL DEFAULT '10 minutes',   -- tiempo de recolección en el punto
    carga_acumulada     SMALLINT,                       -- gravedad acumulada hasta ese punto
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para rutas_detalle
CREATE INDEX IF NOT EXISTS idx_rutas_detalle_ruta_id ON rutas_detalle (ruta_id);
CREATE INDEX IF NOT EXISTS idx_rutas_detalle_incidencia_id ON rutas_detalle (incidencia_id);
CREATE INDEX IF NOT EXISTS idx_rutas_detalle_orden ON rutas_detalle (ruta_id, orden);
CREATE INDEX IF NOT EXISTS idx_rutas_detalle_camion ON rutas_detalle (ruta_id, camion_tipo, camion_id);

-- ============================================================================
-- 4. TABLA: puntos_fijos (configuración estática: depósito y botadero)
-- ============================================================================
CREATE TABLE IF NOT EXISTS puntos_fijos (
    id                  SERIAL PRIMARY KEY,
    nombre              VARCHAR(50) UNIQUE NOT NULL,
    tipo                VARCHAR(15) CHECK (tipo IN ('deposito', 'botadero')),
    lat                 DOUBLE PRECISION NOT NULL,
    lon                 DOUBLE PRECISION NOT NULL,
    geom                GEOMETRY(Point, 4326) NOT NULL,
    activo              BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índice geoespacial para puntos_fijos
CREATE INDEX IF NOT EXISTS idx_puntos_fijos_geom ON puntos_fijos USING GIST (geom);

-- Datos iniciales para puntos_fijos (ejecutar una vez)
INSERT INTO puntos_fijos (nombre, tipo, lat, lon, geom) VALUES
    ('Depósito EPAGAL', 'deposito', -0.936, -78.613, ST_SetSRID(ST_MakePoint(-78.613, -0.936), 4326)),
    ('Botadero Inchapo', 'botadero', -0.949, -78.663, ST_SetSRID(ST_MakePoint(-78.663, -0.949), 4326))
ON CONFLICT (nombre) DO NOTHING;

-- ============================================================================
-- 5. TABLA: config (parámetros globales del sistema)
-- ============================================================================
CREATE TABLE IF NOT EXISTS config (
    id                  SERIAL PRIMARY KEY,
    clave               VARCHAR(50) UNIQUE NOT NULL,
    valor               TEXT NOT NULL,
    descripcion         TEXT,
    tipo_dato           VARCHAR(20) DEFAULT 'string' CHECK (tipo_dato IN ('string', 'integer', 'float', 'boolean')),
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índice para búsqueda rápida por clave
CREATE INDEX IF NOT EXISTS idx_config_clave ON config (clave);

-- Valores iniciales de configuración
INSERT INTO config (clave, valor, descripcion, tipo_dato) VALUES
    ('umbral_gravedad', '20', 'Puntos mínimos para generar ruta por zona', 'integer'),
    ('capacidad_lateral', '3', 'Capacidad en puntos de gravedad - camión lateral', 'integer'),
    ('capacidad_posterior', '5', 'Capacidad en puntos de gravedad - camión posterior', 'integer'),
    ('velocidad_promedio_kmh', '30', 'Velocidad promedio para estimar tiempos', 'integer'),
    ('tiempo_servicio_minutos', '10', 'Tiempo promedio de recolección por incidencia', 'integer')
ON CONFLICT (clave) DO NOTHING;

-- ============================================================================
-- COMENTARIOS ADICIONALES EN LAS TABLAS
-- ============================================================================
COMMENT ON TABLE incidencias IS 'Reportes de ciudadanos sobre incidencias de limpieza';
COMMENT ON TABLE rutas_generadas IS 'Rutas optimizadas generadas por el sistema OR-Tools';
COMMENT ON TABLE rutas_detalle IS 'Secuencia detallada de puntos para cada ruta y camión';
COMMENT ON TABLE puntos_fijos IS 'Ubicaciones fijas: depósito y botadero';
COMMENT ON TABLE config IS 'Parámetros de configuración global del sistema';

-- ============================================================================
-- VISTAS ÚTILES
-- ============================================================================

-- Vista: Incidencias pendientes agrupadas por zona
CREATE OR REPLACE VIEW v_incidencias_pendientes_por_zona AS
SELECT 
    zona,
    COUNT(*) AS total_incidencias,
    SUM(gravedad) AS suma_gravedad,
    COUNT(CASE WHEN tipo = 'animal_muerto' THEN 1 END) AS animales_muertos,
    COUNT(CASE WHEN tipo = 'zona_critica' THEN 1 END) AS zonas_criticas,
    COUNT(CASE WHEN tipo = 'acopio' THEN 1 END) AS acopios,
    MIN(reportado_en) AS reporte_mas_antiguo,
    MAX(reportado_en) AS reporte_mas_reciente
FROM incidencias
WHERE estado = 'pendiente'
GROUP BY zona;

-- Vista: Estadísticas de rutas por zona
CREATE OR REPLACE VIEW v_estadisticas_rutas AS
SELECT 
    zona,
    COUNT(*) AS total_rutas,
    AVG(suma_gravedad) AS promedio_gravedad,
    AVG(costo_total) AS promedio_distancia,
    AVG(camiones_usados) AS promedio_camiones,
    COUNT(CASE WHEN estado = 'completada' THEN 1 END) AS rutas_completadas,
    COUNT(CASE WHEN estado = 'en_ejecucion' THEN 1 END) AS rutas_en_curso
FROM rutas_generadas
GROUP BY zona;

-- ============================================================================
-- FIN DE LA MIGRACIÓN
-- ============================================================================

-- Verificación final
DO $$
BEGIN
    RAISE NOTICE '✅ Migración completada exitosamente';
    RAISE NOTICE 'Tablas creadas: incidencias, rutas_generadas, rutas_detalle, puntos_fijos, config';
    RAISE NOTICE 'Vistas creadas: v_incidencias_pendientes_por_zona, v_estadisticas_rutas';
END $$;
