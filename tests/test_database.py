import sqlite3
from decimal import Decimal

import pytest

from expense_tracker.database import database_connection, initialize_schema
from expense_tracker.database import (
    delete_expense,
    get_expense,
    insert_expense,
    list_expenses,
    update_expense,
)
from expense_tracker.expense import Expense


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


def test_insert_expense_returns_id_and_stores_validated_values(tmp_path):
    database_path = tmp_path / "tracker.db"
    initialize_schema(database_path)
    expense = Expense(Decimal("19.95"), "food", "Dinner", "2026-11-19")

    expense_id = insert_expense(database_path, expense)

    assert expense_id == 1
    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            "SELECT id, amount_cents, category, description, date "
            "FROM expenses WHERE id = ?",
            (expense_id,),
        ).fetchone()
    assert row == (1, 1995, "food", "Dinner", "2026-11-19")


def test_invalid_expense_is_rejected_before_database_write(tmp_path):
    database_path = tmp_path / "tracker.db"
    initialize_schema(database_path)

    try:
        Expense("0.00", "food", "Not stored", "2026-11-19")
    except ValueError:
        pass
    else:
        raise AssertionError("invalid expense was accepted")

    with sqlite3.connect(database_path) as connection:
        count = connection.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]
    assert count == 0


def test_insert_database_error_rolls_back(tmp_path):
    database_path = tmp_path / "tracker.db"
    initialize_schema(database_path)
    expense = Expense("2.50", "other", "Rollback", "2026-11-19")

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "CREATE TRIGGER reject_expenses BEFORE INSERT ON expenses "
            "BEGIN SELECT RAISE(ABORT, 'test failure'); END"
        )

    with pytest.raises(sqlite3.IntegrityError):
        insert_expense(database_path, expense)

    with sqlite3.connect(database_path) as connection:
        count = connection.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]
    assert count == 0


def test_get_expense_returns_record_with_formatted_amount(tmp_path):
    database_path = tmp_path / "tracker.db"
    initialize_schema(database_path)
    expense_id = insert_expense(
        database_path,
        Expense("19.95", "food", "Dinner", "2026-11-20"),
    )

    expense = get_expense(database_path, expense_id)

    assert expense is not None
    assert expense.id == expense_id
    assert expense.amount_cents == 1995
    assert expense.amount_formatted == "$19.95"


def test_get_expense_returns_none_for_missing_id(tmp_path):
    database_path = tmp_path / "tracker.db"
    initialize_schema(database_path)

    assert get_expense(database_path, 999) is None


def test_list_expenses_orders_by_date_then_id(tmp_path):
    database_path = tmp_path / "tracker.db"
    initialize_schema(database_path)
    first_id = insert_expense(
        database_path, Expense("1.00", "food", "Later", "2026-11-21")
    )
    second_id = insert_expense(
        database_path, Expense("2.00", "transport", "Earlier", "2026-11-19")
    )
    third_id = insert_expense(
        database_path, Expense("3.00", "housing", "Same date", "2026-11-19")
    )

    expenses = list_expenses(database_path)

    assert [expense.id for expense in expenses] == [second_id, third_id, first_id]


def test_list_expenses_returns_empty_list_for_empty_table(tmp_path):
    database_path = tmp_path / "tracker.db"
    initialize_schema(database_path)

    assert list_expenses(database_path) == []


def test_update_expense_changes_only_requested_fields(tmp_path):
    database_path = tmp_path / "tracker.db"
    initialize_schema(database_path)
    expense_id = insert_expense(
        database_path, Expense("10.00", "food", "Lunch", "2026-11-20")
    )

    assert update_expense(database_path, expense_id, amount="12.50", category="transport")

    updated = get_expense(database_path, expense_id)
    assert updated is not None
    assert updated.amount_cents == 1250
    assert updated.category == "travel"
    assert updated.description == "Lunch"
    assert updated.date_iso == "2026-11-20"


def test_invalid_update_leaves_record_unchanged(tmp_path):
    database_path = tmp_path / "tracker.db"
    initialize_schema(database_path)
    expense_id = insert_expense(
        database_path, Expense("10.00", "food", "Lunch", "2026-11-20")
    )

    with pytest.raises(ValueError):
        update_expense(database_path, expense_id, amount="0.00", category="transport")

    unchanged = get_expense(database_path, expense_id)
    assert unchanged is not None
    assert unchanged.amount_cents == 1000
    assert unchanged.category == "food"


def test_update_and_delete_nonexistent_ids_report_false(tmp_path):
    database_path = tmp_path / "tracker.db"
    initialize_schema(database_path)

    assert update_expense(database_path, 404, category="food") is False
    assert delete_expense(database_path, 404) is False


def test_delete_expense_removes_record_and_reports_result(tmp_path):
    database_path = tmp_path / "tracker.db"
    initialize_schema(database_path)
    expense_id = insert_expense(
        database_path, Expense("5.00", "food", "Snack", "2026-11-20")
    )

    assert delete_expense(database_path, expense_id) is True
    assert get_expense(database_path, expense_id) is None
    assert delete_expense(database_path, expense_id) is False


def test_list_expenses_filters_by_category(tmp_path):
    database_path = tmp_path / "tracker.db"
    initialize_schema(database_path)
    insert_expense(database_path, Expense("1.00", "food", "Meal", "2026-11-20"))
    insert_expense(database_path, Expense("2.00", "transport", "Bus", "2026-11-19"))

    expenses = list_expenses(database_path, category="FOOD")

    assert [(item.category, item.description) for item in expenses] == [("food", "Meal")]


def test_list_expenses_filters_by_date_bounds_inclusively(tmp_path):
    database_path = tmp_path / "tracker.db"
    initialize_schema(database_path)
    insert_expense(database_path, Expense("1.00", "food", "Before", "2026-11-18"))
    insert_expense(database_path, Expense("2.00", "food", "Start", "2026-11-19"))
    insert_expense(database_path, Expense("3.00", "food", "End", "2026-11-21"))
    insert_expense(database_path, Expense("4.00", "food", "After", "2026-11-22"))

    expenses = list_expenses(database_path, start_date="2026-11-19", end_date="2026-11-21")

    assert [item.description for item in expenses] == ["Start", "End"]


def test_list_expenses_combines_filters_and_preserves_order(tmp_path):
    database_path = tmp_path / "tracker.db"
    initialize_schema(database_path)
    first = insert_expense(database_path, Expense("1.00", "food", "Later", "2026-11-20"))
    insert_expense(database_path, Expense("2.00", "transport", "Other", "2026-11-19"))
    second = insert_expense(database_path, Expense("3.00", "food", "Earlier", "2026-11-19"))

    expenses = list_expenses(database_path, category="food", start_date="2026-11-19", end_date="2026-11-20")

    assert [item.id for item in expenses] == [second, first]


def test_list_expenses_rejects_reversed_or_malformed_dates(tmp_path):
    database_path = tmp_path / "tracker.db"
    initialize_schema(database_path)

    with pytest.raises(ValueError):
        list_expenses(database_path, start_date="2026-11-22", end_date="2026-11-21")
    with pytest.raises(ValueError):
        list_expenses(database_path, start_date="not-a-date")
