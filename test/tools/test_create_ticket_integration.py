"""Live PostgreSQL ticket creation integration tests."""

import unittest
from uuid import uuid4

from src.common.db import get_db_connection
from src.tools.create_ticket import create_ticket


class CreateTicketIntegrationTests(unittest.TestCase):
    def test_creates_and_persists_ticket(self) -> None:
        """Insert a real ticket and verify it persists through a new connection."""
        house_address = "211 Biraj Ct."
        description = (
            "The kitchen sink drain is leaking beneath the cabinet, "
            f"and water is pooling on the floor. Test reference: {uuid4()}."
        )
        # Create a ticket and verify the returned dictionary matches the input values.
        ticket = create_ticket(
            house_address=house_address,
            category="plumbing",
            description=description,
            priority="high",
            status="open",
            reported_by="Automated integration test by seun",
            assigned_to="Yomi Maintenance Team",
        )
        #assert the returned ticket has the expected values
        self.assertIsInstance(ticket["id"], int)
        self.assertIsInstance(ticket["house_id"], int)
        self.assertEqual(ticket["house_address"], house_address)
        self.assertEqual(ticket["category"], "plumbing")
        self.assertEqual(ticket["description"], description)
        self.assertEqual(ticket["priority"], "high")
        self.assertEqual(ticket["status"], "open")
        self.assertEqual(ticket["reported_by"], "Automated integration test by seun")
        self.assertEqual(ticket["assigned_to"], "Yomi Maintenance Team")

        # A new connection verifies the function committed the inserted row.
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, house_id, house_address, category, description, priority, status,
                           reported_by, assigned_to
                    FROM tickets
                    WHERE id = %s
                    """,
                    (ticket["id"],),
                )
                persisted_ticket = cursor.fetchone()

        self.assertIsNotNone(persisted_ticket)
        self.assertEqual(persisted_ticket["id"], ticket["id"])
        self.assertEqual(persisted_ticket["house_id"], ticket["house_id"])
        self.assertEqual(persisted_ticket["house_address"], house_address)
        self.assertEqual(persisted_ticket["category"], "plumbing")
        self.assertEqual(persisted_ticket["description"], description)
        self.assertEqual(persisted_ticket["priority"], "high")
        self.assertEqual(persisted_ticket["status"], "open")
        self.assertEqual(
            persisted_ticket["reported_by"], "Automated integration test by seun"
        )
        self.assertEqual(persisted_ticket["assigned_to"], "Yomi Maintenance Team")

if __name__ == "__main__":
    unittest.main()
