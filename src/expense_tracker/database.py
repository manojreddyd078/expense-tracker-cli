"""SQLite connection and schema management for the expense tracker."""

from contextlib import contextmanager
from pathlib import Path
import sqlite3
from collections.abc import Iterator
from decimal import Decimal

from expense_tracker.expense import Expense
from expense_tracker.utils import parse_iso_date, validate_category


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


def list_expenses(
    path: str | Path,
    *,
    category: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[Expense]:
    """Return filtered expenses ordered by ISO date, then ID."""
    normalized_category = validate_category(category) if category is not None else None
    start = parse_iso_date(start_date) if start_date is not None else None
    end = parse_iso_date(end_date) if end_date is not None else None
    if start is not None and end is not None and start > end:
        raise ValueError("start date cannot be after end date")

    clauses = []
    parameters: list[str] = []
    if normalized_category is not None:
        clauses.append("category = ?")
        parameters.append(normalized_category)
    if start is not None:
        clauses.append("date >= ?")
        parameters.append(start.isoformat())
    if end is not None:
        clauses.append("date <= ?")
        parameters.append(end.isoformat())
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    with database_connection(path) as connection:
        rows = connection.execute(
            "SELECT id, amount_cents, category, description, date "
            f"FROM expenses{where} ORDER BY date ASC, id ASC",
            parameters,
        ).fetchall()
    return [_expense_from_row(row) for row in rows]


def update_expense(
    path: str | Path,
    expense_id: int,
    *,
    amount: object = None,
    category: str | None = None,
    description: str | None = None,
    date: object = None,
) -> bool:
    """Update supplied expense fields and return whether a row was changed."""
    with database_connection(path) as connection:
        row = connection.execute(
            "SELECT id, amount_cents, category, description, date "
            "FROM expenses WHERE id = ?",
            (expense_id,),
        ).fetchone()
        if row is None:
            return False

        current = _expense_from_row(row)
        updated = Expense(
            amount=current.amount if amount is None else amount,
            category=current.category if category is None else category,
            description=current.description if description is None else description,
            date=current.date if date is None else date,
            id=expense_id,
        )
        try:
            cursor = connection.execute(
                "UPDATE expenses SET amount_cents = ?, category = ?, "
                "description = ?, date = ? WHERE id = ?",
                (
                    updated.amount_cents,
                    updated.category,
                    updated.description,
                    updated.date_iso,
                    expense_id,
                ),
            )
            connection.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            connection.rollback()
            raise


def delete_expense(path: str | Path, expense_id: int) -> bool:
    """Delete an expense by ID and return whether a row was affected."""
    with database_connection(path) as connection:
        try:
            cursor = connection.execute(
                "DELETE FROM expenses WHERE id = ?",
                (expense_id,),
            )
            connection.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            connection.rollback()
            raise
