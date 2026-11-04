"""Retrieve ticket records by ticket ID or house ID."""

import logging
from typing import Any

import psycopg

from src.common.db import get_db_connection


def get_tickets(
    ticket_id: int | None = None,
    house_id: int | None = None,
) -> list[dict[str, Any]]:
    """Return all matching ticket rows for exactly one supplied identifier.

    Returns an empty list when no ticket matches.

    Raises:
        ValueError: If both identifiers or neither identifier is supplied.
        psycopg.Error: If PostgreSQL rejects the query or the connection fails.
    """
    if (ticket_id is None) == (house_id is None):
        raise ValueError("Provide exactly one of ticket_id or house_id.")

    if ticket_id is not None:
        query = "SELECT * FROM tickets WHERE id = %s ORDER BY id"
        identifier = ticket_id
    else:
        query = "SELECT * FROM tickets WHERE house_id = %s ORDER BY id"
        identifier = house_id

    logging.info("Retrieving maintenance tickets by identifier.")
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (identifier,))
                tickets = cursor.fetchall()
    except psycopg.Error:
        logging.info("Ticket retrieval failed.")
        raise

    logging.info("Ticket retrieval completed successfully.")
    return [dict(ticket) for ticket in tickets]
