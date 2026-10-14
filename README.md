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

The integration tests use the project `.env` and connect to
`vbp_maintenance`. They create a uniquely identified ticket, verify that it is
committed and readable through a separate connection. The inserted test ticket
is intentionally retained in the database. They require the database and
`tickets` table to be available.
