"""Test cases for the --help option."""

from typer.testing import CliRunner

from ssb_project_cli.ssb_project.app import app


runner = CliRunner()


def test_app_build_help() -> None:
    """Checks if the cli prints help description when supplied with build --help."""
    result = runner.invoke(app, ["build", "--help"], catch_exceptions=False)
    assert result.exit_code == 0
    assert (
        "Create a virtual environment and corresponding Jupyter kernel" in result.stdout
    )


def test_app_create_help() -> None:
    """Checks if the cli prints help description when supplied with create --help."""
    result = runner.invoke(app, ["create", "--help"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "Project name" in result.stdout
    assert "Your Github " in result.stdout
