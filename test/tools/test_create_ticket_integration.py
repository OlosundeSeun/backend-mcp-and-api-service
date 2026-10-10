"""Live PostgreSQL ticket creation integration tests."""

import unittest
from uuid import uuid4

from src.common.db import get_db_connection
from src.tools.create_ticket import create_ticket


class CreateTicketIntegrationTests(unittest.TestCase):
    def test_creates_and_persists_ticket(self) -> None:
        """Insert a real ticket and verify it persists through a new connection."""
        # Use a real house row so the payload satisfies the foreign-key constraint.
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT id FROM houses ORDER BY id LIMIT 1")
                house = cursor.fetchone()

        self.assertIsNotNone(house, "The houses table must contain a row for this test.")

        description = (
            "The kitchen sink drain is leaking beneath the cabinet, "
            f"and water is pooling on the floor. Test reference: {uuid4()}."
        )
        ticket = create_ticket(
            house_id=house["id"],
            category="plumbing",
            description=description,
            priority="high",
            status="open",
            reported_by="Automated integration test",
            assigned_to="Maintenance Team",
        )

        self.assertIsInstance(ticket["id"], int)
        self.assertEqual(ticket["house_id"], house["id"])
        self.assertEqual(ticket["category"], "plumbing")
        self.assertEqual(ticket["description"], description)
        self.assertEqual(ticket["priority"], "high")
        self.assertEqual(ticket["status"], "open")
        self.assertEqual(ticket["reported_by"], "Automated integration test")
        self.assertEqual(ticket["assigned_to"], "Maintenance Team")

        # A new connection verifies the function committed the inserted row.
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, house_id, category, description, priority, status,
                           reported_by, assigned_to
                    FROM tickets
                    WHERE id = %s
                    """,
                    (ticket["id"],),
                )
                persisted_ticket = cursor.fetchone()

        self.assertIsNotNone(persisted_ticket)
        self.assertEqual(persisted_ticket["id"], ticket["id"])
        self.assertEqual(persisted_ticket["house_id"], house["id"])
        self.assertEqual(persisted_ticket["category"], "plumbing")
        self.assertEqual(persisted_ticket["description"], description)
        self.assertEqual(persisted_ticket["priority"], "high")
        self.assertEqual(persisted_ticket["status"], "open")
        self.assertEqual(
            persisted_ticket["reported_by"], "Automated integration test"
        )
        self.assertEqual(persisted_ticket["assigned_to"], "Maintenance Team")

if __name__ == "__main__":
    unittest.main()
