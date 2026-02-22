-- Migración 007: Agregar columnas de centroide a rutas_generadas
-- Criterio de aceptación C5: Ruta candidata incluye centroide del cluster de incidencias
-- Fecha: 2025

-- Agregar columnas para el centroide geográfico del cluster de incidencias
ALTER TABLE rutas_generadas
    ADD COLUMN IF NOT EXISTS centroide_lat FLOAT,
    ADD COLUMN IF NOT EXISTS centroide_lon FLOAT;

-- Agregar clave de configuración para el radio de clustering (C4)
INSERT INTO config (clave, valor, descripcion)
VALUES 
    ('radio_clustering_km', '3.0', 'Radio máximo en km para agrupar incidencias con DBSCAN (C4)')
ON CONFLICT (clave) DO NOTHING;

-- Agregar clave de configuración para el intervalo de agrupación periódica (C1)
INSERT INTO config (clave, valor, descripcion)
VALUES 
    ('intervalo_agrupacion_minutos', '30', 'Intervalo en minutos para ejecutar agrupación automática de incidencias (C1)')
ON CONFLICT (clave) DO NOTHING;

-- Comentario en la tabla
COMMENT ON COLUMN rutas_generadas.centroide_lat IS 'Latitud del centroide geográfico del cluster de incidencias (C5)';
COMMENT ON COLUMN rutas_generadas.centroide_lon IS 'Longitud del centroide geográfico del cluster de incidencias (C5)';
