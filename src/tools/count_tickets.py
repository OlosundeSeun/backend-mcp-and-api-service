"""Summarize ticket counts and retrieve ticket details from PostgreSQL."""

import logging
from typing import Any

import psycopg

from src.common.db import get_db_connection


def count_tickets() -> dict[str, Any]:
    """Return ticket counts grouped by priority and status, plus ticket IDs.

    All observed priority and status values are included, case-insensitively.
    Tickets with a missing value are grouped under ``"unspecified"``. The
    ``tickets`` field contains each ticket's ``id`` and ``house_id``.

    Raises:
        psycopg.Error: If PostgreSQL rejects the query or the connection fails.
        RuntimeError: If PostgreSQL does not return the counts.
    """
    logging.info("Summarizing maintenance ticket counts.")
    query = """
        WITH priority_counts AS (
            SELECT COALESCE(LOWER(priority), 'unspecified') AS category,
                   COUNT(*) AS ticket_count
            FROM tickets
            GROUP BY LOWER(priority)
        ),
        status_counts AS (
            SELECT COALESCE(LOWER(status), 'unspecified') AS category,
                   COUNT(*) AS ticket_count
            FROM tickets
            GROUP BY LOWER(status)
        )
        SELECT
            (SELECT COUNT(*) FROM tickets) AS total,
            COALESCE(
                (SELECT jsonb_object_agg(category, ticket_count)
                 FROM priority_counts),
                '{}'::jsonb
            ) AS by_priority,
            COALESCE(
                (SELECT jsonb_object_agg(category, ticket_count)
                 FROM status_counts),
                '{}'::jsonb
            ) AS by_status,
            COALESCE(
                (SELECT jsonb_agg(
                    jsonb_build_object('id', id, 'house_id', house_id)
                    ORDER BY id
                )
                 FROM tickets),
                '[]'::jsonb
            ) AS tickets
    """
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchone()
    except psycopg.Error:
        logging.info("Ticket count query failed.")
        raise

    if result is None:
        logging.info("Ticket count query completed without a result.")
        raise RuntimeError("The database did not return ticket counts.")

    summary: dict[str, Any] = {
        "total": result["total"],
        "by_priority": {
            "high": 0,
            "medium": 0,
            "low": 0,
            **result["by_priority"],
        },
        "by_status": {
            "open": 0,
            "closed": 0,
            "resolved": 0,
            **result["by_status"],
        },
        "tickets": result["tickets"],
    }

    logging.info("Ticket count summary completed successfully.")
    return summary


def get_ticket(
    ticket_id: int | None = None,
    house_id: int | None = None,
) -> dict[str, Any] | None:
    """Return a complete ticket row by its ticket ID or generated house ID.

    Exactly one identifier must be supplied. Returns ``None`` if no ticket
    matches the identifier.

    Raises:
        ValueError: If both identifiers or neither identifier is supplied.
        psycopg.Error: If PostgreSQL rejects the query or the connection fails.
    """
    if (ticket_id is None) == (house_id is None):
        raise ValueError("Provide exactly one of ticket_id or house_id.")

    if ticket_id is not None:
        query = "SELECT * FROM tickets WHERE id = %s"
        identifier = ticket_id
    else:
        query = "SELECT * FROM tickets WHERE house_id = %s"
        identifier = house_id

    logging.info("Looking up maintenance ticket by identifier.")
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (identifier,))
                ticket = cursor.fetchone()
    except psycopg.Error:
        logging.info("Ticket lookup failed.")
        raise

    if ticket is None:
        logging.info("No ticket matched the supplied identifier.")
        return None

    logging.info("Ticket lookup completed successfully.")
    return dict(ticket)
