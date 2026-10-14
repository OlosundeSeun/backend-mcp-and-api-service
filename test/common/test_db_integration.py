"""Live PostgreSQL connection integration tests."""

import unittest

from src.common.db import get_db_connection


class DatabaseConnectionIntegrationTests(unittest.TestCase):
    def test_connects_to_maintenance_database(self) -> None:
        """Connect using the project .env and confirm the selected database."""
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT current_database() AS database_name")
                result = cursor.fetchone()

        self.assertIsNotNone(result)
        self.assertEqual(result["database_name"], "vbp_maintenance")


if __name__ == "__main__":
    unittest.main()
