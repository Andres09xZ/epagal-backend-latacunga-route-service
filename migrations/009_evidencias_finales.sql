-- ============================================================
-- Migración 009: Tabla de evidencias de finalización
-- Historia de usuario: Finalización de reporte con evidencia
-- Fecha: 2026-02-22
-- ============================================================

-- Tabla principal de evidencias
CREATE TABLE IF NOT EXISTS evidencias_finales (
    id                    SERIAL PRIMARY KEY,
    incidencia_id         INTEGER NOT NULL
                              REFERENCES incidencias(id) ON DELETE CASCADE,
    foto_url              VARCHAR(500),
    comentario            TEXT,
    subido_por_usuario_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    timestamp             TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at            TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Índices para consultas frecuentes
CREATE INDEX IF NOT EXISTS idx_evidencias_incidencia
    ON evidencias_finales (incidencia_id);

CREATE INDEX IF NOT EXISTS idx_evidencias_timestamp
    ON evidencias_finales (timestamp DESC);

-- Restricción: toda evidencia debe tener al menos foto o comentario
ALTER TABLE evidencias_finales
    ADD CONSTRAINT chk_evidencia_no_vacia
    CHECK (foto_url IS NOT NULL OR comentario IS NOT NULL);

-- Comentarios descriptivos
COMMENT ON TABLE evidencias_finales IS
    'Evidencias fotográficas y comentarios al finalizar una incidencia';
COMMENT ON COLUMN evidencias_finales.foto_url IS
    'URL de la foto de evidencia (antes/después). Puede ser local /fotos_incidencias/ o externo';
COMMENT ON COLUMN evidencias_finales.comentario IS
    'Descripción de la acción realizada, ej: "Se removió el animal muerto y se sanitizó el área"';
COMMENT ON COLUMN evidencias_finales.subido_por_usuario_id IS
    'ID del operador/conductor que registró la evidencia';
COMMENT ON COLUMN evidencias_finales.timestamp IS
    'Momento exacto en que se registró la evidencia';
