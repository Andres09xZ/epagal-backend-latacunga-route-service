-- Migración: Agregar estado 'asignada' a rutas_generadas
-- Fecha: 2025-12-19
-- Descripción: Diferencia entre ruta asignada y ruta iniciada

-- 1. Eliminar el constraint anterior
ALTER TABLE rutas_generadas DROP CONSTRAINT IF EXISTS check_ruta_estado;

-- 2. Agregar el nuevo constraint con estado 'asignada'
ALTER TABLE rutas_generadas ADD CONSTRAINT check_ruta_estado 
    CHECK (estado IN ('planeada', 'asignada', 'en_ejecucion', 'completada'));

-- 3. Actualizar rutas que están en_ejecucion pero el conductor no ha iniciado
-- (fecha_inicio es NULL) a estado 'asignada'
UPDATE rutas_generadas r
SET estado = 'asignada'
WHERE estado = 'en_ejecucion'
AND EXISTS (
    SELECT 1 FROM asignaciones_conductores ac
    WHERE ac.ruta_id = r.id
    AND ac.fecha_inicio IS NULL
);

-- Verificar los cambios
SELECT estado, COUNT(*) as total
FROM rutas_generadas
GROUP BY estado;
