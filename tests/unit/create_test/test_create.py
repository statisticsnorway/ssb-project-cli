"""Tests for create function."""
from unittest import TestCase
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from ssb_project_cli.ssb_project.app import create
from ssb_project_cli.ssb_project.create.create import is_valid_project_name
from ssb_project_cli.ssb_project.create.repo_privacy import RepoPrivacy
from ssb_project_cli.ssb_project.settings import STAT_TEMPLATE_DEFAULT_REFERENCE
from ssb_project_cli.ssb_project.settings import STAT_TEMPLATE_REPO_URL


CREATE = "ssb_project_cli.ssb_project.create.create"


@patch(f"{CREATE}.is_memory_full")
@patch(f"{CREATE}.create_error_log")
@patch(f"{CREATE}.rmtree", return_value=None)
@patch(f"{CREATE}.build_project", return_value=None)
@patch(f"{CREATE}.make_and_init_git_repo", return_value=None)
@patch(f"{CREATE}.create_project_from_template", return_value=None)
class TestCreateFunction(TestCase):
    """Test class create function."""

    def test_create_copy_called(
        self,
        _mock_template: Mock,
        _mock_git: Mock,
        _mock_build_project: Mock,
        mock_rmtree: Mock,
        _mock_log: Mock,
        _mock_is_memory_full: Mock,
    ) -> None:
        """Check that rmtree is not called when no sub functions raises an error."""
        create(
            "test_project",
            "description",
            RepoPrivacy.internal,
            False,
            "github_token",
            False,
            "",
            None,
            False,
        )
        assert mock_rmtree.call_count == 0

    def test_default_checkout_value_set(
        self,
        _mock_template: Mock,
        _mock_git: Mock,
        _mock_build_project: Mock,
        mock_rmtree: Mock,
        _mock_log: Mock,
        _mock_is_memory_full: Mock,
    ) -> None:
        """Check that rmtree is not called when no sub functions raises an error."""
        create(
            "test_project",
            "description",
            RepoPrivacy.internal,
            False,
            "github_token",
            False,
            STAT_TEMPLATE_REPO_URL,
            None,
            False,
        )
        assert _mock_build_project.call_args[-2][-3] == STAT_TEMPLATE_DEFAULT_REFERENCE

    def test_rmtree_template_error(
        self,
        mock_template: Mock,
        _mock_git: Mock,
        _mock_build_project: Mock,
        mock_rmtree: Mock,
        mock_log: Mock,
        _mock_is_memory_full: Mock,
    ) -> None:
        """Check that rmtree and create_error_log is called when create_project_from_template raises an Exception."""
        mock_template.side_effect = Exception("Test exception")
        with patch(f"{CREATE}.Path.is_dir", return_value=True):
            create(
                "test_project",
                "description",
                RepoPrivacy.internal,
                False,
                "github_token",
                False,
                "",
                None,
                False,
            )
        assert mock_rmtree.call_count == 1
        assert mock_log.call_count == 1

    def test_rmtree_git_error(
        self,
        _mock_template: Mock,
        mock_git: Mock,
        _mock_build_project: Mock,
        mock_rmtree: Mock,
        _mock_log: Mock,
        _mock_is_memory_full: Mock,
    ) -> None:
        """Check that rmtree is called when make_and_init_git_repo calls SystemExit."""
        mock_git.side_effect = SystemExit(1)
        with patch(f"{CREATE}.Path.is_dir", return_value=True):
            create(
                "test_project",
                "description",
                RepoPrivacy.internal,
                False,
                "github_token",
                False,
                "",
                None,
                False,
            )
        assert mock_rmtree.call_count == 1

    def test_specify_template_uri(
        self,
        _mock_template: Mock,
        mock_git: Mock,
        _mock_build_project: Mock,
        mock_rmtree: Mock,
        _mock_log: Mock,
        _mock_is_memory_full: Mock,
    ) -> None:
        """Test that specifying a different url (slightly) triggers a create and works out"""
        create(
            "test_project",
            "description",
            RepoPrivacy.internal,
            False,
            "github_token",
            False,
            "https://github.com/statisticsnorway/ssb-minimal-template",
            None,
            False,
        )
        assert mock_rmtree.call_count == 0

    @patch(f"{CREATE}.print")
    def test_project_is_lowercase_should_fail(
        self,
        mock_print: Mock,
        _mock_template: Mock,
        _mock_git: Mock,
        _mock_build_project: Mock,
        _mock_rmtree: Mock,
        _mock_log: Mock,
        _mock_is_memory_full: Mock,
    ) -> None:
        """Tests the expected print message and exit code when an invalid project name is given as input"""
        expected_print_message = "Project name cannot contain uppercase letters."
        expected_exit_code = 1

        with pytest.raises(SystemExit) as excinfo:
            create(
                "test_ProjEcT",
                "description",
                RepoPrivacy.internal,
                False,
                "github_token",
                False,
                "",
                None,
                False,
            )

        assert mock_print.call_args[0][0] == expected_print_message
        assert excinfo.value.code == expected_exit_code


@patch(f"{CREATE}.Path.exists")
def test_project_dir_exists(mock_path_exists: Mock) -> None:
    # Test that SystemExit is raised when the project directory exists
    mock_path_exists.return_value = True
    with pytest.raises(SystemExit) as excinfo:
        create(
            "test_project",
            "description",
            RepoPrivacy.internal,
            False,
            "github_token",
            False,
            "",
            None,
            False,
        )
    assert excinfo.value.code == 1


def test_is_valid_project_name() -> None:
    assert is_valid_project_name("test") == True  # noqa: E712
    assert is_valid_project_name("dapla-test") == True  # noqa: E712
    assert is_valid_project_name("123randomletters") == True  # noqa: E712

    assert is_valid_project_name("Test") == False  # noqa: E712
    assert is_valid_project_name("Should-fail") == False  # noqa: E712
    assert is_valid_project_name("123randomletteRs") == False  # noqa: E712


@patch("ssb_project_cli.ssb_project.app.create_project", return_value=None)
def test_default_options_and_types(mock_create_project: Mock) -> None:
    """Check default options andt types retuned by the create typer CLI command."""
    # Check when all optional parameters are given
    create(
        "test_project",
        "description",
        RepoPrivacy.internal,
        False,
        "github_token",
        False,
        "",
        None,
        False,
    )
    assert mock_create_project.call_count == 1
    args, _ = mock_create_project.call_args
    assert len(args) == 12
    no_kernel = args[11]
    assert isinstance(no_kernel, bool) and not no_kernel

    # Only mandatory parameters given, check default values and types of optional parameters.
    create("test_project", "description", RepoPrivacy.internal)
    assert mock_create_project.call_count == 2
    args, _ = mock_create_project.call_args
    assert len(args) == 12

    add_github = args[3]
    github_token = args[4]
    verify_config = args[10]
    template_repo_url = args[8]
    checkout = args[9]
    no_kernel = args[11]
    print(f"\ncheckout has type {type(checkout)} with content {checkout}")
    assert (
        isinstance(add_github, bool) and not add_github
    ), "add_github: Wrong type or value"
    assert (
        isinstance(github_token, str) and github_token == ""  # noqa: S105
    ), "github_token: Wrong type or value"
    assert (
        isinstance(verify_config, bool) and verify_config
    ), "verify_config: Wrong type or value"
    assert (
        isinstance(template_repo_url, str)
        and template_repo_url == STAT_TEMPLATE_REPO_URL
    ), "template_repo_url: Wrong type or value"
    assert (
        isinstance(checkout, str) and checkout == STAT_TEMPLATE_DEFAULT_REFERENCE
    ), "checkout: Wrong type or value"
    assert (
        isinstance(no_kernel, bool) and not no_kernel
    ), "no_kernel: Wrong type or value"
