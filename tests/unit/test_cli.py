"""Tests that the Arguments and Options in the CLI layer are correctly interpreted."""

from pathlib import Path
from unittest.mock import ANY
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from ssb_project_cli.ssb_project.app import app


APP = "ssb_project_cli.ssb_project.app"


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@patch(f"{APP}.create_project", return_value=None)
def test_create_no_verify(
    mock_create_project: Mock, runner: CliRunner, name: Path
) -> None:
    runner.invoke(app, ["create", str(name), "--no-verify"], catch_exceptions=False)
    mock_create_project.assert_called_once_with(
        ANY,
        ANY,
        ANY,
        ANY,
        ANY,
        ANY,
        ANY,
        ANY,
        ANY,
        ANY,
        ANY,
        ANY,
        False,
        ANY,
    )


@patch(f"{APP}.create_project", return_value=None)
def test_create_verify(
    mock_create_project: Mock, runner: CliRunner, name: Path
) -> None:
    runner.invoke(app, ["create", str(name)], catch_exceptions=False)
    mock_create_project.assert_called_once_with(
        ANY,
        ANY,
        ANY,
        ANY,
        ANY,
        ANY,
        ANY,
        ANY,
        ANY,
        ANY,
        ANY,
        ANY,
        True,
        ANY,
    )
