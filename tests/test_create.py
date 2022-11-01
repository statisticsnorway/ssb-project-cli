"""Tests for create function."""
from unittest import TestCase
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from ssb_project_cli.ssb_project.app import create
from tests.test_app import PKG


@patch(f"{PKG}.copytree", return_value=None)
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
        mock_copy: Mock,
    ) -> None:
        """Check if copytree is called when no sub functions raises an error."""
        create("test_project", "description", add_github=False)
        assert mock_copy.call_count == 1

    def test_no_copy_template_error(
        self,
        mock_template: Mock,
        _mock_git: Mock,
        _mock_kernel: Mock,
        _mock_install: Mock,
        mock_copy: Mock,
    ) -> None:
        """Check that copytree is not called when create_project_from_template raises an error."""
        mock_template.side_effect = ValueError("template failing")
        with pytest.raises(ValueError):
            create("test_project", "description", add_github=False)
        assert mock_copy.call_count == 0

    def test_no_copy_git_error(
        self,
        _mock_template: Mock,
        mock_git: Mock,
        _mock_kernel: Mock,
        _mock_install: Mock,
        mock_copy: Mock,
    ) -> None:
        """Check that copytree is not called when make_and_init_git_repo raises an error."""
        mock_git.side_effect = ValueError("git failing")
        with pytest.raises(ValueError):
            create("test_project", "description", add_github=False)
        assert mock_copy.call_count == 0
