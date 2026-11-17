"""Command-line entry point for the expense tracker."""

import argparse
import os
from pathlib import Path

from expense_tracker.database import initialize_schema


DB_ENV_VAR = "EXPENSE_TRACKER_DB"
DEFAULT_DB_PATH = Path.cwd() / "data" / "expenses.db"


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        prog="expense-tracker",
        description="Command-line expense tracker.",
    )
    parser.add_argument(
        "--db",
        type=Path,
        help=f"Database path (overrides ${DB_ENV_VAR}).",
    )
    return parser


def resolve_db_path(cli_path: Path | None = None) -> Path:
    """Resolve the database path using CLI, environment, then local default."""
    if cli_path is not None:
        return cli_path
    env_path = os.environ.get(DB_ENV_VAR)
    if env_path:
        return Path(env_path)
    return DEFAULT_DB_PATH


def main(argv: list[str] | None = None) -> int:
    """Parse CLI arguments, initialize the database, and return success."""
    args = build_parser().parse_args(argv)
    initialize_schema(resolve_db_path(args.db))
    return 0

