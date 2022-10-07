"""Test cases for the --help option."""

from typer.testing import CliRunner

from ssb_project_cli.ssb_project.app import app


runner = CliRunner()


def test_app_build_help() -> None:
    """Checks if the cli prints help description when supplied with build --help."""
    result = runner.invoke(app, ["build", "--help"])
    assert result.exit_code == 0
    assert "Check if Cruft recommends updating" in result.stdout
    assert "--kernel" in result.stdout
    assert "--curr-path" in result.stdout


def test_app_create_help() -> None:
    """Checks if the cli prints help description when supplied with create --help."""
    result = runner.invoke(app, ["create", "--help"])
    assert result.exit_code == 0
    assert "Prosjekt navn" in result.stdout
    assert "Ditt Github PAT" in result.stdout


def test_app_help() -> None:
    """Checks if the cli prints help description when supplied with --help."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "--install-completion" in result.stdout
    assert "--show-completion" in result.stdout
