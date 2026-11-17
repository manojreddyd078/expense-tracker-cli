import sqlite3

from expense_tracker.database import database_connection, initialize_schema


def test_initialize_schema_creates_parent_and_expenses_table(tmp_path):
    database_path = tmp_path / "nested" / "tracker.db"

    initialize_schema(database_path)

    assert database_path.exists()
    with sqlite3.connect(database_path) as connection:
        columns = {
            row[1]: row[2]
            for row in connection.execute("PRAGMA table_info(expenses)")
        }
    assert columns == {
        "id": "INTEGER",
        "amount_cents": "INTEGER",
        "category": "TEXT",
        "description": "TEXT",
        "date": "TEXT",
    }


def test_initialize_schema_is_safe_to_repeat(tmp_path):
    database_path = tmp_path / "tracker.db"

    initialize_schema(database_path)
    initialize_schema(database_path)

    with sqlite3.connect(database_path) as connection:
        tables = connection.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name = 'expenses'"
        ).fetchall()
    assert tables == [("expenses",)]


def test_database_connection_closes_connection(tmp_path):
    database_path = tmp_path / "tracker.db"

    with database_connection(database_path) as connection:
        connection.execute("SELECT 1")

    try:
        connection.execute("SELECT 1")
    except sqlite3.ProgrammingError:
        pass
    else:
        raise AssertionError("database connection was not closed")
