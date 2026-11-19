"""SQLite connection and schema management for the expense tracker."""

from contextlib import contextmanager
from pathlib import Path
import sqlite3
from collections.abc import Iterator

from expense_tracker.expense import Expense


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount_cents INTEGER NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    date TEXT NOT NULL
)
"""


def _prepare_database_path(path: str | Path) -> str:
    """Create a database parent directory and return a SQLite-compatible path."""
    database_path = Path(path)
    if str(database_path) != ":memory:":
        database_path.parent.mkdir(parents=True, exist_ok=True)
    return str(database_path)


@contextmanager
def database_connection(path: str | Path) -> Iterator[sqlite3.Connection]:
    """Yield a SQLite connection and always close it when finished."""
    connection = sqlite3.connect(_prepare_database_path(path))
    try:
        yield connection
    finally:
        connection.close()


def initialize_schema(path: str | Path) -> None:
    """Create the expenses table if it does not already exist."""
    with database_connection(path) as connection:
        connection.execute(SCHEMA_SQL)
        connection.commit()


def insert_expense(path: str | Path, expense: Expense) -> int:
    """Insert a validated expense and return its generated database ID."""
    if not isinstance(expense, Expense):
        raise TypeError("expense must be an Expense instance")

    with database_connection(path) as connection:
        try:
            cursor = connection.execute(
                """
                INSERT INTO expenses
                    (amount_cents, category, description, date)
                VALUES (?, ?, ?, ?)
                """,
                (
                    expense.amount_cents,
                    expense.category,
                    expense.description,
                    expense.date_iso,
                ),
            )
            connection.commit()
            return int(cursor.lastrowid)
        except sqlite3.Error:
            connection.rollback()
            raise
