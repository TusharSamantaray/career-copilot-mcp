"""When a suite runs against Postgres (DATABASE_URL set), start it from an
empty test database, the way SQLite suites start from an empty folder.
Only ever point DATABASE_URL at a throwaway database when testing."""
import os


def fresh_database():
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        return
    import psycopg
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute("DROP TABLE IF EXISTS cc_records")
        conn.execute("DROP TABLE IF EXISTS cc_keys")
