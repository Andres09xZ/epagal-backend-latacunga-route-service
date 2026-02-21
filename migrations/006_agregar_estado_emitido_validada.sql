-- Migración 006: Ampliar CHECK constraint de estado en tabla incidencias
-- Agrega los valores 'emitido' y 'validada' al constraint check_estado
-- Necesario para el flujo ciudadano (estado inicial 'emitido') y el flujo
-- de validación municipal ('validada' antes de asignarse a un conductor)
--
-- Estados completos tras esta migración:
--   emitido → pendiente → validada → asignada → completada | cancelada

-- 1. Eliminar el constraint actual
ALTER TABLE incidencias DROP CONSTRAINT IF EXISTS check_estado;
ALTER TABLE incidencias DROP CONSTRAINT IF EXISTS incidencias_estado_check;

-- 2. Agregar el constraint actualizado con todos los estados del ciclo de vida
ALTER TABLE incidencias
    ADD CONSTRAINT check_estado
    CHECK (estado IN ('emitido', 'pendiente', 'validada', 'asignada', 'completada', 'cancelada'));

-- 3. Ampliar el campo estado a VARCHAR(20) por si acaso
ALTER TABLE incidencias ALTER COLUMN estado TYPE VARCHAR(20);

-- 4. Actualizar el DEFAULT al nuevo estado inicial
ALTER TABLE incidencias ALTER COLUMN estado SET DEFAULT 'emitido';

-- Verificación
DO $$
BEGIN
    RAISE NOTICE 'Migración 006 aplicada: check_estado ahora acepta emitido, pendiente, validada, asignada, completada, cancelada';
END $$;
