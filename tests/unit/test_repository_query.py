"""Tests de construcción de query en PropertyRepository.

Validan que los filtros se traducen correctamente a SQL parametrizado
(sin conectar a la base de datos).
"""

import unittest

from services.property_service.models import PropertyFilters, PropertyStatus
from services.property_service.repository import PropertyRepository


class BuildQueryTest(unittest.TestCase):
    def setUp(self):
        self.repo = PropertyRepository()

    def test_query_always_joins_status_and_status_history(self):
        sql, _ = self.repo._build_query(PropertyFilters())
        self.assertIn("FROM property p", sql)
        self.assertIn("INNER JOIN status_history sh", sql)
        self.assertIn("INNER JOIN status s", sql)

    def test_query_filters_by_visible_statuses(self):
        sql, params = self.repo._build_query(PropertyFilters())
        self.assertIn("s.name IN", sql)
        # Los tres estados visibles deben estar entre los primeros parámetros.
        self.assertIn("pre_venta", params)
        self.assertIn("en_venta", params)
        self.assertIn("vendido", params)

    def test_query_without_filters_uses_default_limit_and_offset(self):
        sql, params = self.repo._build_query(PropertyFilters())
        self.assertIn("LIMIT %s OFFSET %s", sql)
        # Los últimos dos parámetros son limit y offset.
        self.assertEqual(params[-2], 50)
        self.assertEqual(params[-1], 0)

    def test_query_with_year_filter(self):
        sql, params = self.repo._build_query(PropertyFilters(year=2020))
        self.assertIn("AND p.year = %s", sql)
        self.assertIn(2020, params)

    def test_query_with_city_filter_is_case_insensitive(self):
        sql, params = self.repo._build_query(PropertyFilters(city="Bogotá"))
        self.assertIn("AND LOWER(p.city) = LOWER(%s)", sql)
        self.assertIn("Bogotá", params)

    def test_query_with_status_filter(self):
        sql, params = self.repo._build_query(
            PropertyFilters(status=PropertyStatus.EN_VENTA)
        )
        self.assertIn("AND s.name = %s", sql)
        self.assertIn("en_venta", params)

    def test_query_with_all_filters_combined(self):
        sql, params = self.repo._build_query(
            PropertyFilters(
                year=2015,
                city="Medellín",
                status=PropertyStatus.VENDIDO,
                limit=10,
                offset=20,
            )
        )
        self.assertIn("AND p.year = %s", sql)
        self.assertIn("AND LOWER(p.city) = LOWER(%s)", sql)
        self.assertIn("AND s.name = %s", sql)
        self.assertIn(2015, params)
        self.assertIn("Medellín", params)
        self.assertIn("vendido", params)
        self.assertEqual(params[-2], 10)
        self.assertEqual(params[-1], 20)

    def test_query_never_concatenates_user_input(self):
        """Defensa contra inyección SQL: valores de filtros nunca aparecen
        como literales en el SQL (solo como placeholders)."""
        sql, _ = self.repo._build_query(
            PropertyFilters(year=2020, city="'; DROP TABLE property; --")
        )
        self.assertNotIn("'; DROP TABLE property; --", sql)
        self.assertNotIn("2020", sql)


if __name__ == "__main__":
    unittest.main()
