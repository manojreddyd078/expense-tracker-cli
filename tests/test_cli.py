from expense_tracker.cli import build_parser, main
import pytest


def test_package_cli_help(capsys):
    with pytest.raises(SystemExit) as result:
        main(["--help"])

    assert result.value.code == 0

    output = capsys.readouterr().out
    assert "usage:" in output
    assert "--db" in output


def test_cli_parser_accepts_database_path():
    args = build_parser().parse_args(["--db", "custom.db"])

    assert str(args.db) == "custom.db"


def test_cli_parser_has_required_subcommands():
    args = build_parser().parse_args(["list"])

    assert args.command == "list"


def test_cli_help_does_not_create_database(tmp_path):
    database_path = tmp_path / "help-only.db"

    with pytest.raises(SystemExit):
        main(["--db", str(database_path), "--help"])

    assert not database_path.exists()


def test_cli_add_show_update_delete_workflow(tmp_path, capsys):
    database_path = tmp_path / "cli.db"

    assert main(["--db", str(database_path), "add", "12.50", "food", "2026-11-24", "--description", "Lunch"]) == 0
    assert "Added expense #1" in capsys.readouterr().out
    assert main(["--db", str(database_path), "show", "1"]) == 0
    assert "$12.50" in capsys.readouterr().out
    assert main(["--db", str(database_path), "update", "1", "--amount", "13.00"]) == 0
    assert "Updated expense #1" in capsys.readouterr().out
    assert main(["--db", str(database_path), "delete", "1"]) == 0
    assert "Deleted expense #1" in capsys.readouterr().out


def test_cli_missing_id_returns_nonzero(tmp_path, capsys):
    result = main(["--db", str(tmp_path / "cli.db"), "show", "99"])

    assert result != 0
    assert "not found" in capsys.readouterr().err


def test_cli_invalid_add_returns_nonzero_without_record(tmp_path, capsys):
    result = main(["--db", str(tmp_path / "cli.db"), "add", "0", "food", "2026-11-24"])

    assert result != 0
    assert "Error:" in capsys.readouterr().err
