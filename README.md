# backend-mcp-and-api-service

Python backend utilities for the MCP/API service.

## Configure PostgreSQL

Install the dependencies and copy `.env.example` to `.env`. Fill in the
PostgreSQL host, port, database name, username, and password in `.env`. The
database name for this service is `vb_maintenance`; set `DB_SSLMODE` to the
mode required by your PostgreSQL server.

The database role needs permission to connect to the database and insert into
`tickets`, as well as the required schema and sequence permissions. Apply
[`migrations/001_ticket_house_address_and_generated_house_id.sql`](./migrations/001_ticket_house_address_and_generated_house_id.sql)
before running the updated ticket tool. This migration makes `tickets.house_id`
an automatically generated, unique per-ticket value and adds `house_address`.
Existing ticket `house_id` values are renumbered sequentially; the previous
foreign key to `houses` is removed.

From the project root, apply the migration with:

```powershell
psql -d vb_maintenance -f migrations/001_ticket_house_address_and_generated_house_id.sql
```

Install dependencies with:

```powershell
python -m pip install -r requirements.txt
```

## Run the MCP server

Start the HTTP server from the project root:

```powershell
python -m src.main
```

The MCP endpoint uses Streamable HTTP at `http://localhost:8000/mcp`. The
readiness endpoint is `http://localhost:8000/health`; it checks PostgreSQL and
returns HTTP 503 if the database is unavailable. Set `MCP_HOST` and
`MCP_PORT` (or `PORT`) to configure the listener.

For Google ADK, configure an `McpToolset` with the MCP endpoint URL. For example,
the Python ADK client can connect using `StreamableHTTPConnectionParams` with
`url="http://<server-host>:8000/mcp"`. Make the listener reachable to the ADK
deployment and protect externally exposed deployments with an authenticated
gateway or equivalent network access control.

## Create a ticket

The shared PostgreSQL connection function is `get_db_connection` in
`src/common/db.py`. The ticket creation function and command-line tool are in
`src/tools/create_ticket.py`. The required arguments are `category`,
`description`, and `house-address`; the table supplies defaults for
omitted priority and status.

Run from the project root. Supply the house address directly; PostgreSQL
generates `house_id`:

```powershell
python -m src.tools.create_ticket --category plumbing --description "The kitchen sink is leaking." --house-address "211 Biraj Ct." --reported-by Taylor
```

Run unit tests with:

```powershell
python -m unittest discover -s test -p "test_*.py" -v
```

Run the real PostgreSQL integration tests with:

```powershell
python -m unittest discover -s test -p "*integration.py" -v
```

Run only the end-to-end ticket insertion test with its single entry point:

```powershell
python -m test.run_ticket_insert_e2e
```

Test the running MCP service through the official MCP client SDK. Start
`python -m src.main` in one terminal, then opt in to this live test from another
terminal. It connects to the server, discovers `create_ticket`, calls it, and
checks the returned ticket. This inserts a real ticket and leaves it in the
database:

```powershell
$env:RUN_MCP_E2E = "1"
python -m unittest test.test_mcp_client_integration -v
```

Set `MCP_SERVER_URL` if the server is not at
`http://127.0.0.1:8000/mcp`:

```powershell
$env:MCP_SERVER_URL = "http://localhost:8000/mcp"
```

The integration tests use the project `.env` and connect to
`vbp_maintenance`. They create a uniquely identified ticket, verify that it is
committed and readable through a separate connection. The inserted test ticket
is intentionally retained in the database. They require the database and
`tickets` table to be available.
