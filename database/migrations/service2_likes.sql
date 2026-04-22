-- =============================================================================
-- Servicio 2 — Extensión del modelo para el sistema de "Me gusta"
-- =============================================================================
-- Este script extiende el modelo actual para soportar:
--   1. Registrar "Me gusta" de usuarios autenticados sobre inmuebles.
--   2. Consultar el histórico completo de likes por usuario.
--   3. Generar un ranking interno de popularidad de inmuebles.
--
-- Decisiones de diseño (ver README para justificación completa):
--   - Se reutiliza la tabla `auth_user` existente (sistema de usuarios de
--     Django que ya está presente en la base de datos).
--   - No se agrega un contador desnormalizado de likes en `property` (ese
--     cambio se propone por separado en el Extra 3 como optimización).
--   - UNIQUE(user_id, property_id) previene likes duplicados y acelera el
--     lookup "¿este usuario ya dio like a este inmueble?".
-- =============================================================================


-- Tabla de likes.
-- Cada fila representa un "Me gusta" activo de un usuario sobre un inmueble.
-- Si un usuario retira el like, la fila se elimina.
CREATE TABLE IF NOT EXISTS property_like (
    id           INT           NOT NULL AUTO_INCREMENT,
    user_id      INT           NOT NULL,
    property_id  INT           NOT NULL,
    created_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),

    -- Un usuario no puede dar like al mismo inmueble más de una vez.
    -- Este índice también sirve para el lookup "¿ya dio like?" que hace la UI.
    CONSTRAINT uq_property_like__user_property
        UNIQUE (user_id, property_id),

    -- Índice para acelerar el ranking de popularidad:
    --   SELECT property_id, COUNT(*) FROM property_like GROUP BY property_id
    -- El índice permite que el motor haga un index scan en lugar de un
    -- full table scan.
    INDEX idx_property_like__property_id (property_id),

    -- Integridad referencial. Si se elimina un usuario o un inmueble,
    -- sus likes también se eliminan (no tiene sentido mantener likes
    -- "huérfanos" que no se pueden consultar ni mostrar).
    CONSTRAINT fk_property_like__user
        FOREIGN KEY (user_id) REFERENCES auth_user (id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    CONSTRAINT fk_property_like__property
        FOREIGN KEY (property_id) REFERENCES property (id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =============================================================================
-- Queries representativas (ejemplos, no forman parte del DDL)
-- =============================================================================

-- 1. Dar like (idempotente gracias al UNIQUE; si ya existe, no inserta).
--    La autenticación del usuario ocurre a nivel de aplicación (JWT/sesión);
--    el user_id se extrae del token y se pasa aquí.
--
-- INSERT IGNORE INTO property_like (user_id, property_id) VALUES (?, ?);


-- 2. Quitar like.
--
-- DELETE FROM property_like WHERE user_id = ? AND property_id = ?;


-- 3. Histórico de likes de un usuario (ordenado del más reciente al más antiguo).
--
-- SELECT
--     pl.id,
--     pl.property_id,
--     p.address,
--     p.city,
--     pl.created_at
-- FROM property_like pl
-- INNER JOIN property p ON p.id = pl.property_id
-- WHERE pl.user_id = ?
-- ORDER BY pl.created_at DESC, pl.id DESC
-- LIMIT ? OFFSET ?;


-- 4. Ranking de popularidad (top N inmuebles más gustados).
--    Se apoya en idx_property_like__property_id para evitar full scan.
--
-- SELECT
--     property_id,
--     COUNT(*) AS total_likes
-- FROM property_like
-- GROUP BY property_id
-- ORDER BY total_likes DESC
-- LIMIT ?;


-- 5. ¿Un usuario específico dio like a un inmueble específico?
--    Usa el UNIQUE index como covering index → lookup O(log n).
--
-- SELECT 1 FROM property_like
-- WHERE user_id = ? AND property_id = ?
-- LIMIT 1;
