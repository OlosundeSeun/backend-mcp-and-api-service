"""Single-command entry point for the live ticket insertion test."""

import unittest

from test.tools.test_create_ticket_integration import CreateTicketIntegrationTests


def main() -> None:
    """Run the end-to-end test that connects to PostgreSQL and inserts a ticket."""
    suite = unittest.TestLoader().loadTestsFromTestCase(
        CreateTicketIntegrationTests
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())


if __name__ == "__main__":
    main()
