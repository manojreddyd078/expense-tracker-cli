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
