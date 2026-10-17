import asyncio
import unittest
from unittest.mock import MagicMock, patch

import httpx
import psycopg

from src.main import app, mcp


class MCPServerTests(unittest.TestCase):
    async def request_health(self) -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.get("/health")

    @patch("src.main.get_db_connection")
    def test_health_endpoint_reports_database_ready(self, get_connection):
        connection = get_connection.return_value.__enter__.return_value
        cursor = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        cursor.fetchone.return_value = {"?column?": 1}

        response = asyncio.run(self.request_health())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {"status": "healthy", "database": "connected"}
        )
        cursor.execute.assert_called_once_with("SELECT 1")

    @patch("src.main.get_db_connection", side_effect=psycopg.OperationalError("private"))
    def test_health_endpoint_reports_database_unavailable(self, get_connection):
        response = asyncio.run(self.request_health())

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(), {"status": "unhealthy", "database": "unavailable"}
        )
        self.assertNotIn("private", response.text)
        get_connection.assert_called_once_with()

    def test_ticket_tool_is_registered_with_address_input(self):
        tools = asyncio.run(mcp.list_tools())
        ticket_tool = next(tool for tool in tools if tool.name == "create_ticket")

        self.assertIn("house_address", ticket_tool.inputSchema["properties"])
        self.assertIn("category", ticket_tool.inputSchema["required"])
        self.assertIn("description", ticket_tool.inputSchema["required"])


if __name__ == "__main__":
    unittest.main()
