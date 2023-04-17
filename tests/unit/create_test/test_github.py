"""Tests for GitHub module"""
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import mock_open
from unittest.mock import patch

import pytest
from github import BadCredentialsException
from github import GithubException

from ssb_project_cli.ssb_project.create.github import create_github
from ssb_project_cli.ssb_project.create.github import (
    get_environment_specific_github_object,
)
from ssb_project_cli.ssb_project.create.github import get_github_pat_from_gitcredentials
from ssb_project_cli.ssb_project.create.github import get_github_pat_from_netrc
from ssb_project_cli.ssb_project.create.github import is_github_repo
from ssb_project_cli.ssb_project.create.github import set_branch_protection_rules


GITHUB = "ssb_project_cli.ssb_project.create.github"


@patch(f"{GITHUB}.Github")
def test_create_github(mock_github: Mock) -> None:
    """Checks if create_github works."""
    create_github("token", "repo", "privacy", "desc", "org_name")
    assert mock_github.call_count == 1


@patch(f"{GITHUB}.create_error_log")
@patch(f"{GITHUB}.Github.get_repo")
def test_create_github_bad_credentials(
    mock_github_create_repo: Mock, mock_log: Mock
) -> None:
    """Checks if create_github works."""
    mock_github_create_repo.return_value = BadCredentialsException(
        Mock(), Mock(), Mock()
    )

    with pytest.raises(SystemExit):
        create_github("token", "repo", "privacy", "desc", "org_name")
    assert mock_log.call_count == 1


@patch(f"{GITHUB}.Github.get_repo")
def test_is_github_repo(mock_get_repo: Mock) -> None:
    """Checks if is_github_repo returns/raises expected values/errors."""
    mock_get_repo.side_effect = [
        None,
        GithubException(1, None, None),
        BadCredentialsException(1, None, None),
    ]
    assert is_github_repo("", "", "org_name")
    assert not is_github_repo("", "", "org_name")


@patch(f"{GITHUB}.Github")
def test_set_branch_protection_rules(mock_github: Mock) -> None:
    """Checks if set_branch_protection_rules works.

    Just cheks whether the token is given as an argument to
    Github() and repo name to Github().get_repo.
    """
    set_branch_protection_rules("token", "repo", "org_name")
    assert "token" in mock_github.call_args[0][0]


@pytest.mark.parametrize(
    "data,result,expected",
    [
        (
            "machine github.com login SSB-ola password ghp_4ak3tok",
            {"SSB-ola": "ghp_4ak3tok"},
            True,
        ),
        (
            "machine github.com login SSB-kari password ghp_faketok13",
            {"SSB-kari": "ghp_faketok13"},
            True,
        ),
        ("", {"SSB-kari": "ghp_faketok13"}, False),
        (
            "machine github.com login only-kari password ghp_faketok13",
            {"SSB-kari": "ghp_faketok13"},
            False,
        ),
        (
            "machine github.com login SSB-kari password ghp_token77",
            {"SSB-kari": "ghp_token"},
            False,
        ),
    ],
)
def test_get_github_pat_from_netrc(
    data: str, result: dict[str, str], expected: bool
) -> None:
    with patch(f"{GITHUB}.Path.exists", return_value=True):
        with patch(f"{GITHUB}.open", mock_open(read_data=data)):
            assert (get_github_pat_from_netrc(Path(".")) == result) == expected


@pytest.mark.parametrize(
    "data,result,expected",
    [
        (
            "https://ola:ghp_4ak3tok@github.com",
            {"ola": "ghp_4ak3tok"},
            True,
        ),
        (
            "https://ola:ghp_4ak3tok@github.com\nhttps://kari:token@github.com",
            {"ola": "ghp_4ak3tok", "kari": "token"},
            True,
        ),
        ("", {"SSB-kari": "ghp_faketok13"}, False),
        (
            "https://ola:ghp_4ak3tok@github.com",
            {"ola": "wrong-token"},
            False,
        ),
    ],
)
def test_get_github_pat_from_gitcredentials(
    data: str, result: dict[str, str], expected: bool
) -> None:
    with patch(f"{GITHUB}.Path.exists", return_value=True):
        with patch(f"{GITHUB}.open", mock_open(read_data=data)):
            assert (get_github_pat_from_gitcredentials(Path(".")) == result) == expected


@patch(f"{GITHUB}.running_onprem")
@patch(f"{GITHUB}.Github")
def test_get_environment_specific_github_object(
    mock_github: Mock, mock_running_onprem: Mock
) -> None:
    mock_running_onprem.side_effect = [True, False]

    # Test when running on-premises
    get_environment_specific_github_object("")
    # Assert that the Github object was called with verify=False
    assert (
        mock_github.call_args.kwargs["verify"] == "/etc/ssl/certs/ca-certificates.crt"
    )

    # Test when not running on-premises
    get_environment_specific_github_object("")

    # Assert that the Github object was called with verify=True
    assert mock_github.call_args.kwargs["verify"] is True
