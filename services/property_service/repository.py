"""Acceso a datos para el Servicio 1.

Todas las queries usan parámetros enlazados (nunca concatenación) para evitar
inyección SQL. El repositorio expone una interfaz pequeña y enfocada:
listar inmuebles visibles aplicando filtros.
"""

import logging
from typing import Optional

from mysql.connector import Error as MySQLError

from database.connection import get_connection
from services.property_service.exceptions import RepositoryError
from services.property_service.models import Property, PropertyFilters, PropertyStatus

logger = logging.getLogger(__name__)


# Estados que el usuario externo puede ver. Constante a nivel de módulo para
# que sea sencillo revisarla y cambiarla si las reglas de negocio evolucionan.
_VISIBLE_STATUSES = tuple(s.value for s in PropertyStatus)


# Query base. Para cada inmueble obtiene su ÚLTIMO registro en status_history
# (desempate por id DESC en caso de empates en update_date) y une con la
# tabla catálogo status para filtrar por nombre.
#
# Diseño de la subquery:
#   - Se usa subquery correlacionado (en lugar de función de ventana) porque
#     es compatible con MySQL < 8.0 y produce un plan predecible con un
#     índice en status_history(property_id, update_date, id).
#   - Se une DESPUÉS contra status_history una sola vez por el sh.id
#     seleccionado, lo que evita hacer el lookup del nombre del estado
#     dentro de la subquery.
#
# Los filtros dinámicos (year, city, status) se agregan como placeholders.
_BASE_QUERY = """
    SELECT
        p.address      AS address,
        p.city         AS city,
        s.name         AS status,
        p.price        AS price,
        p.description  AS description
    FROM property p
    INNER JOIN status_history sh
        ON sh.id = (
            SELECT sh2.id
            FROM status_history sh2
            WHERE sh2.property_id = p.id
            ORDER BY sh2.update_date DESC, sh2.id DESC
            LIMIT 1
        )
    INNER JOIN status s
        ON s.id = sh.status_id
    WHERE s.name IN ({visible_statuses_placeholders})
"""


class PropertyRepository:
    """Repositorio de inmuebles. Encapsula todo el acceso a la DB del Servicio 1."""

    def list_visible(self, filters: PropertyFilters) -> list[Property]:
        """Devuelve los inmuebles visibles que cumplen los filtros dados.

        Maneja inconsistencias de datos a nivel de fila: si una fila tiene
        campos críticos en null o con tipos inválidos, se omite con un log
        de advertencia en lugar de romper toda la respuesta.
        """
        query, params = self._build_query(filters)

        try:
            with get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(query, params)
                rows = cursor.fetchall()
                cursor.close()
        except MySQLError as exc:
            logger.exception("Error consultando inmuebles: %s", exc)
            raise RepositoryError("Error consultando la base de datos") from exc

        return self._map_rows(rows)

    # --- helpers privados ---

    def _build_query(
        self, filters: PropertyFilters
    ) -> tuple[str, tuple]:
        """Construye la query y sus parámetros a partir de los filtros.

        El orden de los parámetros importa — sigue el orden de aparición en
        la query (IN de estados visibles, luego filtros dinámicos, luego
        limit/offset).
        """
        placeholders = ", ".join(["%s"] * len(_VISIBLE_STATUSES))
        sql_parts = [_BASE_QUERY.format(visible_statuses_placeholders=placeholders)]
        params: list = list(_VISIBLE_STATUSES)

        if filters.year is not None:
            sql_parts.append("AND p.year = %s")
            params.append(filters.year)

        if filters.city:
            # Comparación case-insensitive por UX: el usuario no debería
            # fallar al buscar "Bogotá" vs "bogota". Los datos de ejemplo
            # muestran ciudades en minúscula sin tilde, así que esto también
            # tolera diferencias si la collation de MySQL es _ci (case
            # insensitive), que es el default habitual.
            sql_parts.append("AND LOWER(p.city) = LOWER(%s)")
            params.append(filters.city)

        if filters.status is not None:
            sql_parts.append("AND s.name = %s")
            params.append(filters.status.value)

        # Orden estable para que la paginación sea determinista.
        sql_parts.append("ORDER BY p.id ASC")
        sql_parts.append("LIMIT %s OFFSET %s")
        params.extend([filters.limit, filters.offset])

        return "\n".join(sql_parts), tuple(params)

    def _map_rows(self, rows: list[dict]) -> list[Property]:
        """Convierte filas del cursor a objetos Property, saltando filas corruptas.

        Inconsistencias toleradas: precio o descripción en null (se conservan
        como null en la respuesta porque el inmueble sigue siendo relevante).
        Inconsistencias que causan exclusión: dirección, ciudad o estado en null
        o vacíos, porque sin esos campos el inmueble no es útil.
        """
        result: list[Property] = []
        for row in rows:
            try:
                address = (row.get("address") or "").strip()
                city = (row.get("city") or "").strip()
                status = (row.get("status") or "").strip()

                if not address or not city or not status:
                    logger.warning(
                        "Fila omitida por datos incompletos: %s", row
                    )
                    continue

                price = self._coerce_optional_int(row.get("price"))
                description = row.get("description")
                if description is not None:
                    description = str(description).strip() or None

                result.append(
                    Property(
                        address=address,
                        city=city,
                        status=status,
                        price=price,
                        description=description,
                    )
                )
            except Exception as exc:
                # Nunca dejar que una fila corrupta tumbe la respuesta completa.
                logger.warning("Error mapeando fila %s: %s", row, exc)
                continue

        return result

    @staticmethod
    def _coerce_optional_int(value) -> Optional[int]:
        """Convierte a int si es posible; devuelve None si no (null, vacío o negativo)."""
        if value is None:
            return None
        try:
            as_int = int(value)
        except (TypeError, ValueError):
            return None
        if as_int < 0:
            # Precio negativo es dato inconsistente; lo tratamos como faltante.
            return None
        return as_int
