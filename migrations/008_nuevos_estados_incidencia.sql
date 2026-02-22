-- ============================================================
-- Migración 008: Nuevos estados de incidencia
-- Flujo: emitido → recibido → validado → en_ejecucion → finalizado / rechazado
-- Fecha: 2026-02-22
-- ============================================================

-- 1. Eliminar el CHECK constraint anterior (si existe)
ALTER TABLE incidencias DROP CONSTRAINT IF EXISTS check_estado;

-- 2. Migrar datos existentes al nuevo esquema de estados
UPDATE incidencias SET estado = 'emitido'      WHERE estado = 'emitido';
UPDATE incidencias SET estado = 'recibido'     WHERE estado = 'pendiente';
UPDATE incidencias SET estado = 'validado'     WHERE estado = 'validada';
UPDATE incidencias SET estado = 'en_ejecucion' WHERE estado = 'asignada';
UPDATE incidencias SET estado = 'finalizado'   WHERE estado = 'completada';
UPDATE incidencias SET estado = 'rechazado'    WHERE estado = 'cancelada';

-- 3. Agregar el nuevo CHECK constraint
ALTER TABLE incidencias
    ADD CONSTRAINT check_estado
    CHECK (estado IN ('emitido', 'recibido', 'validado', 'en_ejecucion', 'finalizado', 'rechazado'));

-- 4. Verificar resultado
SELECT estado, COUNT(*) as cantidad
FROM incidencias
GROUP BY estado
ORDER BY estado;
