"""Tests unitarios del PropertyController.

Se testa el parseo de query params, la validación y el mapeo de excepciones
a códigos HTTP. El use case se mockea.
"""

import unittest
from unittest.mock import MagicMock

from services.property_service.controllers import PropertyController
from services.property_service.exceptions import RepositoryError
from services.property_service.models import (
    Property,
    PropertyFilters,
    PropertyStatus,
)
from services.property_service.use_cases import ListPropertiesResult


class PropertyControllerParsingTest(unittest.TestCase):
    def setUp(self):
        self.use_case = MagicMock()
        self.use_case.execute.return_value = ListPropertiesResult(count=0, results=[])
        self.controller = PropertyController(use_case=self.use_case)

    def test_no_filters_uses_defaults(self):
        response = self.controller.list_properties(query_params={})

        self.assertEqual(response.status, 200)
        called_with: PropertyFilters = self.use_case.execute.call_args.args[0]
        self.assertIsNone(called_with.year)
        self.assertIsNone(called_with.city)
        self.assertIsNone(called_with.status)
        self.assertEqual(called_with.limit, 50)
        self.assertEqual(called_with.offset, 0)

    def test_parses_all_filters(self):
        params = {
            "year": ["2020"],
            "city": ["Bogotá"],
            "status": ["en_venta"],
            "limit": ["10"],
            "offset": ["20"],
        }
        self.controller.list_properties(query_params=params)

        called_with: PropertyFilters = self.use_case.execute.call_args.args[0]
        self.assertEqual(called_with.year, 2020)
        self.assertEqual(called_with.city, "Bogotá")
        self.assertEqual(called_with.status, PropertyStatus.EN_VENTA)
        self.assertEqual(called_with.limit, 10)
        self.assertEqual(called_with.offset, 20)

    def test_invalid_status_returns_400(self):
        response = self.controller.list_properties(
            query_params={"status": ["alquilado"]}
        )
        self.assertEqual(response.status, 400)
        self.assertEqual(response.body["error"], "invalid_filter")

    def test_non_integer_year_returns_400(self):
        response = self.controller.list_properties(
            query_params={"year": ["dos mil veinte"]}
        )
        self.assertEqual(response.status, 400)

    def test_year_out_of_range_returns_400(self):
        response = self.controller.list_properties(
            query_params={"year": ["1500"]}
        )
        self.assertEqual(response.status, 400)

    def test_limit_over_max_returns_400(self):
        response = self.controller.list_properties(
            query_params={"limit": ["999999"]}
        )
        self.assertEqual(response.status, 400)

    def test_negative_offset_returns_400(self):
        response = self.controller.list_properties(
            query_params={"offset": ["-1"]}
        )
        self.assertEqual(response.status, 400)


class PropertyControllerErrorMappingTest(unittest.TestCase):
    def test_repository_error_returns_500(self):
        use_case = MagicMock()
        use_case.execute.side_effect = RepositoryError("boom")
        controller = PropertyController(use_case=use_case)

        response = controller.list_properties(query_params={})

        self.assertEqual(response.status, 500)
        self.assertEqual(response.body["error"], "internal_error")

    def test_successful_response_contains_results(self):
        use_case = MagicMock()
        use_case.execute.return_value = ListPropertiesResult(
            count=1,
            results=[
                Property(
                    address="Calle 1",
                    city="Bogotá",
                    status="en_venta",
                    price=100,
                    description="desc",
                )
            ],
        )
        controller = PropertyController(use_case=use_case)

        response = controller.list_properties(query_params={})

        self.assertEqual(response.status, 200)
        self.assertEqual(response.body["count"], 1)
        self.assertEqual(len(response.body["results"]), 1)
        self.assertEqual(response.body["results"][0]["address"], "Calle 1")


if __name__ == "__main__":
    unittest.main()
