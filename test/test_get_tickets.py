import unittest
from unittest.mock import MagicMock, patch

from src.tools.get_tickets import get_tickets


class GetTicketsTests(unittest.TestCase):
    @patch("src.tools.get_tickets.get_db_connection")
    def test_returns_all_ticket_fields_matching_ticket_id(self, get_connection):
        rows = [
            {"id": 8, "house_id": 15, "category": "plumbing"},
        ]
        connection = get_connection.return_value.__enter__.return_value
        cursor = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        cursor.fetchall.return_value = rows

        self.assertEqual(get_tickets(ticket_id=8), rows)
        cursor.execute.assert_called_once_with(
            "SELECT * FROM tickets WHERE id = %s ORDER BY id",
            (8,),
        )

    @patch("src.tools.get_tickets.get_db_connection")
    def test_returns_ticket_records_matching_house_id(self, get_connection):
        rows = [
            {"id": 15, "house_id": 8, "category": "plumbing"},
            {"id": 16, "house_id": 8, "category": "electrical"},
        ]
        connection = get_connection.return_value.__enter__.return_value
        cursor = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        cursor.fetchall.return_value = rows

        self.assertEqual(get_tickets(house_id=8), rows)
        cursor.execute.assert_called_once_with(
            "SELECT * FROM tickets WHERE house_id = %s ORDER BY id",
            (8,),
        )

    @patch("src.tools.get_tickets.get_db_connection")
    def test_returns_empty_list_when_no_tickets_match(self, get_connection):
        connection = get_connection.return_value.__enter__.return_value
        cursor = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        cursor.fetchall.return_value = []

        self.assertEqual(get_tickets(ticket_id=999), [])

    @patch("src.tools.get_tickets.get_db_connection")
    def test_requires_exactly_one_identifier(self, get_connection):
        for kwargs in ({}, {"ticket_id": 1, "house_id": 1}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaisesRegex(ValueError, "exactly one"):
                    get_tickets(**kwargs)

        get_connection.assert_not_called()


if __name__ == "__main__":
    unittest.main()
