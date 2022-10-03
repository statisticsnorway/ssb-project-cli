"""Test cases for the --help option."""

from typer.testing import CliRunner

from dapla_hurtigstart_cli.hurtigstart.hurtigstart_cli import app


runner = CliRunner()


def test_app_build_help():
    result = runner.invoke(app, ["build", "--help"])
    assert result.exit_code == 0
    assert "Check if Cruft recommends updating" in result.stdout


def test_app_create_help():
    result = runner.invoke(app, ["create", "--help"])
    assert result.exit_code == 0
    assert "Prosjekt navn" in result.stdout
    assert "Ditt Github PAT" in result.stdout
