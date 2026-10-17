"""Live MCP client integration test against a running service and database."""

import asyncio
import json
import os
import unittest
from uuid import uuid4

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8000/mcp")
RUN_MCP_E2E = os.getenv("RUN_MCP_E2E") == "1"


@unittest.skipUnless(
    RUN_MCP_E2E,
    "Set RUN_MCP_E2E=1 to call the live MCP server and insert a real ticket.",
)
class MCPClientIntegrationTests(unittest.TestCase):
    def test_client_calls_create_ticket_tool_on_running_server(self) -> None:
        """Discover and invoke the tool through the MCP Streamable HTTP client."""
        category = "integration-test"
        description = f"Automated MCP client integration check {uuid4()}."
        house_address = "3409 New Towne."
        priority = "low"
        status = "open"
        reported_by = "Femi"
        assigned_to = "MCP integration test assignee"
        ticket_payload = {
            "category": category,
            "description": description,
            "house_address": house_address,
            "priority": priority,
            "status": status,
            "reported_by": reported_by,
            "assigned_to": assigned_to,
        }
        result = asyncio.run(self._create_ticket(ticket_payload))

        self.assertFalse(result.isError, result.content)
        ticket = result.structuredContent
        if ticket is None:
            text_blocks = [
                block.text for block in result.content if hasattr(block, "text")
            ]
            self.assertTrue(text_blocks, "The tool returned no structured or text content.")
            parsed_result = json.loads(text_blocks[0])
            ticket = parsed_result.get("result", parsed_result)
        # Check that the returned ticket has the expected structure and values.
        self.assertIsInstance(ticket, dict)
        self.assertIsInstance(ticket.get("id"), int)
        self.assertIsInstance(ticket.get("house_id"), int)
        self.assertEqual(ticket.get("category"), category)
        self.assertEqual(ticket.get("description"), description)
        self.assertEqual(ticket.get("house_address"), house_address)
        self.assertEqual(ticket.get("priority"), priority)
        self.assertEqual(ticket.get("status"), status)
        self.assertEqual(ticket.get("reported_by"), reported_by)
        self.assertEqual(ticket.get("assigned_to"), assigned_to)

    async def _create_ticket(self, ticket_payload: dict[str, str]):
        """Call the remote tool using the official MCP Python client SDK."""
        async with streamable_http_client(MCP_SERVER_URL) as (
            read_stream,
            write_stream,
            _,
        ):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools = await session.list_tools()
                self.assertIn("create_ticket", {tool.name for tool in tools.tools})
                return await session.call_tool("create_ticket", ticket_payload)


if __name__ == "__main__":
    unittest.main()
