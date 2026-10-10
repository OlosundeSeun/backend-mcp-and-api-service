"""Insert a maintenance ticket into the PostgreSQL tickets table."""

import argparse
import logging
from typing import Any

import psycopg

from src.common.db import get_db_connection


def create_ticket(
    category: str,
    description: str,
    house_id: int | None = None,
    priority: str | None = None,
    status: str | None = None,
    reported_by: str | None = None,
    assigned_to: str | None = None,
) -> dict[str, Any]:
    """Insert a maintenance ticket and return the row created by PostgreSQL.

    Args:
        category: Required ticket category, limited to the table's 50-character
            column size.
        description: Required description of the maintenance issue.
        house_id: Optional ID of the related house; must exist in ``houses``.
        priority: Optional priority; omitted values use the database default.
        status: Optional status; omitted values use the database default.
        reported_by: Optional name of the person reporting the issue.
        assigned_to: Optional name of the person assigned to the issue.

    Returns:
        The inserted ticket as a dictionary keyed by database column name.

    Raises:
        ValueError: If a required string is empty, the category is too long, or
            ``house_id`` is not an integer.
        psycopg.Error: If PostgreSQL rejects the insert or the connection fails.
        RuntimeError: If PostgreSQL does not return the inserted row.
    """
    logging.info("Validating maintenance ticket input.")
    if not isinstance(category, str) or not category.strip():
        logging.info("Ticket creation rejected: category is missing or empty.")
        raise ValueError("category must be a non-empty string.")
    if len(category) > 50:
        logging.info("Ticket creation rejected: category exceeds the column limit.")
        raise ValueError("category must be at most 50 characters.")
    if not isinstance(description, str) or not description.strip():
        logging.info("Ticket creation rejected: description is missing or empty.")
        raise ValueError("description must be a non-empty string.")
    if house_id is not None and type(house_id) is not int:
        logging.info("Ticket creation rejected: house_id is not an integer.")
        raise ValueError("house_id must be an integer or None.")

    # Column names come only from this fixed list; all ticket values are parameters.
    columns = ["category", "description"]
    values: list[Any] = [category, description]
    optional_fields = (
        ("house_id", house_id),
        ("priority", priority),
        ("status", status),
        ("reported_by", reported_by),
        ("assigned_to", assigned_to),
    )
    # Exclude unspecified values so nullable columns and database defaults work.
    for column, value in optional_fields:
        if value is not None:
            columns.append(column)
            values.append(value)

    placeholders = ", ".join("%s" for _ in values)
    # query is constructed from fixed column names and parameter placeholders only;
    # values are passed separately to avoid SQL injection.
    query = (
        f"INSERT INTO tickets ({', '.join(columns)}) "
        f"VALUES ({placeholders}) RETURNING *"
    )

    # The connection context commits on success, rolls back on error, and closes.
    logging.info("Inserting maintenance ticket into the database.")
    try:
        # The connection context commits on success, rolls back on error, and closes.
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, values)
                ticket = cursor.fetchone()
    except psycopg.Error:
        # Do not include ticket contents or exception text in logs.
        logging.info("Ticket insert failed.")
        raise

    if ticket is None:
        logging.info("Ticket insert completed without a returned row.")
        raise RuntimeError("The database did not return the inserted ticket.")
    logging.info("Ticket inserted successfully.")
    return dict(ticket)


def main() -> None:
    """Run the ticket creation command-line interface.

    Parses the supplied ticket fields, calls :func:`create_ticket`, and prints
    the ID returned by PostgreSQL. Database configuration and insert errors are
    allowed to propagate so command failures are visible to the caller.
    """
    # Set up readable info-level output for direct CLI use; host applications
    # should configure their own logging when importing this function.
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting ticket creation command-line tool.")
    parser = argparse.ArgumentParser(description="Create a maintenance ticket.")
    parser.add_argument("--category", required=True, help="Ticket category")
    parser.add_argument("--description", required=True, help="Ticket description")
    parser.add_argument("--house-id", type=int, help="Related house ID")
    parser.add_argument("--priority", help="Ticket priority (defaults to medium)")
    parser.add_argument("--status", help="Ticket status (defaults to open)")
    parser.add_argument("--reported-by", help="Name of the person reporting the ticket")
    parser.add_argument("--assigned-to", help="Name of the person assigned the ticket")
    args = parser.parse_args()

    ticket = create_ticket(
        category=args.category,
        description=args.description,
        house_id=args.house_id,
        priority=args.priority,
        status=args.status,
        reported_by=args.reported_by,
        assigned_to=args.assigned_to,
    )
    logging.info("Ticket creation command-line tool completed successfully.")
    print(f"Created ticket {ticket['id']}.")


if __name__ == "__main__":
    main()
