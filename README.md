# expense-tracker-cli

A minimal Python 3.11+ command-line expense tracker skeleton.

## Quickstart

Create a virtual environment, install the package with its test extras, and
run the CLI help:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
py -m pip install -e ".[test]"
expense-tracker --help
pytest
```

The optional `--db` argument selects a database path. If omitted, the CLI uses
`EXPENSE_TRACKER_DB`, when set, and otherwise defaults to `data/expenses.db`.

Database operations and expense management are not implemented yet.

