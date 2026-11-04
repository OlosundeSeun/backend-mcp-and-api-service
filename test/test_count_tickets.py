import unittest
from unittest.mock import MagicMock, patch

from src.tools.count_tickets import count_tickets, get_ticket


class CountTicketsTests(unittest.TestCase):
    @patch("src.tools.count_tickets.get_db_connection")
    def test_returns_total_counts_and_ticket_identifiers(self, get_connection):
        connection = get_connection.return_value.__enter__.return_value
        cursor = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        cursor.fetchone.return_value = {
            "total": 2,
            "by_priority": {"high": 2},
            "by_status": {"open": 1, "resolved": 1},
            "tickets": [
                {"id": 15, "house_id": 8},
                {"id": 16, "house_id": 9},
            ],
        }

        result = count_tickets()

        self.assertEqual(
            result,
            {
                "total": 2,
                "by_priority": {"high": 2, "medium": 0, "low": 0},
                "by_status": {"open": 1, "closed": 0, "resolved": 1},
                "tickets": [
                    {"id": 15, "house_id": 8},
                    {"id": 16, "house_id": 9},
                ],
            },
        )
        cursor.execute.assert_called_once()
        query = cursor.execute.call_args.args[0]
        self.assertIn("jsonb_build_object('id', id, 'house_id', house_id)", query)

    @patch("src.tools.count_tickets.get_db_connection")
    def test_returns_zero_counts_for_empty_ticket_table(self, get_connection):
        connection = get_connection.return_value.__enter__.return_value
        cursor = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        cursor.fetchone.return_value = {
            "total": 0,
            "by_priority": {},
            "by_status": {},
            "tickets": [],
        }

        self.assertEqual(
            count_tickets(),
            {
                "total": 0,
                "by_priority": {"high": 0, "medium": 0, "low": 0},
                "by_status": {"open": 0, "closed": 0, "resolved": 0},
                "tickets": [],
            },
        )


class GetTicketTests(unittest.TestCase):
    @patch("src.tools.count_tickets.get_db_connection")
    def test_looks_up_ticket_by_id_and_returns_all_columns(self, get_connection):
        ticket = {
            "id": 15,
            "house_id": 8,
            "category": "plumbing",
            "description": "Leaking faucet",
            "priority": "high",
            "status": "open",
        }
        connection = get_connection.return_value.__enter__.return_value
        cursor = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        cursor.fetchone.return_value = ticket

        self.assertEqual(get_ticket(ticket_id=15), ticket)
        cursor.execute.assert_called_once_with(
            "SELECT * FROM tickets WHERE id = %s",
            (15,),
        )

    @patch("src.tools.count_tickets.get_db_connection")
    def test_looks_up_ticket_by_house_id(self, get_connection):
        connection = get_connection.return_value.__enter__.return_value
        cursor = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        cursor.fetchone.return_value = {"id": 15, "house_id": 8}

        get_ticket(house_id=8)

        cursor.execute.assert_called_once_with(
            "SELECT * FROM tickets WHERE house_id = %s",
            (8,),
        )

    @patch("src.tools.count_tickets.get_db_connection")
    def test_returns_none_when_ticket_is_not_found(self, get_connection):
        connection = get_connection.return_value.__enter__.return_value
        cursor = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        cursor.fetchone.return_value = None

        self.assertIsNone(get_ticket(ticket_id=999))

    @patch("src.tools.count_tickets.get_db_connection")
    def test_requires_exactly_one_identifier(self, get_connection):
        for kwargs in ({}, {"ticket_id": 1, "house_id": 1}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaisesRegex(ValueError, "exactly one"):
                    get_ticket(**kwargs)

        get_connection.assert_not_called()


if __name__ == "__main__":
    unittest.main()
