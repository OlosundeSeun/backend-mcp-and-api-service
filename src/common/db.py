"""PostgreSQL connection setup shared by application tools."""

import logging
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


def get_db_connection() -> psycopg.Connection:
    """Open and return a PostgreSQL connection configured from the project `.env`.

    Loads the required host, port, database, username, and password settings from
    the `.env` file in the project root. An optional ``DB_SSLMODE`` setting
    controls PostgreSQL TLS behavior and defaults to ``prefer``. Returned rows
    are dictionaries keyed by column name.

    Returns:
        An open psycopg connection using dictionary row results.

    Raises:
        ValueError: If a required setting is missing or ``DB_PORT`` is not an
            integer.
        psycopg.OperationalError: If PostgreSQL cannot be reached or rejects
            the supplied connection settings.
    """
    # Load project configuration explicitly so this works from any working directory.
    load_dotenv(dotenv_path=ENV_FILE, override=True)

    required_settings = ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")
    missing_settings = [name for name in required_settings if not os.getenv(name)]
    if missing_settings:
        # Log setting names only; never log environment values or credentials.
        logging.info(
            "Required database environment variables were not all loaded; "
            "missing: %s",
            ", ".join(missing_settings),
        )
        raise ValueError(
            "Missing required database settings in .env: "
            + ", ".join(missing_settings)
        )
    logging.info("All required database environment variables were loaded successfully.")

    # Convert the port before connecting so invalid configuration has a clear error.
    try:
        port = int(os.environ["DB_PORT"])
    except ValueError as error:
        logging.info("Database connection configuration has an invalid port.")
        raise ValueError("DB_PORT in .env must be an integer.") from error

    # Dict rows let callers return inserted records by their database column names.
    logging.info("Opening PostgreSQL connection.")
    try:
        # The connection context commits on success, rolls back on error, and closes.
        connection = psycopg.connect(
            host=os.environ["DB_HOST"],
            port=port,
            dbname=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            sslmode=os.getenv("DB_SSLMODE", "prefer"),
            connect_timeout=5,
            row_factory=dict_row,
        )
    except psycopg.Error:
        # Avoid logging the exception because it may contain connection details.
        logging.info("PostgreSQL connection attempt failed.")
        raise

    logging.info("PostgreSQL connection established.")
    return connection
