"""Tests for create function."""
from unittest import TestCase
from unittest.mock import Mock
from unittest.mock import patch

from ssb_project_cli.ssb_project.app import create
from ssb_project_cli.ssb_project.create.repo_privacy import RepoPrivacy


CREATE = "ssb_project_cli.ssb_project.create.create"


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
    ) -> None:
        """Check that rmtree is not called when no sub functions raises an error."""
        create(
            "test_project", "description", RepoPrivacy.internal, False, "github_token"
        )
        assert mock_rmtree.call_count == 0

    def test_rmtree_template_error(
        self,
        mock_template: Mock,
        _mock_git: Mock,
        _mock_build_project: Mock,
        mock_rmtree: Mock,
        mock_log: Mock,
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
            )
        assert mock_rmtree.call_count == 1
