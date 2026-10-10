import unittest
from unittest.mock import MagicMock, patch

from src.tools.create_ticket import create_ticket


class CreateTicketTests(unittest.TestCase):
    @patch("src.tools.create_ticket.get_db_connection")
    def test_inserts_ticket_with_parameters_and_returns_database_row(
        self, get_connection
    ):
        inserted_row = {
            "id": 12,
            "category": "plumbing",
            "description": "Leaking faucet",
            "priority": "high",
        }
        connection = get_connection.return_value.__enter__.return_value
        cursor = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        cursor.fetchone.return_value = inserted_row

        with self.assertLogs(level="INFO") as captured_logs:
            result = create_ticket(
                category="plumbing",
                description="Leaking faucet",
                house_id=3,
                priority="high",
                status="open",
                reported_by="Alex",
                assigned_to="Jordan",
            )

        self.assertEqual(result, inserted_row)
        log_output = "\n".join(captured_logs.output)
        self.assertIn("Ticket inserted successfully.", log_output)
        self.assertNotIn("Leaking faucet", log_output)
        self.assertNotIn("Alex", log_output)
        self.assertNotIn("Jordan", log_output)
        cursor.execute.assert_called_once_with(
            "INSERT INTO tickets "
            "(category, description, house_id, priority, status, reported_by, assigned_to) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING *",
            ["plumbing", "Leaking faucet", 3, "high", "open", "Alex", "Jordan"],
        )
        get_connection.return_value.__exit__.assert_called_once_with(None, None, None)

    @patch("src.tools.create_ticket.get_db_connection")
    def test_omits_optional_fields_so_postgres_applies_defaults(self, get_connection):
        connection = get_connection.return_value.__enter__.return_value
        cursor = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        cursor.fetchone.return_value = {"id": 13}

        create_ticket(category="electrical", description="Hall light is out")

        cursor.execute.assert_called_once_with(
            "INSERT INTO tickets (category, description) VALUES (%s, %s) RETURNING *",
            ["electrical", "Hall light is out"],
        )

    @patch("src.tools.create_ticket.get_db_connection")
    def test_rejects_empty_description_without_connecting(self, get_connection):
        with self.assertRaisesRegex(ValueError, "description must be a non-empty string"):
            create_ticket(category="maintenance", description="  ")
        get_connection.assert_not_called()


if __name__ == "__main__":
    unittest.main()
