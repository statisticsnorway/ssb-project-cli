"""Tests for local_repo module."""
import json
from pathlib import Path
from random import randint
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from ssb_project_cli.ssb_project.create.github import valid_repo_name
from ssb_project_cli.ssb_project.create.local_repo import create_project_from_template
from ssb_project_cli.ssb_project.create.local_repo import extract_name_email
from ssb_project_cli.ssb_project.create.local_repo import get_gitconfig_element
from ssb_project_cli.ssb_project.create.local_repo import make_git_repo_and_push
from ssb_project_cli.ssb_project.create.local_repo import mangle_url
from ssb_project_cli.ssb_project.settings import STAT_TEMPLATE_DEFAULT_REFERENCE
from ssb_project_cli.ssb_project.settings import STAT_TEMPLATE_REPO_URL


LOCAL_REPO = "ssb_project_cli.ssb_project.create.local_repo"


@pytest.mark.parametrize(
    "name,expected",
    [
        ("word", True),
        ("words-with-hyphens", True),
        ("words_with_underscores", True),
        ("non-ascii-$%&", False),
        ("norwegian-characters-æøå", False),
        ("words with spaces", False),
        ("hi", False),
    ],
)
def test_valid_repo_name(name: str, expected: bool) -> None:
    """Checks a range of valid and invalid repo names."""
    assert valid_repo_name(name) == expected


@pytest.mark.parametrize(
    "url,mangle,expected",
    [
        ("ssh://example.com", "test", "ssh://test@example.com"),
        ("git://github.com/etc", "user", "git://user@github.com/etc"),
    ],
)
def test_mangle_url(url: str, mangle: str, expected: str) -> None:
    """Checks if mangle_url returns the correct mangled string."""
    assert mangle_url(url, mangle) == expected


@patch(f"{LOCAL_REPO}.temp_git_repo.Repo")
@patch(f"{LOCAL_REPO}.get_environment_specific_github_object")
@patch(f"{LOCAL_REPO}.make_and_init_git_repo")
def test_make_git_repo_and_push(
    mock_make_and_init_git_repo: Mock,
    mock_get_environment_specific_github_object: Mock,
    mock_repo: Mock,
) -> None:
    """Checks that make_git_repo_and_push works.

    The git repo is mocked with 5 fake remotes to check that
    repo.delete_remote is called the expected amount of times.
    """
    mock_get_environment_specific_github_object.get_user.return_value = Mock(
        login="user"
    )

    test_repo = Mock(remotes=range(5))
    mock_make_and_init_git_repo.return_value = test_repo
    mock_repo.init.return_value = test_repo

    make_git_repo_and_push("", "", Path())

    assert mock_make_and_init_git_repo.call_count == 1
    assert test_repo.delete_remote.call_count == 6
    assert test_repo.create_remote.call_count == 2
    assert test_repo.git.push.call_count == 1


@patch(f"{LOCAL_REPO}.temp_git_repo.Repo")
@patch(f"{LOCAL_REPO}.get_environment_specific_github_object")
@patch(f"{LOCAL_REPO}.make_and_init_git_repo")
def test_make_and_repo_and_push(
    mock_make_and_init_git_repo: Mock,
    mock_get_environment_specific_github_object: Mock,
    mock_repo: Mock,
) -> None:
    """Checks that make_git_repo_and_push works.

    The git repo is mocked with 5 fake remotes to check that
    repo.delete_remote is called the expected amount of times.
    """
    mock_get_environment_specific_github_object.get_user.return_value = Mock(
        login="user"
    )

    test_repo = Mock(remotes=range(5))
    mock_make_and_init_git_repo.return_value = test_repo
    mock_repo.init.return_value = test_repo

    make_git_repo_and_push("", "", Path())

    assert mock_make_and_init_git_repo.call_count == 1
    assert test_repo.delete_remote.call_count == 6
    assert test_repo.create_remote.call_count == 2
    assert test_repo.git.push.call_count == 1


"""
@patch(f"{LOCAL_REPO}.Repo.git.branch")
@patch(f"{LOCAL_REPO}.Repo.index")
@patch(f"{LOCAL_REPO}.Repo.git.add")
@patch(f"{LOCAL_REPO}.Repo.init")
def test_make_and_init_git_repo(mock_repo_init: Mock,mock_repo_add: Mock,mock_commit: Mock,mock_branch: Mock):
    make_and_init_git_repo("/Users/anders/test/tt")
    assert mock_repo_init.call_count == 1
    assert mock_repo_add.call_count == 1
    assert mock_commit.call_count == 1
    assert mock_branch.call_count == 2
"""


def fake_run_gitconfig(cmd: list[str], stdout: int, encoding: str) -> Mock:
    """Emulates subprocess.run for git config --get."""
    vals = {
        "user.name": "Name",
        "user.email": "name@email.com",
    }
    key = cmd[-1]
    if key not in vals:
        return Mock(stdout="")
    return Mock(stdout=vals[key])


@patch(f"{LOCAL_REPO}.subprocess.run", fake_run_gitconfig)
def test_get_gitconfig_element() -> None:
    """Checks that get_gitconfig_element works correctly."""
    assert get_gitconfig_element("user.name") == "Name"
    assert get_gitconfig_element("user.email") == "name@email.com"
    assert get_gitconfig_element("user.phone") == ""


@patch(f"{LOCAL_REPO}.subprocess.run")
def test_extract_name_email(mock_run: Mock) -> None:
    """Checks if extract_name_email returns the expected values."""
    mock_run.side_effect = [
        Mock(stdout=s) for s in ["Name ", " name@email.com", "Name2", ""]
    ]
    assert extract_name_email() == ("Name", "name@email.com")
    assert extract_name_email() == ("Name2", "")


@patch(f"{LOCAL_REPO}.extract_name_email")
@patch(f"{LOCAL_REPO}.request_name_email")
def test_create_project_from_template(
    mock_request: Mock, mock_extract: Mock, tmp_path: Path
) -> None:
    """Checks if create_project_from_template works for a temporary path.

    NOTE: Kind of an integration test. Could mock away subprocess.run for pure unit test.
    """
    mock_extract.return_value = ("Name", "")
    mock_request.return_value = ("Name2", "email@email.com")

    create_project_from_template(
        "testname",
        "test description",
        STAT_TEMPLATE_REPO_URL,
        STAT_TEMPLATE_DEFAULT_REFERENCE,
        tmp_path,
    )

    assert mock_extract.call_count == 1
    assert mock_request.call_count == 1

    project_dir = tmp_path.joinpath("testname")
    assert project_dir.exists()

    pyproject = project_dir.joinpath("pyproject.toml")
    assert pyproject.exists()


@patch(f"{LOCAL_REPO}.extract_name_email")
@patch(f"{LOCAL_REPO}.request_name_email")
@patch(f"{LOCAL_REPO}.subprocess.run")
def test_create_project_from_template_license_year(
    mock_run: Mock, mock_request: Mock, mock_extract: Mock, tmp_path: Path
) -> None:
    """Verify that we supply the license year to Cruft"""
    mock_extract.return_value = ("Name", "")
    mock_request.return_value = ("Name2", "email@email.com")
    license_year = str(randint(1000, 3000))  # noqa: S311 non-cryptographic use
    project_name = "testname"
    create_project_from_template(
        project_name,
        "test description",
        STAT_TEMPLATE_REPO_URL,
        STAT_TEMPLATE_DEFAULT_REFERENCE,
        tmp_path,
        license_year,
    )
    mock_run_call_args = mock_run.call_args.args
    cruft_args = json.loads(mock_run_call_args[-1][-1])
    assert cruft_args["license_year"] == license_year
    assert cruft_args["project_name"] == project_name


@patch(f"{LOCAL_REPO}.extract_name_email")
@patch(f"{LOCAL_REPO}.request_name_email")
@patch(f"{LOCAL_REPO}.subprocess.run")
def test_create_project_from_template_different_template_uri(
    mock_run: Mock, mock_request: Mock, mock_extract: Mock, tmp_path: Path
) -> None:
    """Check that different template uri works"""
    mock_extract.return_value = ("Name", "")
    mock_request.return_value = ("Name2", "email@email.com")
    license_year = str(randint(1000, 3000))  # noqa: S311 non-cryptographic use
    project_name = "testname"
    create_project_from_template(
        project_name,
        "test description",
        "https://github.com/statisticsnorway/ssb-minimal-template",
        STAT_TEMPLATE_DEFAULT_REFERENCE,
        tmp_path,
        license_year,
    )
    mock_run_call_args = mock_run.call_args.args
    cruft_args = json.loads(mock_run_call_args[-1][-1])
    assert cruft_args["license_year"] == license_year
    assert cruft_args["project_name"] == project_name