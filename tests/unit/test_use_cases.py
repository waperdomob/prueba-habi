"""Tests unitarios del use case ListVisiblePropertiesUseCase.

El use case se testa con un repositorio falso (in-memory) para aislar la
lógica de negocio de la base de datos.
"""

import unittest
from unittest.mock import MagicMock

from services.property_service.models import Property, PropertyFilters, PropertyStatus
from services.property_service.use_cases import ListVisiblePropertiesUseCase


def _make_property(
    address: str = "Calle 1",
    city: str = "Bogotá",
    status: str = "en_venta",
    price: int = 100_000_000,
    description: str = "Descripción",
) -> Property:
    return Property(
        address=address,
        city=city,
        status=status,
        price=price,
        description=description,
    )


class ListVisiblePropertiesUseCaseTest(unittest.TestCase):
    def test_returns_properties_with_count(self):
        repo = MagicMock()
        repo.list_visible.return_value = [
            _make_property(address="Calle 1"),
            _make_property(address="Calle 2"),
        ]
        use_case = ListVisiblePropertiesUseCase(repository=repo)

        result = use_case.execute(PropertyFilters())

        self.assertEqual(result.count, 2)
        self.assertEqual(len(result.results), 2)
        self.assertEqual(result.results[0].address, "Calle 1")

    def test_returns_empty_result_when_repository_is_empty(self):
        repo = MagicMock()
        repo.list_visible.return_value = []
        use_case = ListVisiblePropertiesUseCase(repository=repo)

        result = use_case.execute(PropertyFilters())

        self.assertEqual(result.count, 0)
        self.assertEqual(result.results, [])

    def test_passes_filters_to_repository(self):
        repo = MagicMock()
        repo.list_visible.return_value = []
        use_case = ListVisiblePropertiesUseCase(repository=repo)

        filters = PropertyFilters(
            year=2020,
            city="Medellín",
            status=PropertyStatus.PRE_VENTA,
            limit=10,
            offset=5,
        )
        use_case.execute(filters)

        repo.list_visible.assert_called_once_with(filters)

    def test_result_serializes_to_expected_dict(self):
        repo = MagicMock()
        repo.list_visible.return_value = [
            _make_property(
                address="Cra 10 # 20-30",
                city="Bogotá",
                status="vendido",
                price=250_000_000,
                description="Casa con patio",
            )
        ]
        use_case = ListVisiblePropertiesUseCase(repository=repo)

        result = use_case.execute(PropertyFilters())
        payload = result.to_dict()

        self.assertEqual(payload["count"], 1)
        self.assertEqual(
            payload["results"][0],
            {
                "address": "Cra 10 # 20-30",
                "city": "Bogotá",
                "status": "vendido",
                "price": 250_000_000,
                "description": "Casa con patio",
            },
        )


if __name__ == "__main__":
    unittest.main()
