"""Tests for create function."""
from unittest import TestCase
from unittest.mock import Mock
from unittest.mock import patch

from ssb_project_cli.ssb_project.app import create
from tests.test_app import PKG


@patch(f"{PKG}.running_onprem", return_value=False)
@patch(f"{PKG}.poetry_source_includes_source_name", return_value=False)
@patch(f"{PKG}.poetry_source_add")
@patch(f"{PKG}.poetry_source_remove")
@patch(f"{PKG}.rmtree", return_value=None)
@patch(f"{PKG}.poetry_install", return_value=None)
@patch(f"{PKG}.install_ipykernel", return_value=None)
@patch(f"{PKG}.make_and_init_git_repo", return_value=None)
@patch(f"{PKG}.create_project_from_template", return_value=None)
class TestCreateFunction(TestCase):
    """Test class create function."""

    def test_create_copy_called(
        self,
        _mock_template: Mock,
        _mock_git: Mock,
        _mock_kernel: Mock,
        _mock_install: Mock,
        mock_rmtree: Mock,
        _mock_poetry_source_remove: Mock,
        _mock_poetry_source_add: Mock,
        _mock_poetry_source_includes_source_name: Mock,
        _mock_running_onprem: Mock,
    ) -> None:
        """Check if copytree is called when no sub functions raises an error."""
        create("test_project", "description", add_github=False)
        assert mock_rmtree.call_count == 0

    def test_rmtree_template_error(
        self,
        mock_template: Mock,
        _mock_git: Mock,
        _mock_kernel: Mock,
        _mock_install: Mock,
        mock_rmtree: Mock,
        _mock_poetry_source_remove: Mock,
        _mock_poetry_source_add: Mock,
        _mock_poetry_source_includes_source_name: Mock,
        _mock_running_onprem: Mock,
    ) -> None:
        """Check that copytree is not called when create_project_from_template raises an error."""
        mock_template.side_effect = SystemExit(1)
        with patch(f"{PKG}.Path.is_dir", return_value=True):
            create("test_project", "description", add_github=False)
        assert mock_rmtree.call_count == 1

    def test_rmtree_git_error(
        self,
        _mock_template: Mock,
        mock_git: Mock,
        _mock_kernel: Mock,
        _mock_install: Mock,
        mock_rmtree: Mock,
        _mock_poetry_source_remove: Mock,
        _mock_poetry_source_add: Mock,
        _mock_poetry_source_includes_source_name: Mock,
        _mock_running_onprem: Mock,
    ) -> None:
        """Check that copytree is not called when make_and_init_git_repo raises an error."""
        mock_git.side_effect = SystemExit(1)
        with patch(f"{PKG}.Path.is_dir", return_value=True):
            create("test_project", "description", add_github=False)
        assert mock_rmtree.call_count == 1
