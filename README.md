# backend-mcp-and-api-service

Python backend utilities for the MCP/API service.

## Configure PostgreSQL

Install the dependencies and copy `.env.example` to `.env`. Fill in the
PostgreSQL host, port, database name, username, and password in `.env`. The
database name for this service is `vb_maintenance`; set `DB_SSLMODE` to the
mode required by your PostgreSQL server.

The database role needs permission to connect to the database and insert into
`tickets`, as well as the required schema and sequence permissions. The table
must exist, and any non-null `house_id` must reference a row in `houses`.

Install dependencies with:

```powershell
python -m pip install -r requirements.txt
```

## Create a ticket

The shared PostgreSQL connection function is `get_db_connection` in
`src/common/db.py`. The ticket creation function and command-line tool are in
`src/tools/create_ticket.py`. The required arguments are `category` and
`description`; the table supplies defaults for omitted priority and status.

Run from the project root:

```powershell
python -m src.tools.create_ticket --category plumbing --description "The kitchen sink is leaking." --house-id 42 --reported-by Taylor
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

The integration tests use the project `.env` and connect to
`vbp_maintenance`. They create a uniquely identified ticket, verify that it is
committed and readable through a separate connection. The inserted test ticket
is intentionally retained in the database. They require the database and
`tickets` table to be available.
