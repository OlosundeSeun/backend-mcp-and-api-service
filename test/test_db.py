import os
import unittest
from unittest.mock import patch

from psycopg.rows import dict_row

from src.common import db


class GetDatabaseConnectionTests(unittest.TestCase):
    @patch.dict(
        os.environ,
        {
            "DB_HOST": "db.example.test",
            "DB_PORT": "5433",
            "DB_NAME": "vbp_maintenance",
            "DB_USER": "maintenance_app",
            "DB_PASSWORD": "test-password",
            "DB_SSLMODE": "require",
        },
        clear=True,
    )
    @patch("src.common.db.psycopg.connect")
    @patch("src.common.db.load_dotenv")
    def test_loads_project_env_and_connects_with_settings(
        self, load_dotenv, connect
    ):
        with self.assertLogs(level="INFO") as captured_logs:
            connection = db.get_db_connection()

        self.assertIs(connection, connect.return_value)
        load_dotenv.assert_called_once_with(dotenv_path=db.ENV_FILE, override=True)
        connect.assert_called_once_with(
            host="db.example.test",
            port=5433,
            dbname="vbp_maintenance",
            user="maintenance_app",
            password="test-password",
            sslmode="require",
            connect_timeout=5,
            row_factory=dict_row,
        )
        log_output = "\n".join(captured_logs.output)
        self.assertIn(
            "All required database environment variables were loaded successfully.",
            log_output,
        )
        self.assertIn("PostgreSQL connection established.", log_output)
        self.assertNotIn("test-password", log_output)
        self.assertNotIn("db.example.test", log_output)
        self.assertNotIn("maintenance_app", log_output)

    @patch.dict(os.environ, {}, clear=True)
    @patch("src.common.db.psycopg.connect")
    @patch("src.common.db.load_dotenv")
    def test_reports_missing_env_settings(self, load_dotenv, connect):
        with self.assertLogs(level="INFO") as captured_logs:
            with self.assertRaisesRegex(ValueError, "DB_HOST, DB_PORT"):
                db.get_db_connection()

        load_dotenv.assert_called_once_with(dotenv_path=db.ENV_FILE, override=True)
        connect.assert_not_called()
        log_output = "\n".join(captured_logs.output)
        self.assertIn("Required database environment variables were not all loaded", log_output)
        self.assertIn("DB_HOST", log_output)
        self.assertIn("DB_PASSWORD", log_output)
        self.assertNotIn("test-password", log_output)

    @patch.dict(
        os.environ,
        {
            "DB_HOST": "db.example.test",
            "DB_PORT": "not-a-port",
            "DB_NAME": "vbp_maintenance",
            "DB_USER": "maintenance_app",
            "DB_PASSWORD": "test-password",
        },
        clear=True,
    )
    @patch("src.common.db.psycopg.connect")
    @patch("src.common.db.load_dotenv")
    def test_reports_invalid_port(self, load_dotenv, connect):
        with self.assertRaisesRegex(ValueError, "DB_PORT.*must be an integer"):
            db.get_db_connection()
        load_dotenv.assert_called_once_with(dotenv_path=db.ENV_FILE, override=True)
        connect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
