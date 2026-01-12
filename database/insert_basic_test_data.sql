-- ============================================
-- DATOS DE PRUEBA BÁSICOS - EPAGAL Latacunga
-- Solo Sectores y Horarios (sin dependencias)
-- ============================================

-- 1. CREAR SECTORES DE EJEMPLO
INSERT INTO sectores (nombre, zona, poligono, coordenadas_centro, poblacion_estimada, cantidad_viviendas, activo) 
VALUES
(
    'Centro Histórico',
    'occidental',
    ST_GeomFromText('POLYGON((-78.617 -0.933, -78.615 -0.933, -78.615 -0.935, -78.617 -0.935, -78.617 -0.933))', 4326),
    ST_GeomFromText('POINT(-78.616 -0.934)', 4326),
    5000,
    1200,
    true
),
(
    'La Laguna',
    'occidental',
    ST_GeomFromText('POLYGON((-78.620 -0.930, -78.618 -0.930, -78.618 -0.932, -78.620 -0.932, -78.620 -0.930))', 4326),
    ST_GeomFromText('POINT(-78.619 -0.931)', 4326),
    3500,
    850,
    true
),
(
    'San Felipe',
    'oriental',
    ST_GeomFromText('POLYGON((-78.625 -0.928, -78.623 -0.928, -78.623 -0.930, -78.625 -0.930, -78.625 -0.928))', 4326),
    ST_GeomFromText('POINT(-78.624 -0.929)', 4326),
    4200,
    1000,
    true
),
(
    'Eloy Alfaro',
    'oriental',
    ST_GeomFromText('POLYGON((-78.612 -0.936, -78.610 -0.936, -78.610 -0.938, -78.612 -0.938, -78.612 -0.936))', 4326),
    ST_GeomFromText('POINT(-78.611 -0.937)', 4326),
    6000,
    1500,
    true
)
ON CONFLICT (nombre) DO NOTHING;

-- 2. CREAR HORARIOS DE RECOLECCIÓN
-- Nota: Requiere que exista al menos un conductor en la tabla conductores

-- Horario 1: Lunes, Miércoles, Viernes - Centro Histórico
INSERT INTO horarios_recoleccion (
    sector_id, 
    dias_semana, 
    hora_inicio, 
    hora_fin, 
    frecuencia, 
    tipo_residuo,
    camion_placa,
    ruta_optimizada,
    distancia_km,
    tiempo_estimado,
    activo,
    created_at
)
SELECT 
    s.id,
    ARRAY[1, 3, 5],
    '07:00:00'::time,
    '12:00:00'::time,
    'semanal',
    'organico',
    'ABC-1234',
    ST_GeomFromText('LINESTRING(-78.617 -0.933, -78.616 -0.934, -78.615 -0.935)', 4326),
    5.5,
    INTERVAL '2 hours 30 minutes',
    true,
    NOW()
FROM sectores s
WHERE s.nombre = 'Centro Histórico'
LIMIT 1
ON CONFLICT DO NOTHING;

-- Horario 2: Martes, Jueves - La Laguna
INSERT INTO horarios_recoleccion (
    sector_id, 
    dias_semana, 
    hora_inicio, 
    hora_fin, 
    frecuencia, 
    tipo_residuo,
    camion_placa,
    ruta_optimizada,
    distancia_km,
    tiempo_estimado,
    activo,
    created_at
)
SELECT 
    s.id,
    ARRAY[2, 4],
    '08:00:00'::time,
    '13:00:00'::time,
    'semanal',
    'reciclable',
    'XYZ-5678',
    ST_GeomFromText('LINESTRING(-78.620 -0.930, -78.619 -0.931, -78.618 -0.932)', 4326),
    4.2,
    INTERVAL '2 hours',
    true,
    NOW()
FROM sectores s
WHERE s.nombre = 'La Laguna'
LIMIT 1
ON CONFLICT DO NOTHING;

-- Horario 3: Lunes a Viernes - San Felipe
INSERT INTO horarios_recoleccion (
    sector_id, 
    dias_semana, 
    hora_inicio, 
    hora_fin, 
    frecuencia, 
    tipo_residuo,
    camion_placa,
    ruta_optimizada,
    distancia_km,
    tiempo_estimado,
    activo,
    created_at
)
SELECT 
    s.id,
    ARRAY[1, 2, 3, 4, 5],
    '06:30:00'::time,
    '11:30:00'::time,
    'diaria',
    'comun',
    'DEF-9012',
    ST_GeomFromText('LINESTRING(-78.625 -0.928, -78.624 -0.929, -78.623 -0.930)', 4326),
    6.8,
    INTERVAL '3 hours',
    true,
    NOW()
FROM sectores s
WHERE s.nombre = 'San Felipe'
LIMIT 1
ON CONFLICT DO NOTHING;

-- Horario 4: Miércoles, Sábado - Eloy Alfaro
INSERT INTO horarios_recoleccion (
    sector_id, 
    dias_semana, 
    hora_inicio, 
    hora_fin, 
    frecuencia, 
    tipo_residuo,
    camion_placa,
    ruta_optimizada,
    distancia_km,
    tiempo_estimado,
    activo,
    created_at
)
SELECT 
    s.id,
    ARRAY[3, 6],
    '07:30:00'::time,
    '12:30:00'::time,
    'semanal',
    'organico',
    'GHI-3456',
    ST_GeomFromText('LINESTRING(-78.612 -0.936, -78.611 -0.937, -78.610 -0.938)', 4326),
    5.0,
    INTERVAL '2 hours 15 minutes',
    true,
    NOW()
FROM sectores s
WHERE s.nombre = 'Eloy Alfaro'
LIMIT 1
ON CONFLICT DO NOTHING;

-- ============================================
-- VERIFICACIÓN
-- ============================================

SELECT 'SECTORES INSERTADOS:' as resultado, COUNT(*) as total FROM sectores;
SELECT id, nombre, zona, activo FROM sectores ORDER BY nombre;

SELECT 'HORARIOS INSERTADOS:' as resultado, COUNT(*) as total FROM horarios_recoleccion;
SELECT h.id, s.nombre as sector, array_to_string(h.dias_semana, ',') as dias, h.tipo_residuo, h.camion_placa
FROM horarios_recoleccion h
JOIN sectores s ON h.sector_id = s.id
ORDER BY h.id;
