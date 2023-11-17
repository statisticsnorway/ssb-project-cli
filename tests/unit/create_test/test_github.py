"""Tests for GitHub module"""
from pathlib import Path
from unittest.mock import MagicMock
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
from ssb_project_cli.ssb_project.create.github import get_github_username
from ssb_project_cli.ssb_project.create.github import get_org_members
from ssb_project_cli.ssb_project.create.github import is_github_repo
from ssb_project_cli.ssb_project.create.github import set_branch_protection_rules


GITHUB = "ssb_project_cli.ssb_project.create.github"


@patch(f"{GITHUB}.Github")
def test_create_github(mock_github: Mock) -> None:
    """Checks if create_github works."""
    create_github("token", "repo", "privacy", "desc", "org_name")
    assert mock_github.call_count == 1


@patch(f"{GITHUB}.Github.get_organization")
@patch(f"{GITHUB}.create_error_log")
def test_create_github_bad_credentials(
    mock_log: Mock, mock_github_get_organization: Mock
) -> None:
    """Checks if create_github works."""
    mock_org = Mock()
    mock_github_get_organization.return_value = mock_org
    mock_org.create_repo.return_value = Mock()
    mock_org.create_repo.side_effect = BadCredentialsException(Mock(), Mock(), Mock())

    with pytest.raises(SystemExit):
        create_github("token", "repo", "privacy", "desc", "org_name")
    assert mock_log.call_count == 1


@patch(f"{GITHUB}.Github.get_repo")
def test_is_github_repo(mock_get_repo: Mock) -> None:
    """Checks if is_github_repo returns/raises expected values/errors."""
    mock_get_repo.side_effect = [
        None,
        GithubException(status=1, data="", headers=None),
    ]
    assert is_github_repo("fake-token", "", "org_name")
    assert not is_github_repo("fake-token", "", "org_name")


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
    assert "verify" not in mock_github.call_args.kwargs.keys()


@patch(f"{GITHUB}.requests")
def test_get_org_members(mock_requests: Mock) -> None:
    mock_response_1 = MagicMock()
    mock_response_1.status_code = 200
    mock_response_1.json.return_value = [{"login": "user1"}]

    mock_response_2 = MagicMock()
    mock_response_2.status_code = 200
    mock_response_2.json.return_value = [{"login": "user2"}]

    mock_response_3 = MagicMock()
    mock_response_3.status_code = 200
    mock_response_3.json.return_value = []

    mock_requests.get.side_effect = [mock_response_1, mock_response_2, mock_response_3]
    assert get_org_members("fake_token") == ["user1", "user2"]


@patch(f"{GITHUB}.requests")
def test_get_org_members_cant_reach_api(mock_requests: Mock) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 1

    mock_requests.get.side_effect = mock_response
    with pytest.raises(SystemExit):
        get_org_members("fake_token")


@patch(f"{GITHUB}.get_org_members")
@patch(f"{GITHUB}.requests")
@patch(f"{GITHUB}.running_onprem")
@patch(f"{GITHUB}.Github")
def test_get_github_username_onprem(
    github_mock: Mock,
    running_onprem_mock: Mock,
    _requests_mock: Mock,
    _get_org_member_mock: Mock,
) -> None:
    running_onprem_mock.return_value = True
    mock_autocomplete = Mock()
    mock_autocomplete.ask.return_value = "TestUser1"
    with patch("questionary.autocomplete", return_value=mock_autocomplete):
        assert "TestUser1" == get_github_username(github_mock, "fake_token")


@patch(f"{GITHUB}.running_onprem")
@patch(f"{GITHUB}.Github")
def test_get_github_username_not_onprem(
    github_mock: Mock, running_onprem_mock: Mock
) -> None:
    running_onprem_mock.return_value = False
    mock_user = Mock()
    mock_user.login = "testuser"
    github_mock.get_user.return_value = mock_user
    assert "testuser" == get_github_username(github_mock, "fake_token")
