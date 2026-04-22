"""Router minimalista.

Mapea (método HTTP, path) a una función handler que recibe el contexto de
la request y devuelve una Response. No hay necesidad de patrones de URL
complejos en esta prueba (un solo recurso), así que el router es literal.
"""

from dataclasses import dataclass
from typing import Callable, Optional

from services.property_service.controllers import PropertyController, Response


@dataclass(frozen=True)
class RouteContext:
    """Datos que el router pasa al handler."""

    query_params: dict[str, list[str]]
    body: bytes


HandlerFn = Callable[[RouteContext], Response]


class Router:
    def __init__(self, property_controller: PropertyController):
        self._property_controller = property_controller
        self._routes: dict[tuple[str, str], HandlerFn] = {
            ("GET", "/properties"): self._handle_list_properties,
            ("GET", "/health"): self._handle_health,
        }

    def resolve(self, method: str, path: str) -> Optional[HandlerFn]:
        return self._routes.get((method.upper(), path))

    # --- handlers ---

    def _handle_list_properties(self, ctx: RouteContext) -> Response:
        return self._property_controller.list_properties(ctx.query_params)

    def _handle_health(self, ctx: RouteContext) -> Response:
        return Response(status=200, body={"status": "ok"})
