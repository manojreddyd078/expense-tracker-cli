"""SQLite connection and schema management for the expense tracker."""

from contextlib import contextmanager
from pathlib import Path
import sqlite3
from collections.abc import Iterator
from decimal import Decimal

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


def _expense_from_row(row: tuple[object, ...]) -> Expense:
    """Convert a database row to the validated domain model."""
    return Expense(
        amount=Decimal(row[1]) / 100,
        category=str(row[2]),
        description=str(row[3]),
        date=str(row[4]),
        id=int(row[0]),
    )


def get_expense(path: str | Path, expense_id: int) -> Expense | None:
    """Return an expense by ID, or ``None`` when it does not exist."""
    with database_connection(path) as connection:
        row = connection.execute(
            "SELECT id, amount_cents, category, description, date "
            "FROM expenses WHERE id = ?",
            (expense_id,),
        ).fetchone()
    return None if row is None else _expense_from_row(row)


def list_expenses(path: str | Path) -> list[Expense]:
    """Return all expenses ordered by ISO date, then ID."""
    with database_connection(path) as connection:
        rows = connection.execute(
            "SELECT id, amount_cents, category, description, date "
            "FROM expenses ORDER BY date ASC, id ASC"
        ).fetchall()
    return [_expense_from_row(row) for row in rows]
