-- Give every ticket its own generated house_id and store the selected house
-- name/address on the ticket. Run once against the service database.

BEGIN;

DO $migration$
DECLARE
    foreign_key RECORD;
BEGIN
    FOR foreign_key IN
        SELECT constraint_row.conname, namespace_row.nspname AS schema_name
        FROM pg_constraint AS constraint_row
        JOIN pg_class AS table_row
          ON table_row.oid = constraint_row.conrelid
        JOIN pg_namespace AS namespace_row
          ON namespace_row.oid = table_row.relnamespace
        JOIN pg_attribute AS column_row
          ON column_row.attrelid = table_row.oid
         AND column_row.attnum = ANY (constraint_row.conkey)
        WHERE constraint_row.contype = 'f'
          AND table_row.relname = 'tickets'
          AND column_row.attname = 'house_id'
          AND namespace_row.nspname = current_schema()
    LOOP
        EXECUTE format(
            'ALTER TABLE %I.tickets DROP CONSTRAINT %I',
            foreign_key.schema_name,
            foreign_key.conname
        );
    END LOOP;
END
$migration$;

ALTER TABLE tickets
    ADD COLUMN IF NOT EXISTS house_address TEXT;

WITH numbered_tickets AS (
    SELECT id, row_number() OVER (ORDER BY id) AS generated_house_id
    FROM tickets
)
UPDATE tickets
SET house_id = numbered_tickets.generated_house_id
FROM numbered_tickets
WHERE tickets.id = numbered_tickets.id;

CREATE SEQUENCE IF NOT EXISTS tickets_house_id_seq;
ALTER SEQUENCE tickets_house_id_seq OWNED BY tickets.house_id;
ALTER TABLE tickets
    ALTER COLUMN house_id SET DEFAULT nextval('tickets_house_id_seq'),
    ALTER COLUMN house_id SET NOT NULL;

SELECT setval(
    'tickets_house_id_seq',
    COALESCE((SELECT MAX(house_id) FROM tickets), 1),
    EXISTS (SELECT 1 FROM tickets)
);

CREATE UNIQUE INDEX IF NOT EXISTS tickets_house_id_unique_idx
    ON tickets (house_id);

COMMIT;
