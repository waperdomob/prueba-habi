-- =============================================================================
-- Extra 3 — Modelo de datos mejorado (optimizado para velocidad de consulta)
-- =============================================================================
-- Este script propone un rediseño sobre el esquema actual que mejora
-- significativamente el rendimiento de las consultas del Servicio 1 y del
-- ranking de likes del Servicio 2, a costa de un pequeño overhead en las
-- escrituras (triggers de sincronización).
--
-- El enfoque es DESNORMALIZACIÓN ESTRATÉGICA sobre las tablas existentes,
-- no un modelo completamente nuevo. Se mantiene la fuente de verdad
-- (status_history, property_like) y se añaden columnas cacheadas
-- sincronizadas vía triggers. Justificación completa en el README.
--
-- IMPORTANTE: este script asume que la tabla property_like ya existe
-- (se crea en service2_likes.sql).
-- =============================================================================


-- -----------------------------------------------------------------------------
-- 1. Columnas denormalizadas en `property`
-- -----------------------------------------------------------------------------

-- current_status_id: FK al status actual. Evita el subquery correlacionado
-- del Servicio 1. NULL se permite temporalmente para inmuebles sin historial;
-- el filtro del Servicio 1 igualmente los excluye (WHERE s.name IN (...)).
ALTER TABLE property
    ADD COLUMN current_status_id INT NULL AFTER year,
    ADD CONSTRAINT fk_property__current_status
        FOREIGN KEY (current_status_id) REFERENCES status (id)
        ON DELETE SET NULL ON UPDATE CASCADE;

-- likes_count: contador desnormalizado. DEFAULT 0 y NOT NULL para que
-- siempre sea seguro ordenar por esta columna sin preocuparse por NULLs.
ALTER TABLE property
    ADD COLUMN likes_count INT NOT NULL DEFAULT 0 AFTER current_status_id;


-- -----------------------------------------------------------------------------
-- 2. Índices compuestos orientados a los patrones reales de consulta
-- -----------------------------------------------------------------------------

-- Cubre la consulta más común del Servicio 1: filtros combinados de estado
-- + ciudad + año. El orden de columnas sigue la regla general: columnas con
-- mayor selectividad o que aparecen en más queries van primero.
--   - current_status_id: siempre se filtra (por los 3 estados visibles).
--   - city: filtro frecuente de alta selectividad.
--   - year: filtro opcional.
CREATE INDEX idx_property_search
    ON property (current_status_id, city, year);

-- Ranking de popularidad: ORDER BY likes_count DESC LIMIT N se resuelve
-- con un reverse index scan en O(log n).
CREATE INDEX idx_property_ranking
    ON property (likes_count);

-- Filtro aislado por año (cuando el usuario no combina con estado/ciudad).
CREATE INDEX idx_property_year
    ON property (year);


-- -----------------------------------------------------------------------------
-- 3. Triggers de sincronización
-- -----------------------------------------------------------------------------

-- Al insertar un nuevo registro en status_history, actualizar el
-- current_status_id del inmueble. Esto implementa la regla "el estado actual
-- es el último registro insertado" directamente a nivel de DB, sin depender
-- de subqueries en tiempo de lectura.
DELIMITER //

CREATE TRIGGER trg_status_history_after_insert
AFTER INSERT ON status_history
FOR EACH ROW
BEGIN
    UPDATE property
    SET current_status_id = NEW.status_id
    WHERE id = NEW.property_id;
END //

-- Al borrar un registro de status_history, recalcular el current_status_id
-- a partir del nuevo "último" registro. Caso borde poco frecuente pero
-- importante para mantener consistencia si se limpian datos.
CREATE TRIGGER trg_status_history_after_delete
AFTER DELETE ON status_history
FOR EACH ROW
BEGIN
    UPDATE property p
    SET p.current_status_id = (
        SELECT sh.status_id
        FROM status_history sh
        WHERE sh.property_id = OLD.property_id
        ORDER BY sh.update_date DESC, sh.id DESC
        LIMIT 1
    )
    WHERE p.id = OLD.property_id;
END //

-- Mantener likes_count sincronizado ante inserciones en property_like.
CREATE TRIGGER trg_property_like_after_insert
AFTER INSERT ON property_like
FOR EACH ROW
BEGIN
    UPDATE property
    SET likes_count = likes_count + 1
    WHERE id = NEW.property_id;
END //

-- Mantener likes_count sincronizado ante eliminaciones en property_like.
CREATE TRIGGER trg_property_like_after_delete
AFTER DELETE ON property_like
FOR EACH ROW
BEGIN
    UPDATE property
    SET likes_count = GREATEST(likes_count - 1, 0)
    WHERE id = OLD.property_id;
END //

DELIMITER ;


-- -----------------------------------------------------------------------------
-- 4. Script de carga inicial (backfill)
-- -----------------------------------------------------------------------------
-- Después de aplicar las migraciones, se deben poblar las nuevas columnas
-- con los valores actuales. Estas queries se corren UNA sola vez.

-- Poblar current_status_id con el último estado de cada inmueble.
UPDATE property p
SET p.current_status_id = (
    SELECT sh.status_id
    FROM status_history sh
    WHERE sh.property_id = p.id
    ORDER BY sh.update_date DESC, sh.id DESC
    LIMIT 1
);

-- Poblar likes_count con el conteo actual.
UPDATE property p
SET p.likes_count = (
    SELECT COUNT(*)
    FROM property_like pl
    WHERE pl.property_id = p.id
);


-- -----------------------------------------------------------------------------
-- 5. Script de reconciliación (para mantenimiento)
-- -----------------------------------------------------------------------------
-- Las mismas queries del paso 4 se pueden correr periódicamente (p.ej.
-- semanalmente como job de mantenimiento) para detectar y corregir
-- desviaciones si un trigger fallara. Idealmente deben producir 0 filas
-- afectadas; si no, hay un problema que investigar.


-- -----------------------------------------------------------------------------
-- 6. Servicio 1 después del rediseño (query equivalente, mucho más rápida)
-- -----------------------------------------------------------------------------
--
-- SELECT
--     p.address,
--     p.city,
--     s.name AS status,
--     p.price,
--     p.description
-- FROM property p
-- INNER JOIN status s ON s.id = p.current_status_id
-- WHERE s.name IN ('pre_venta', 'en_venta', 'vendido')
--   AND p.city = ?       -- opcional
--   AND p.year = ?       -- opcional
-- ORDER BY p.id ASC
-- LIMIT ? OFFSET ?;
--
-- El índice idx_property_search cubre el WHERE completo. El subquery
-- correlacionado de la versión original desaparece.
--
-- -----------------------------------------------------------------------------
-- 7. Ranking de likes después del rediseño
-- -----------------------------------------------------------------------------
--
-- SELECT id, address, city, likes_count
-- FROM property
-- WHERE current_status_id IS NOT NULL
-- ORDER BY likes_count DESC
-- LIMIT 10;
--
-- Reverse index scan sobre idx_property_ranking: O(log n).
