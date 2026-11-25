"""Command-line interface for the expense tracker."""

import argparse
import os
from pathlib import Path
import sqlite3
import sys

from expense_tracker.database import (
    delete_expense,
    get_expense,
    initialize_schema,
    insert_expense,
    list_expenses,
    update_expense,
)
from expense_tracker.categories import SUPPORTED_CATEGORIES
from expense_tracker.expense import Expense

DB_ENV_VAR = "EXPENSE_TRACKER_DB"
DEFAULT_DB_PATH = Path.cwd() / "data" / "expenses.db"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="expense-tracker")
    parser.add_argument("--db", type=Path, help=f"Database path (overrides ${DB_ENV_VAR}).")
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("add", help="Add an expense")
    add.add_argument("amount")
    add.add_argument("category")
    add.add_argument("date")
    add.add_argument("--description", default="")
    commands.add_parser("list", help="List expenses")
    show = commands.add_parser("show", help="Show one expense")
    show.add_argument("id", type=int)
    update = commands.add_parser("update", help="Update an expense")
    update.add_argument("id", type=int)
    update.add_argument("--amount")
    update.add_argument("--category")
    update.add_argument("--description")
    update.add_argument("--date")
    delete = commands.add_parser("delete", help="Delete an expense")
    delete.add_argument("id", type=int)
    commands.add_parser("categories", help="List supported categories")
    return parser


def resolve_db_path(cli_path: Path | None = None) -> Path:
    if cli_path is not None:
        return cli_path
    env_path = os.environ.get(DB_ENV_VAR)
    return Path(env_path) if env_path else DEFAULT_DB_PATH


def _display(expense: Expense) -> None:
    print(f"#{expense.id}: {expense.amount_formatted} | {expense.category} | {expense.date_iso} | {expense.description}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "categories":
        print("Supported categories:")
        for category in SUPPORTED_CATEGORIES:
            print(f"- {category}")
        return 0
    database_path = resolve_db_path(args.db)
    initialize_schema(database_path)
    try:
        if args.command == "add":
            expense_id = insert_expense(database_path, Expense(args.amount, args.category, args.description, args.date))
            print(f"Added expense #{expense_id}.")
        elif args.command == "list":
            for expense in list_expenses(database_path):
                _display(expense)
        elif args.command == "show":
            expense = get_expense(database_path, args.id)
            if expense is None:
                print(f"Expense #{args.id} not found.", file=sys.stderr)
                return 1
            _display(expense)
        elif args.command == "update":
            changed = update_expense(database_path, args.id, amount=args.amount, category=args.category, description=args.description, date=args.date)
            if not changed:
                print(f"Expense #{args.id} not found.", file=sys.stderr)
                return 1
            print(f"Updated expense #{args.id}.")
        elif args.command == "delete":
            deleted = delete_expense(database_path, args.id)
            if not deleted:
                print(f"Expense #{args.id} not found.", file=sys.stderr)
                return 1
            print(f"Deleted expense #{args.id}.")
        return 0
    except (ValueError, TypeError, sqlite3.Error) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
