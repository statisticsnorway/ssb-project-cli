"""Test cases for the --help option."""

from typer.testing import CliRunner

from ssb_project_cli.ssb_project.app import app


runner = CliRunner()


def test_app_build_help() -> None:
    """Checks if the cli prints help description when supplied with build --help."""
    result = runner.invoke(app, ["build", "--help"])
    assert result.exit_code == 0
    assert "Builds a virtual environment with Poetry and creates a kernel" in result.stdout


def test_app_create_help() -> None:
    """Checks if the cli prints help description when supplied with create --help."""
    result = runner.invoke(app, ["create", "--help"])
    assert result.exit_code == 0
    assert "Project name" in result.stdout
    assert "Your github PAT" in result.stdout
