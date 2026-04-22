"""Tests del mapeo de filas del PropertyRepository.

No conectan a MySQL — se enfocan en la lógica de _map_rows y _coerce_optional_int,
que es donde vive el manejo de inconsistencias de datos.
"""

import unittest

from services.property_service.repository import PropertyRepository


class MapRowsTest(unittest.TestCase):
    def setUp(self):
        self.repo = PropertyRepository()

    def test_maps_a_valid_row(self):
        rows = [
            {
                "address": "Calle 1 # 2-3",
                "city": "Bogotá",
                "status": "en_venta",
                "price": 100_000_000,
                "description": "Apto con vista",
            }
        ]
        result = self.repo._map_rows(rows)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].address, "Calle 1 # 2-3")
        self.assertEqual(result[0].price, 100_000_000)

    def test_skips_rows_without_address(self):
        rows = [
            {"address": None, "city": "Bogotá", "status": "en_venta", "price": 1, "description": ""},
            {"address": "", "city": "Bogotá", "status": "en_venta", "price": 1, "description": ""},
            {"address": "   ", "city": "Bogotá", "status": "en_venta", "price": 1, "description": ""},
        ]
        result = self.repo._map_rows(rows)
        self.assertEqual(result, [])

    def test_skips_rows_without_status(self):
        rows = [
            {"address": "Calle 1", "city": "Bogotá", "status": None, "price": 1, "description": ""},
        ]
        result = self.repo._map_rows(rows)
        self.assertEqual(result, [])

    def test_null_price_is_preserved_as_none(self):
        rows = [
            {
                "address": "Calle 1",
                "city": "Bogotá",
                "status": "en_venta",
                "price": None,
                "description": "x",
            }
        ]
        result = self.repo._map_rows(rows)
        self.assertEqual(len(result), 1)
        self.assertIsNone(result[0].price)

    def test_negative_price_is_treated_as_none(self):
        rows = [
            {
                "address": "Calle 1",
                "city": "Bogotá",
                "status": "en_venta",
                "price": -500,
                "description": "x",
            }
        ]
        result = self.repo._map_rows(rows)
        self.assertIsNone(result[0].price)

    def test_non_integer_price_is_treated_as_none(self):
        rows = [
            {
                "address": "Calle 1",
                "city": "Bogotá",
                "status": "en_venta",
                "price": "no-es-un-número",
                "description": "x",
            }
        ]
        result = self.repo._map_rows(rows)
        self.assertIsNone(result[0].price)

    def test_partial_failure_does_not_break_full_response(self):
        rows = [
            {"address": None, "city": "Bogotá", "status": "en_venta", "price": 1, "description": ""},
            {"address": "Calle 2", "city": "Medellín", "status": "vendido", "price": 2, "description": ""},
        ]
        result = self.repo._map_rows(rows)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].address, "Calle 2")


if __name__ == "__main__":
    unittest.main()
