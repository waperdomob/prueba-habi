"""Casos de uso del Servicio 1.

Esta capa contiene la lógica de negocio y es testeable de forma aislada:
recibe un repositorio (puede ser real o un mock) y orquesta la operación.
No conoce HTTP, JSON, ni MySQL.
"""

from dataclasses import dataclass

from services.property_service.models import Property, PropertyFilters
from services.property_service.repository import PropertyRepository


@dataclass(frozen=True)
class ListPropertiesResult:
    count: int
    results: list[Property]

    def to_dict(self) -> dict:
        return {
            "count": self.count,
            "results": [p.to_dict() for p in self.results],
        }


class ListVisiblePropertiesUseCase:
    """Lista los inmuebles visibles que cumplen los filtros dados.

    Regla de negocio: un inmueble es visible si su último registro en
    status_history está en {pre_venta, en_venta, vendido}. El repositorio
    es quien garantiza esta regla a nivel de query.
    """

    def __init__(self, repository: PropertyRepository):
        self._repository = repository

    def execute(self, filters: PropertyFilters) -> ListPropertiesResult:
        properties = self._repository.list_visible(filters)
        return ListPropertiesResult(
            count=len(properties),
            results=properties,
        )
