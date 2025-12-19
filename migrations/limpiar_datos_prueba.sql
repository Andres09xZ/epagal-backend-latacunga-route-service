-- Script para limpiar toda la base de datos
-- Mantiene solo el usuario administrador
-- Autor: Sistema EPAGAL
-- Fecha: 2025-12-18

-- Desactivar constraints temporalmente
SET session_replication_role = 'replica';

-- 1. Eliminar todas las asignaciones de conductores
DELETE FROM asignaciones_conductores;
ALTER SEQUENCE asignaciones_conductores_id_seq RESTART WITH 1;

-- 2. Eliminar todas las rutas generadas
DELETE FROM rutas_generadas;
ALTER SEQUENCE rutas_generadas_id_seq RESTART WITH 1;

-- 3. Eliminar todos los puntos de ruta
DELETE FROM puntos_ruta;
ALTER SEQUENCE puntos_ruta_id_seq RESTART WITH 1;

-- 4. Eliminar todas las incidencias
DELETE FROM incidencias;
ALTER SEQUENCE incidencias_id_seq RESTART WITH 1;

-- 5. Eliminar todos los conductores
DELETE FROM conductores;
ALTER SEQUENCE conductores_id_seq RESTART WITH 1;

-- 6. Eliminar todos los usuarios EXCEPTO el admin
DELETE FROM usuarios WHERE tipo_usuario != 'admin';

-- 7. Verificar que el admin existe, si no, crearlo
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE username = 'admin') THEN
        INSERT INTO usuarios (username, email, password_hash, tipo_usuario, activo, created_at)
        VALUES (
            'admin',
            'admin@epagal.gob.ec',
            '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeEKkDl.LF/7RDqZe', -- password: admin123
            'admin',
            true,
            NOW()
        );
    END IF;
END $$;

-- Reactivar constraints
SET session_replication_role = 'origin';

-- Mostrar resumen
SELECT 
    'Limpieza completada' as mensaje,
    (SELECT COUNT(*) FROM incidencias) as incidencias_restantes,
    (SELECT COUNT(*) FROM rutas_generadas) as rutas_restantes,
    (SELECT COUNT(*) FROM conductores) as conductores_restantes,
    (SELECT COUNT(*) FROM usuarios WHERE tipo_usuario = 'admin') as admins_restantes,
    (SELECT COUNT(*) FROM usuarios WHERE tipo_usuario != 'admin') as otros_usuarios;

-- Verificar usuario admin
SELECT 
    id, 
    username, 
    email, 
    tipo_usuario, 
    activo 
FROM usuarios 
WHERE tipo_usuario = 'admin';
