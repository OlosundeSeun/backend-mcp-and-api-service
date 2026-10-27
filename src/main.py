"""HTTP entry point for the maintenance-ticket MCP service."""

import logging
import os
from typing import Any

# PostgreSQL errors are handled by the health endpoint; Uvicorn serves HTTP.
import psycopg
import uvicorn

# FastMCP provides the MCP protocol and tool registration.
from mcp.server.fastmcp import FastMCP

# Starlette types add a regular HTTP health route to the MCP application.
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

# Reuse the database connection and ticket insertion logic already used by the CLI.
from src.common.db import get_db_connection
from src.tools.create_ticket import create_ticket as insert_ticket

# Use the module logger so failures can be reported without exposing credentials.
logger = logging.getLogger(__name__)

# Give connecting MCP clients a descriptive server name and purpose.
mcp = FastMCP(
    "Maintenance Ticket Service",
    instructions="Create maintenance tickets in the configured PostgreSQL database.",
)


# Register ticket creation as a callable MCP tool for external agent clients.
@mcp.tool()
def create_ticket(
    category: str,
    description: str,
    house_address: str,
    priority: str | None = None,
    status: str | None = None,
    reported_by: str | None = None,
    assigned_to: str | None = None,
) -> dict[str, Any]:
    """Create a maintenance ticket and return its database record."""
    # Delegate validation, SQL construction, and insertion to the shared function.
    return insert_ticket(
        category=category,
        description=description,
        house_address=house_address,
        priority=priority,
        status=status,
        reported_by=reported_by,
        assigned_to=assigned_to,
    )


# Expose service readiness separately from MCP tool operations.
def health_check(_request: Request) -> JSONResponse:
    """Report service readiness by checking PostgreSQL connectivity."""
    try:
        # Open a real database connection so health means PostgreSQL is reachable.
        with get_db_connection() as connection:
            # Run a minimal query that verifies the connection can execute SQL.
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                # Treat an unexpected empty result as a readiness failure.
                if cursor.fetchone() is None:
                    raise RuntimeError("Database health query returned no result.")
    except (psycopg.Error, ValueError):
        # Return a generic response; database exception details are not public.
        logger.warning("Health check failed: database is unavailable.")
        return JSONResponse(
            {"status": "unhealthy", "database": "unavailable"},
            status_code=503,
        )

    # Report readiness only after the database check succeeds.
    return JSONResponse({"status": "healthy", "database": "connected"})


# Build the Streamable HTTP MCP application (the MCP endpoint is /mcp).
app = mcp.streamable_http_app()

# Add a conventional GET health endpoint alongside the MCP route.
app.routes.insert(0, Route("/health", health_check, methods=["GET"]))


# Provide the module entry point for `python -m src.main`.
def main() -> None:
    """Run the MCP server over Streamable HTTP."""
    # Listen on all interfaces by default so remote agent deployments can reach it.
    host = os.getenv("MCP_HOST", "0.0.0.0")
    try:
        # Prefer the service-specific port setting, then common PORT, then 8002.
        port = int(os.getenv("MCP_PORT", os.getenv("PORT", "8002")))
    except ValueError as error:
        # Fail explicitly for invalid configuration instead of silently defaulting.
        raise ValueError("MCP_PORT or PORT must be an integer.") from error

    # Start the ASGI server with the configured bind address and port.
    uvicorn.run(app, host=host, port=port)


# Avoid starting the server when this module is imported for tests or reuse.
if __name__ == "__main__":
    main()
