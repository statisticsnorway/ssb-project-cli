from dataclasses import dataclass
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch
from webbrowser import get

import pytest
from github import BadCredentialsException
from github import GithubException

from ssb_project_cli.ssb_project.app import extract_name_email
from ssb_project_cli.ssb_project.app import get_gitconfig_element
from ssb_project_cli.ssb_project.app import is_github_repo
from ssb_project_cli.ssb_project.app import make_git_repo_and_push
from ssb_project_cli.ssb_project.app import mangle_url
from ssb_project_cli.ssb_project.app import request_name_email
from ssb_project_cli.ssb_project.app import set_branch_protection_rules


PKG = "ssb_project_cli.ssb_project.app"


@pytest.mark.parametrize(
    "url,mangle,expected",
    [
        ("https://example.com", "test", "https://test@example.com"),
        ("git://github.com/etc", "user", "git://user@github.com/etc"),
    ],
)
def test_mangle_url(url: str, mangle: str, expected: str) -> None:
    assert mangle_url(url, mangle) == expected


@patch(f"{PKG}.Github.get_repo")
def test_is_github_repo(mock_get_repo: Mock) -> None:
    mock_get_repo.side_effect = [
        None,
        GithubException(1, None, None),
        BadCredentialsException(1, None, None),
    ]
    assert is_github_repo("", "")
    assert not is_github_repo("", "")
    with pytest.raises(ValueError):
        is_github_repo("", "")


@patch(f"{PKG}.git.Repo")
@patch(f"{PKG}.Github.get_user")
@patch(f"{PKG}.Github.get_repo")
def test_make_git_repo_and_push(
    mock_getrepo: Mock, mock_getuser: Mock, mock_repo: Mock
) -> None:
    mock_getuser.return_value = Mock(login="user")

    test_repo = Mock(remotes=range(5))
    mock_repo.init.return_value = test_repo

    make_git_repo_and_push("", "", Path())

    assert mock_repo.init.call_count == 1
    assert test_repo.delete_remote.call_count == 6
    assert test_repo.create_remote.call_count == 2
    assert test_repo.git.push.call_count == 1


@patch(f"{PKG}.subprocess.run")
def test_get_gitconfig_element(mock_run: Mock) -> None:
    mock_run.side_effect = [Mock(stdout=s) for s in ["Name ", " name@email.com", ""]]
    assert get_gitconfig_element("user.name") == "Name"
    assert get_gitconfig_element("user.email") == "name@email.com"
    assert get_gitconfig_element("user.phone") is None


@patch(f"{PKG}.subprocess.run")
def test_extract_name_email(mock_run: Mock) -> None:
    mock_run.side_effect = [
        Mock(stdout=s) for s in ["Name ", " name@email.com", "Name2", ""]
    ]
    assert extract_name_email() == ("Name", "name@email.com")
    assert extract_name_email() == ("Name2", None)


@patch(f"{PKG}.typer.prompt")
def test_request_name_email(mock_prompt: Mock) -> Mock:
    mock_prompt.side_effect = ["Name", "email@email.com"]
    assert request_name_email() == ("Name", "email@email.com")


@patch(f"{PKG}.Github.get_repo")
def test_set_branch_protection_rules(mock_getrepo: Mock) -> None:
    set_branch_protection_rules("token", "repo")
    assert "repo" in mock_getrepo.call_args[0][0]
