"""Controller del Servicio 1.

Traduce entre el mundo HTTP (query strings, JSON, códigos de estado) y el
mundo de dominio (filtros, modelos, use cases). No ejecuta lógica de negocio.
"""

import json
import logging
from typing import Optional

from services.property_service.exceptions import InvalidFilterError, RepositoryError
from services.property_service.models import PropertyFilters, PropertyStatus
from services.property_service.use_cases import ListVisiblePropertiesUseCase

logger = logging.getLogger(__name__)


# Paginación: límites razonables para evitar que un cliente pida una página
# enorme y sature la DB o la memoria del servidor.
_DEFAULT_LIMIT = 50
_MAX_LIMIT = 200


class Response:
    """Estructura simple de respuesta HTTP: status + payload serializable."""

    __slots__ = ("status", "body")

    def __init__(self, status: int, body: dict):
        self.status = status
        self.body = body

    def to_json_bytes(self) -> bytes:
        return json.dumps(self.body, ensure_ascii=False).encode("utf-8")


class PropertyController:
    """Orquesta el flujo HTTP del endpoint GET /properties."""

    def __init__(self, use_case: ListVisiblePropertiesUseCase):
        self._use_case = use_case

    def list_properties(self, query_params: dict[str, list[str]]) -> Response:
        """Entry point del endpoint.

        query_params tiene el formato que produce urllib.parse.parse_qs:
        cada clave mapea a una lista de valores (aunque aquí solo usamos
        el primer valor de cada lista).
        """
        try:
            filters = self._parse_filters(query_params)
        except InvalidFilterError as exc:
            return Response(
                status=400,
                body={"error": "invalid_filter", "message": str(exc)},
            )

        try:
            result = self._use_case.execute(filters)
        except RepositoryError:
            # El detalle ya se logueó en el repository; no exponer al cliente.
            return Response(
                status=500,
                body={"error": "internal_error", "message": "Error interno del servidor"},
            )

        return Response(status=200, body=result.to_dict())

    # --- parsing ---

    def _parse_filters(self, params: dict[str, list[str]]) -> PropertyFilters:
        year = self._parse_optional_int(params, "year", minimum=1800, maximum=2100)
        city = self._parse_optional_str(params, "city", max_length=120)

        status_raw = self._first_value(params, "status")
        status = None
        if status_raw is not None:
            try:
                status = PropertyStatus.from_value(status_raw)
            except ValueError as exc:
                raise InvalidFilterError(str(exc)) from exc

        limit = self._parse_optional_int(params, "limit", minimum=1, maximum=_MAX_LIMIT)
        offset = self._parse_optional_int(params, "offset", minimum=0, maximum=10_000_000)

        return PropertyFilters(
            year=year,
            city=city,
            status=status,
            limit=limit if limit is not None else _DEFAULT_LIMIT,
            offset=offset if offset is not None else 0,
        )

    @staticmethod
    def _first_value(params: dict[str, list[str]], key: str) -> Optional[str]:
        values = params.get(key)
        if not values:
            return None
        value = values[0].strip()
        return value or None

    def _parse_optional_int(
        self,
        params: dict[str, list[str]],
        key: str,
        *,
        minimum: int,
        maximum: int,
    ) -> Optional[int]:
        raw = self._first_value(params, key)
        if raw is None:
            return None
        try:
            value = int(raw)
        except ValueError:
            raise InvalidFilterError(
                f"El parámetro '{key}' debe ser un entero. Valor recibido: '{raw}'."
            )
        if value < minimum or value > maximum:
            raise InvalidFilterError(
                f"El parámetro '{key}' debe estar entre {minimum} y {maximum}. "
                f"Valor recibido: {value}."
            )
        return value

    def _parse_optional_str(
        self,
        params: dict[str, list[str]],
        key: str,
        *,
        max_length: int,
    ) -> Optional[str]:
        value = self._first_value(params, key)
        if value is None:
            return None
        if len(value) > max_length:
            raise InvalidFilterError(
                f"El parámetro '{key}' excede la longitud máxima ({max_length})."
            )
        return value
