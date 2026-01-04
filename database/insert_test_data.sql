-- ============================================
-- Script de datos de prueba para Horarios y Tracking
-- Sistema EPAGAL Latacunga
-- ============================================

-- Limpiar datos existentes (opcional)
-- DELETE FROM puntos_tracking_horario;
-- DELETE FROM ejecuciones_horario;
-- DELETE FROM horarios_recoleccion;
-- DELETE FROM sectores;

-- ============================================
-- 1. SECTORES
-- ============================================

INSERT INTO sectores (nombre, zona, descripcion, geometria, activo) VALUES
('Centro Histórico', 'Zona 1', 'Sector del centro de la ciudad', 
 ST_GeomFromText('POLYGON((-78.617 -0.933, -78.615 -0.933, -78.615 -0.935, -78.617 -0.935, -78.617 -0.933))', 4326),
 true),
 
('La Laguna', 'Zona 2', 'Barrio La Laguna y alrededores',
 ST_GeomFromText('POLYGON((-78.620 -0.930, -78.618 -0.930, -78.618 -0.932, -78.620 -0.932, -78.620 -0.930))', 4326),
 true),
 
('San Felipe', 'Zona 3', 'Sector San Felipe',
 ST_GeomFromText('POLYGON((-78.625 -0.928, -78.623 -0.928, -78.623 -0.930, -78.625 -0.930, -78.625 -0.928))', 4326),
 true),
 
('Eloy Alfaro', 'Zona 4', 'Barrio Eloy Alfaro',
 ST_GeomFromText('POLYGON((-78.612 -0.936, -78.610 -0.936, -78.610 -0.938, -78.612 -0.938, -78.612 -0.936))', 4326),
 true)
ON CONFLICT (nombre) DO NOTHING;

-- ============================================
-- 2. HORARIOS DE RECOLECCIÓN
-- ============================================

-- Lunes, Miércoles, Viernes - Centro Histórico
INSERT INTO horarios_recoleccion (
    sector_id, 
    dias_semana, 
    hora_inicio, 
    hora_fin, 
    frecuencia, 
    tipo_residuo,
    camion_placa,
    activo
) VALUES (
    (SELECT id FROM sectores WHERE nombre = 'Centro Histórico' LIMIT 1),
    ARRAY[1, 3, 5], -- Lunes, Miércoles, Viernes
    '07:00:00',
    '12:00:00',
    'semanal',
    'organico',
    'ABC-1234',
    true
)
ON CONFLICT DO NOTHING;

-- Martes, Jueves - La Laguna
INSERT INTO horarios_recoleccion (
    sector_id, 
    dias_semana, 
    hora_inicio, 
    hora_fin, 
    frecuencia, 
    tipo_residuo,
    camion_placa,
    activo
) VALUES (
    (SELECT id FROM sectores WHERE nombre = 'La Laguna' LIMIT 1),
    ARRAY[2, 4], -- Martes, Jueves
    '08:00:00',
    '13:00:00',
    'semanal',
    'reciclable',
    'XYZ-5678',
    true
)
ON CONFLICT DO NOTHING;

-- Lunes a Viernes - San Felipe
INSERT INTO horarios_recoleccion (
    sector_id, 
    dias_semana, 
    hora_inicio, 
    hora_fin, 
    frecuencia, 
    tipo_residuo,
    camion_placa,
    activo
) VALUES (
    (SELECT id FROM sectores WHERE nombre = 'San Felipe' LIMIT 1),
    ARRAY[1, 2, 3, 4, 5], -- Lunes a Viernes
    '06:30:00',
    '11:30:00',
    'diaria',
    'comun',
    'DEF-9012',
    true
)
ON CONFLICT DO NOTHING;

-- Miércoles, Sábado - Eloy Alfaro
INSERT INTO horarios_recoleccion (
    sector_id, 
    dias_semana, 
    hora_inicio, 
    hora_fin, 
    frecuencia, 
    tipo_residuo,
    camion_placa,
    activo
) VALUES (
    (SELECT id FROM sectores WHERE nombre = 'Eloy Alfaro' LIMIT 1),
    ARRAY[3, 6], -- Miércoles, Sábado
    '07:30:00',
    '12:30:00',
    'semanal',
    'organico',
    'GHI-3456',
    true
)
ON CONFLICT DO NOTHING;

-- ============================================
-- 3. EJECUCIONES ACTIVAS (para Tracking)
-- ============================================

-- Ejecución en curso - Centro Histórico
INSERT INTO ejecuciones_horario (
    horario_id,
    fecha_programada,
    conductor_id,
    camion_placa,
    estado,
    hora_inicio,
    observaciones
) VALUES (
    (SELECT id FROM horarios_recoleccion WHERE camion_placa = 'ABC-1234' LIMIT 1),
    CURRENT_DATE,
    (SELECT id FROM conductores WHERE estado = 'activo' LIMIT 1),
    'ABC-1234',
    'en_curso',
    NOW() - INTERVAL '30 minutes',
    'Ejecución de prueba en curso'
)
ON CONFLICT DO NOTHING;

-- Ejecución en curso - La Laguna
INSERT INTO ejecuciones_horario (
    horario_id,
    fecha_programada,
    conductor_id,
    camion_placa,
    estado,
    hora_inicio,
    observaciones
) VALUES (
    (SELECT id FROM horarios_recoleccion WHERE camion_placa = 'XYZ-5678' LIMIT 1),
    CURRENT_DATE,
    (SELECT id FROM conductores WHERE estado = 'activo' OFFSET 1 LIMIT 1),
    'XYZ-5678',
    'en_curso',
    NOW() - INTERVAL '45 minutes',
    'Ejecución de prueba en curso'
)
ON CONFLICT DO NOTHING;

-- ============================================
-- 4. PUNTOS DE TRACKING GPS
-- ============================================

-- Puntos GPS para la primera ejecución
INSERT INTO puntos_tracking_horario (
    ejecucion_id,
    ubicacion,
    velocidad,
    timestamp
)
SELECT 
    (SELECT id FROM ejecuciones_horario WHERE camion_placa = 'ABC-1234' AND estado = 'en_curso' ORDER BY hora_inicio DESC LIMIT 1),
    ST_GeomFromText('POINT(' || 
        -78.617 + (random() * 0.01 - 0.005) || ' ' || 
        -0.933 + (random() * 0.01 - 0.005) || 
    ')', 4326),
    15 + random() * 30,
    NOW() - INTERVAL '1 minute' * generate_series
FROM generate_series(1, 10);

-- Puntos GPS para la segunda ejecución
INSERT INTO puntos_tracking_horario (
    ejecucion_id,
    ubicacion,
    velocidad,
    timestamp
)
SELECT 
    (SELECT id FROM ejecuciones_horario WHERE camion_placa = 'XYZ-5678' AND estado = 'en_curso' ORDER BY hora_inicio DESC LIMIT 1),
    ST_GeomFromText('POINT(' || 
        -78.620 + (random() * 0.01 - 0.005) || ' ' || 
        -0.930 + (random() * 0.01 - 0.005) || 
    ')', 4326),
    10 + random() * 25,
    NOW() - INTERVAL '1 minute' * generate_series
FROM generate_series(1, 10);

-- ============================================
-- VERIFICACIÓN DE DATOS
-- ============================================

-- Ver sectores creados
SELECT 'SECTORES CREADOS:' as info;
SELECT id, nombre, zona, activo FROM sectores ORDER BY id;

-- Ver horarios creados
SELECT 'HORARIOS CREADOS:' as info;
SELECT h.id, s.nombre as sector, h.dias_semana, h.hora_inicio, h.hora_fin, h.tipo_residuo, h.camion_placa
FROM horarios_recoleccion h
JOIN sectores s ON h.sector_id = s.id
ORDER BY h.id;

-- Ver ejecuciones activas
SELECT 'EJECUCIONES ACTIVAS:' as info;
SELECT e.id, e.camion_placa, e.estado, e.hora_inicio, COUNT(p.id) as puntos_gps
FROM ejecuciones_horario e
LEFT JOIN puntos_tracking_horario p ON e.id = p.ejecucion_id
WHERE e.estado = 'en_curso'
GROUP BY e.id
ORDER BY e.id;

SELECT 'DATOS DE PRUEBA INSERTADOS CORRECTAMENTE' as resultado;
