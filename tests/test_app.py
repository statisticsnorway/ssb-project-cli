"""Tests for src/ssb_project_cli/ssb_project/app.py."""

from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from github import BadCredentialsException
from github import GithubException

from ssb_project_cli.ssb_project.app import create_github
from ssb_project_cli.ssb_project.app import create_project_from_template
from ssb_project_cli.ssb_project.app import extract_name_email
from ssb_project_cli.ssb_project.app import get_gitconfig_element
from ssb_project_cli.ssb_project.app import get_kernels_dict
from ssb_project_cli.ssb_project.app import is_github_repo
from ssb_project_cli.ssb_project.app import make_git_repo_and_push
from ssb_project_cli.ssb_project.app import mangle_url
from ssb_project_cli.ssb_project.app import projectname_from_currfolder
from ssb_project_cli.ssb_project.app import request_name_email
from ssb_project_cli.ssb_project.app import set_branch_protection_rules
from ssb_project_cli.ssb_project.app import workspace
from ssb_project_cli.ssb_project.app import workspace_uri_from_projectname


PKG = "ssb_project_cli.ssb_project.app"


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


@patch(f"{PKG}.Github.get_repo")
def test_is_github_repo(mock_get_repo: Mock) -> None:
    """Checks if is_github_repo returns/raises expected values/errors."""
    mock_get_repo.side_effect = [
        None,
        GithubException(1, None, None),
        BadCredentialsException(1, None, None),
    ]
    assert is_github_repo("", "")
    assert not is_github_repo("", "")
    with pytest.raises(ValueError):
        is_github_repo("", "")


@patch(f"{PKG}.Repo")
@patch(f"{PKG}.Github.get_user")
@patch(f"{PKG}.Github.get_repo")
def test_make_git_repo_and_push(
    mock_getrepo: Mock, mock_getuser: Mock, mock_repo: Mock
) -> None:
    """Checks that make_git_repo_and_push works.

    The git repo is mocked with 5 fake remotes to check that
    repo.delete_remote is called the expected amount of times.
    """
    mock_getuser.return_value = Mock(login="user")

    test_repo = Mock(remotes=range(5))
    mock_repo.init.return_value = test_repo

    make_git_repo_and_push("", "", Path())

    assert mock_repo.init.call_count == 1
    assert test_repo.delete_remote.call_count == 6
    assert test_repo.create_remote.call_count == 2
    assert test_repo.git.push.call_count == 1


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


@patch(f"{PKG}.subprocess.run", fake_run_gitconfig)
def test_get_gitconfig_element() -> None:
    """Checks that get_gitconfig_element works correctly."""
    # mock_run.side_effect = [Mock(stdout=s) for s in ["Name ", " name@email.com", ""]]
    assert get_gitconfig_element("user.name") == "Name"
    assert get_gitconfig_element("user.email") == "name@email.com"
    assert get_gitconfig_element("user.phone") == ""


@patch(f"{PKG}.subprocess.run")
def test_extract_name_email(mock_run: Mock) -> None:
    """Checks if extract_name_email returns the expected values."""
    mock_run.side_effect = [
        Mock(stdout=s) for s in ["Name ", " name@email.com", "Name2", ""]
    ]
    assert extract_name_email() == ("Name", "name@email.com")
    assert extract_name_email() == ("Name2", "")


@patch(f"{PKG}.typer.prompt")
def test_request_name_email(mock_prompt: Mock) -> None:
    """Checks if request_name_email returns the expected values."""
    mock_prompt.side_effect = ["Name", "email@email.com"]
    assert request_name_email() == ("Name", "email@email.com")


@patch(f"{PKG}.Github")
def test_set_branch_protection_rules(mock_github: Mock) -> None:
    """Checks if set_branch_protection_rules works.

    Just cheks whether the token is given as an argument to
    Github() and repo name to Github().get_repo.
    """
    set_branch_protection_rules("token", "repo")
    assert "token" in mock_github.call_args[0][0]


@patch(f"{PKG}.extract_name_email")
@patch(f"{PKG}.request_name_email")
def test_create_project_from_template(
    mock_request: Mock, mock_extract: Mock, tmp_path: Path
) -> None:
    """Checks if create_project_from_template works for a temporary path.

    NOTE: Kind of an integration test. Could mock away subprocess.run for pure unit test.
    """
    mock_extract.return_value = ("Name", "")
    mock_request.return_value = ("Name2", "email@email.com")
    with patch(f"{PKG}.DEFAULT_REPO_CREATE_PATH", tmp_path):
        create_project_from_template("testname", "test description")

        assert mock_extract.call_count == 1
        assert mock_request.call_count == 1

        project_dir = tmp_path.joinpath("testname")
        assert project_dir.exists()

        pyproject = project_dir.joinpath("pyproject.toml")
        assert pyproject.exists()

        with pytest.raises(ValueError):
            create_project_from_template("testname", "test description")


@patch(f"{PKG}.workspace_uri_from_projectname", return_value="")
@patch(f"{PKG}.typer.echo")
@patch(f"{PKG}.projectname_from_currfolder", return_value="")
def test_workspace(
    mock_projectname: Mock, mock_echo: Mock, mock_workspaceuri: Mock
) -> None:
    """Checks if workspace works as expected."""
    workspace()
    assert mock_echo.call_count == 3


@patch(f"{PKG}.typer.echo", lambda x: "")
@patch(f"{PKG}.debug_without_create_repo", False)
@patch(f"{PKG}.Github")
def test_create_github(mock_github: Mock) -> None:
    """Checks if create_github works."""
    create_github("token", "repo", "privacy", "desc")
    assert mock_github.call_count == 1


@patch(f"{PKG}.os")
@patch(f"{PKG}.toml.load")
def test_projectname_from_currfolder(mock_load: Mock, mock_os: Mock) -> None:
    """Checks if projectname_from_currfolder works as intended."""
    mock_os.listdir.side_effect = [["file1", "file2"], ["file3", "pyproject.toml"]]
    mock_load.return_value = {"tool": {"poetry": {"name": "projectname"}}}
    name = projectname_from_currfolder("")
    assert name == "projectname"


@patch(f"{PKG}.os.environ", {"JUPYTERHUB_USER": "test"})
def test_workspace_uri_from_projectname() -> None:
    """Checks that the URI returned by the workspace_uri_from_projectname is correct."""
    project_name = "test"
    assert (
        workspace_uri_from_projectname(project_name)
        == f"https://jupyter.dapla.ssb.no/user/test/lab/workspaces/{project_name}"
    )


@patch(f"{PKG}.subprocess.run")
def test_get_kernels_dict(mock_run: Mock) -> None:
    """Checks that get_kernels_dict correctly parses jupyter output."""
    mock_run.side_effect = [
        Mock(
            returncode=0,
            stdout=b"Available kernels:\n  python    /some/path\n  R    /other/path",
        ),
        Mock(returncode=1, stderr=b"Some error"),
    ]
    assert get_kernels_dict() == {"python": "/some/path", "R": "/other/path"}
    with pytest.raises(ValueError):
        get_kernels_dict()
