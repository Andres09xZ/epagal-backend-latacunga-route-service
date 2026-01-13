-- Script para insertar puntos fijos si no existen
INSERT INTO puntos_fijos (nombre, tipo, lat, lon, geom, activo) VALUES
    ('Depósito EPAGAL', 'deposito', -0.936, -78.613, ST_SetSRID(ST_MakePoint(-78.613, -0.936), 4326), true),
    ('Botadero Inchapo', 'botadero', -0.949, -78.663, ST_SetSRID(ST_MakePoint(-78.663, -0.949), 4326), true)
ON CONFLICT (nombre) DO UPDATE SET activo = true;

-- Verificar
SELECT * FROM puntos_fijos;
