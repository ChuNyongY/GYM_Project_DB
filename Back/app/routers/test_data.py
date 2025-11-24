"""
Test-data router (disabled)

This module previously provided test-data generation utilities and relied on
SQLAlchemy ORM models and Faker. That code has been disabled because the
project migrated to raw SQL (pymysql) and many ORM models were removed.

If you need a test-data generator, re-create this module using the current
database access patterns (use the `get_db` cursor dependency and raw SQL
INSERT statements) or create a separate script that runs outside the
application package.
"""

def _disabled():
    raise RuntimeError(
        "test_data router has been disabled. Recreate it using raw SQL if needed."
    )


__all__ = ["_disabled"]