"""Tests for the prompt module."""

from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch

from ssb_project_cli.ssb_project.create.prompt import choose_login
from ssb_project_cli.ssb_project.create.prompt import request_name_email


PROMPT = "ssb_project_cli.ssb_project.create.prompt"


@patch(f"{PROMPT}.typer.prompt")
def test_request_name_email(mock_prompt: Mock) -> None:
    """Checks if request_name_email returns the expected values."""
    mock_prompt.side_effect = ["Name", "email@email.com"]
    assert request_name_email() == ("Name", "email@email.com")


@patch(f"{PROMPT}.get_github_pat")
@patch(f"{PROMPT}.questionary")
def test_prompt_pat(mock_questionary: Mock, mock_get_pat: Mock) -> None:
    mock_get_pat.return_value = {"user": "pat", "user2": "pat2"}
    mock_questionary.select().ask.return_value = "user2"
    assert choose_login(Path(".")) == "pat2"


@patch(f"{PROMPT}.get_github_pat")
def test_prompt_pat_single_login(mock_get_pat: Mock) -> None:
    mock_get_pat.return_value = {"user": "pat"}
    assert choose_login(Path(".")) == "pat"
