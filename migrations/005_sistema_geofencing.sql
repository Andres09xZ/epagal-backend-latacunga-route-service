-- Migración 005: Sistema de Geofencing
-- Descripción: Tablas para monitoreo en tiempo real con alertas de desviación de ruta,
--              velocidad excesiva, paradas prolongadas y validación de zonas geográficas.
-- Fecha: 2025-01-09
-- Compatible con: Neon PostgreSQL (Serverless PostgreSQL)

-- ===================================================================
-- Habilitar PostGIS (si no está habilitado)
-- IMPORTANTE: En Neon, PostGIS debe estar habilitado desde la consola web
-- o usando: CREATE EXTENSION IF NOT EXISTS postgis CASCADE;
-- ===================================================================
CREATE EXTENSION IF NOT EXISTS postgis CASCADE;


-- ===================================================================
-- Configuración de Geofencing
-- ===================================================================
CREATE TABLE IF NOT EXISTS geofence_config (
    id SERIAL PRIMARY KEY,
    parametro VARCHAR(100) NOT NULL UNIQUE,
    valor NUMERIC(10, 2) NOT NULL,
    unidad VARCHAR(50),
    descripcion TEXT,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE geofence_config IS 'Configuración de parámetros del sistema de geofencing';
COMMENT ON COLUMN geofence_config.parametro IS 'Nombre del parámetro (ej: velocidad_maxima_kmh)';
COMMENT ON COLUMN geofence_config.valor IS 'Valor numérico del parámetro';
COMMENT ON COLUMN geofence_config.unidad IS 'Unidad de medida (km/h, metros, minutos)';


-- ===================================================================
-- Zonas Geográficas
-- ===================================================================
CREATE TABLE IF NOT EXISTS zonas_geograficas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    tipo VARCHAR(50) NOT NULL, -- 'cobertura', 'restriccion', 'zona_operativa'
    geometria GEOMETRY(POLYGON, 4326) NOT NULL,
    descripcion TEXT,
    activa BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE zonas_geograficas IS 'Polígonos de zonas geográficas para validación';
COMMENT ON COLUMN zonas_geograficas.tipo IS 'Tipo de zona: cobertura (EPAGAL), restriccion, zona_operativa (occidental/oriental)';
COMMENT ON COLUMN zonas_geograficas.geometria IS 'Geometría PostGIS en coordenadas WGS84 (EPSG:4326)';

-- Índice espacial para consultas rápidas
CREATE INDEX idx_zonas_geometria ON zonas_geograficas USING GIST (geometria);
CREATE INDEX idx_zonas_tipo ON zonas_geograficas (tipo);


-- ===================================================================
-- Historial de Posiciones GPS
-- ===================================================================
CREATE TABLE IF NOT EXISTS historial_posiciones (
    id SERIAL PRIMARY KEY,
    conductor_id INTEGER NOT NULL REFERENCES conductores(id) ON DELETE CASCADE,
    ruta_id INTEGER REFERENCES rutas(id) ON DELETE SET NULL,
    geometria GEOMETRY(POINT, 4326) NOT NULL,
    latitud NUMERIC(10, 7) NOT NULL,
    longitud NUMERIC(10, 7) NOT NULL,
    precision_m NUMERIC(6, 2),
    velocidad_kmh NUMERIC(5, 2),
    direccion_grados NUMERIC(5, 2),
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE historial_posiciones IS 'Registro histórico de todas las posiciones GPS reportadas';
COMMENT ON COLUMN historial_posiciones.precision_m IS 'Precisión horizontal del GPS en metros';
COMMENT ON COLUMN historial_posiciones.velocidad_kmh IS 'Velocidad instantánea reportada por GPS';
COMMENT ON COLUMN historial_posiciones.direccion_grados IS 'Dirección de movimiento (0-360 grados, 0=Norte)';

-- Índices para consultas de historial
CREATE INDEX idx_historial_conductor ON historial_posiciones (conductor_id);
CREATE INDEX idx_historial_ruta ON historial_posiciones (ruta_id);
CREATE INDEX idx_historial_timestamp ON historial_posiciones (timestamp DESC);
CREATE INDEX idx_historial_geometria ON historial_posiciones USING GIST (geometria);


-- ===================================================================
-- Alertas de Geofencing
-- ===================================================================
CREATE TABLE IF NOT EXISTS geofence_alerts (
    id SERIAL PRIMARY KEY,
    conductor_id INTEGER NOT NULL REFERENCES conductores(id) ON DELETE CASCADE,
    ruta_id INTEGER REFERENCES rutas(id) ON DELETE SET NULL,
    tipo VARCHAR(50) NOT NULL,
    severidad VARCHAR(20) NOT NULL,
    descripcion TEXT NOT NULL,
    geometria GEOMETRY(POINT, 4326) NOT NULL,
    latitud NUMERIC(10, 7) NOT NULL,
    longitud NUMERIC(10, 7) NOT NULL,
    velocidad_kmh NUMERIC(5, 2),
    distancia_desviacion_m NUMERIC(8, 2),
    tiempo_parada_min INTEGER,
    estado VARCHAR(20) DEFAULT 'activa',
    contador_recurrencia INTEGER DEFAULT 1,
    recomendaciones TEXT,
    timestamp TIMESTAMP NOT NULL,
    resuelta_at TIMESTAMP,
    resuelta_por VARCHAR(100),
    notas TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE geofence_alerts IS 'Registro de alertas generadas por el sistema de geofencing';
COMMENT ON COLUMN geofence_alerts.tipo IS 'Tipo: desviacion_ruta, velocidad_excesiva, parada_prolongada, fuera_zona_cobertura, zona_incorrecta, precision_gps_baja, salto_temporal';
COMMENT ON COLUMN geofence_alerts.severidad IS 'Nivel: low, medium, high, critical';
COMMENT ON COLUMN geofence_alerts.estado IS 'Estado: activa, resuelta, ignorada, escalada';
COMMENT ON COLUMN geofence_alerts.contador_recurrencia IS 'Número de veces que se ha generado la misma alerta en período reciente';

-- Índices para consultas de alertas
CREATE INDEX idx_alerts_conductor ON geofence_alerts (conductor_id);
CREATE INDEX idx_alerts_ruta ON geofence_alerts (ruta_id);
CREATE INDEX idx_alerts_tipo ON geofence_alerts (tipo);
CREATE INDEX idx_alerts_severidad ON geofence_alerts (severidad);
CREATE INDEX idx_alerts_estado ON geofence_alerts (estado);
CREATE INDEX idx_alerts_timestamp ON geofence_alerts (timestamp DESC);
CREATE INDEX idx_alerts_geometria ON geofence_alerts USING GIST (geometria);


-- ===================================================================
-- Estadísticas de Geofencing
-- ===================================================================
CREATE TABLE IF NOT EXISTS estadisticas_geofencing (
    id SERIAL PRIMARY KEY,
    conductor_id INTEGER NOT NULL REFERENCES conductores(id) ON DELETE CASCADE,
    periodo_inicio TIMESTAMP NOT NULL,
    periodo_fin TIMESTAMP NOT NULL,
    total_alertas INTEGER DEFAULT 0,
    alertas_desviacion INTEGER DEFAULT 0,
    alertas_velocidad INTEGER DEFAULT 0,
    alertas_parada INTEGER DEFAULT 0,
    alertas_zona INTEGER DEFAULT 0,
    alertas_gps INTEGER DEFAULT 0,
    distancia_total_km NUMERIC(10, 2) DEFAULT 0,
    velocidad_promedio_kmh NUMERIC(5, 2) DEFAULT 0,
    velocidad_maxima_kmh NUMERIC(5, 2) DEFAULT 0,
    tiempo_conduccion_horas NUMERIC(6, 2) DEFAULT 0,
    puntuacion_seguridad NUMERIC(3, 1) DEFAULT 100,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (conductor_id, periodo_inicio, periodo_fin)
);

COMMENT ON TABLE estadisticas_geofencing IS 'Estadísticas agregadas de desempeño de conductores';
COMMENT ON COLUMN estadisticas_geofencing.puntuacion_seguridad IS 'Puntuación de seguridad 0-100 (100=perfecto)';
COMMENT ON COLUMN estadisticas_geofencing.tiempo_conduccion_horas IS 'Tiempo total en movimiento (velocidad > 5 km/h)';

-- Índices para reportes
CREATE INDEX idx_stats_conductor ON estadisticas_geofencing (conductor_id);
CREATE INDEX idx_stats_periodo ON estadisticas_geofencing (periodo_inicio, periodo_fin);


-- ===================================================================
-- Insertar Configuración Por Defecto
-- ===================================================================
INSERT INTO geofence_config (parametro, valor, unidad, descripcion, activo) VALUES
    ('velocidad_maxima_kmh', 80, 'km/h', 'Velocidad máxima permitida para alerta', TRUE),
    ('velocidad_critica_kmh', 100, 'km/h', 'Velocidad crítica para alerta de alta severidad', TRUE),
    ('distancia_desviacion_m', 500, 'metros', 'Distancia máxima de desviación de ruta antes de alertar', TRUE),
    ('tiempo_parada_min', 15, 'minutos', 'Tiempo máximo de parada prolongada antes de alertar', TRUE),
    ('precision_minima_gps_m', 50, 'metros', 'Precisión mínima requerida del GPS', TRUE),
    ('ventana_recurrencia_min', 30, 'minutos', 'Ventana de tiempo para contar alertas recurrentes', TRUE),
    ('umbral_recurrencia', 3, 'veces', 'Número de recurrencias para escalar severidad', TRUE),
    ('velocidad_salto_temporal_kmh', 150, 'km/h', 'Velocidad requerida para detectar salto temporal anómalo', TRUE),
    ('distancia_parada_m', 50, 'metros', 'Distancia máxima para considerar vehículo detenido', TRUE),
    ('velocidad_minima_movimiento_kmh', 5, 'km/h', 'Velocidad mínima para considerar vehículo en movimiento', TRUE)
ON CONFLICT (parametro) DO NOTHING;


-- ===================================================================
-- Insertar Zonas Geográficas de EPAGAL
-- ===================================================================

-- Zona Occidental (San Felipe, La Matriz, Eloy Alfaro, Ignacio Flores)
INSERT INTO zonas_geograficas (nombre, tipo, geometria, descripcion, activa) VALUES
(
    'zona_occidental',
    'zona_operativa',
    ST_GeomFromText('POLYGON((
        -78.6300 -0.9250,
        -78.6300 -0.9450,
        -78.6100 -0.9450,
        -78.6100 -0.9250,
        -78.6300 -0.9250
    ))', 4326),
    'Zona occidental de Latacunga: San Felipe, La Matriz, Eloy Alfaro, Ignacio Flores',
    TRUE
),

-- Zona Oriental (Juan Montalvo, La Laguna)
(
    'zona_oriental',
    'zona_operativa',
    ST_GeomFromText('POLYGON((
        -78.6100 -0.9250,
        -78.6100 -0.9450,
        -78.5900 -0.9450,
        -78.5900 -0.9250,
        -78.6100 -0.9250
    ))', 4326),
    'Zona oriental de Latacunga: Juan Montalvo, La Laguna',
    TRUE
),

-- Área total de cobertura EPAGAL (combina ambas zonas)
(
    'cobertura_epagal',
    'cobertura',
    ST_GeomFromText('POLYGON((
        -78.6300 -0.9250,
        -78.6300 -0.9450,
        -78.5900 -0.9450,
        -78.5900 -0.9250,
        -78.6300 -0.9250
    ))', 4326),
    'Área total de cobertura de EPAGAL en Latacunga',
    TRUE
)
ON CONFLICT (nombre) DO NOTHING;


-- ===================================================================
-- Triggers para updated_at
-- ===================================================================

-- Función genérica para actualizar timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para geofence_config
CREATE TRIGGER update_geofence_config_updated_at
    BEFORE UPDATE ON geofence_config
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger para zonas_geograficas
CREATE TRIGGER update_zonas_geograficas_updated_at
    BEFORE UPDATE ON zonas_geograficas
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger para geofence_alerts
CREATE TRIGGER update_geofence_alerts_updated_at
    BEFORE UPDATE ON geofence_alerts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger para estadisticas_geofencing
CREATE TRIGGER update_estadisticas_geofencing_updated_at
    BEFORE UPDATE ON estadisticas_geofencing
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ===================================================================
-- Vistas útiles para reportes
-- ===================================================================

-- Vista de alertas activas con información del conductor
CREATE OR REPLACE VIEW alertas_activas_detalle AS
SELECT 
    a.id,
    a.conductor_id,
    c.nombre_completo AS conductor_nombre,
    c.zona_preferida AS zona_asignada,
    a.tipo,
    a.severidad,
    a.descripcion,
    a.latitud,
    a.longitud,
    a.velocidad_kmh,
    a.distancia_desviacion_m,
    a.tiempo_parada_min,
    a.contador_recurrencia,
    a.timestamp,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - a.timestamp))/60 AS minutos_desde_alerta
FROM geofence_alerts a
JOIN conductores c ON a.conductor_id = c.id
WHERE a.estado = 'activa'
ORDER BY a.severidad DESC, a.timestamp DESC;

COMMENT ON VIEW alertas_activas_detalle IS 'Vista de alertas activas con información detallada del conductor';


-- Vista de estadísticas mensuales por conductor
CREATE OR REPLACE VIEW estadisticas_mensuales AS
SELECT 
    e.conductor_id,
    c.nombre_completo AS conductor_nombre,
    c.zona_preferida AS zona_asignada,
    DATE_TRUNC('month', e.periodo_inicio) AS mes,
    SUM(e.total_alertas) AS total_alertas_mes,
    SUM(e.alertas_velocidad) AS alertas_velocidad_mes,
    SUM(e.alertas_desviacion) AS alertas_desviacion_mes,
    AVG(e.velocidad_promedio_kmh) AS velocidad_promedio_mes,
    MAX(e.velocidad_maxima_kmh) AS velocidad_maxima_mes,
    SUM(e.distancia_total_km) AS distancia_total_mes,
    SUM(e.tiempo_conduccion_horas) AS horas_conduccion_mes,
    AVG(e.puntuacion_seguridad) AS puntuacion_promedio_mes
FROM estadisticas_geofencing e
JOIN conductores c ON e.conductor_id = c.id
GROUP BY e.conductor_id, c.nombre_completo, c.zona_preferida, DATE_TRUNC('month', e.periodo_inicio)
ORDER BY mes DESC, total_alertas_mes DESC;

COMMENT ON VIEW estadisticas_mensuales IS 'Estadísticas agregadas mensuales por conductor';


-- ===================================================================
-- Funciones de utilidad PostGIS
-- ===================================================================

-- Función para verificar si un punto está dentro de una zona
CREATE OR REPLACE FUNCTION punto_en_zona(
    lat NUMERIC,
    lon NUMERIC,
    nombre_zona VARCHAR
)
RETURNS BOOLEAN AS $$
DECLARE
    punto GEOMETRY;
    zona GEOMETRY;
BEGIN
    punto := ST_SetSRID(ST_MakePoint(lon, lat), 4326);
    SELECT geometria INTO zona FROM zonas_geograficas 
    WHERE nombre = nombre_zona AND activa = TRUE;
    
    IF zona IS NULL THEN
        RETURN FALSE;
    END IF;
    
    RETURN ST_Contains(zona, punto);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION punto_en_zona IS 'Verifica si coordenadas lat/lon están dentro de una zona geográfica';


-- ===================================================================
-- Permisos (ajustar según usuario de la aplicación)
-- ===================================================================
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;


-- ===================================================================
-- Verificación de migración
-- ===================================================================
DO $$
BEGIN
    RAISE NOTICE 'Migración 005 completada exitosamente';
    RAISE NOTICE 'Tablas creadas: geofence_config, zonas_geograficas, historial_posiciones, geofence_alerts, estadisticas_geofencing';
    RAISE NOTICE 'Índices espaciales creados para consultas PostGIS eficientes';
    RAISE NOTICE 'Configuración por defecto insertada';
    RAISE NOTICE 'Zonas geográficas de EPAGAL insertadas (occidental, oriental, cobertura)';
END $$;
