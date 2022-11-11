"""Tests for delete_folder function."""
import shutil
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock
from unittest.mock import patch

from ssb_project_cli.ssb_project.app import delete_folder
from tests.test_app import PKG


@patch(f"{PKG}.create_error_log")
@patch(f"{PKG}.Path.is_dir")
@patch(f"{PKG}.rmtree")
class TestCreateFunction(TestCase):
    """Test class for delete_folder function."""

    def test_delete_folder_is_dir(
        self, mock_rmtree: Mock, mock_isdir: Mock, mock_log: Mock
    ) -> None:
        """Test that mock_rmtree is called if folder exist."""
        mock_isdir.side_effect = [True]

        delete_folder(Path())
        assert mock_isdir.call_count == 1
        assert mock_rmtree.call_count == 1
        assert mock_log.call_count == 0

    def test_delete_folder_not_dir(
        self, mock_rmtree: Mock, mock_isdir: Mock, mock_log: Mock
    ) -> None:
        """Test that mock_rmtree and mock_log is not called if folder does not exist."""
        mock_isdir.side_effect = [False]

        delete_folder(Path())
        assert mock_isdir.call_count == 1
        assert mock_rmtree.call_count == 0
        assert mock_log.call_count == 0

    def test_delete_folder_log_shutil_error(
        self, mock_rmtree: Mock, mock_isdir: Mock, mock_log: Mock
    ) -> None:
        """Tests that logging is done if a shutil.Error is raised."""
        mock_isdir.side_effect = [True]
        mock_rmtree.side_effect = shutil.Error()

        delete_folder(Path())
        assert mock_isdir.call_count == 1
        assert mock_rmtree.call_count == 1
        assert mock_log.call_count == 1
