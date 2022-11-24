"""Tests for create_github function."""
from unittest import TestCase
from unittest.mock import Mock
from unittest.mock import patch

import pytest
import requests

from ssb_project_cli.ssb_project.app import RepoPrivacy
from ssb_project_cli.ssb_project.app import create_github
from tests.test_app import PKG


def mock_response(status_code: int, mock_request: Mock) -> None:
    """Sets status code of the mocked request´s response object"""
    response = requests.Response()
    response.status_code = status_code
    mock_request.return_value = response


@patch(f"{PKG}.create_error_log")
@patch(f"{PKG}.requests.post")
@patch(f"{PKG}.Github.get_repo")
class TestCreateGithubFunction(TestCase):
    """Test class create_github function."""

    def test_create_github_(
        self, mock_github_get_repo: Mock, mock_request: Mock, mock_log: Mock
    ) -> None:
        """Checks if create_github works."""
        mock_response(201, mock_request)

        create_github("token", "name", RepoPrivacy.internal, "desc")
        assert mock_request.call_count == 1
        assert mock_log.call_count == 0
        assert mock_github_get_repo.call_count == 1

    def test_create_github(
        self, mock_github_get_repo: Mock, mock_request: Mock, mock_log: Mock
    ) -> None:
        """Checks if create_github exits and logs when response is not 201."""
        mock_response(404, mock_request)

        with pytest.raises(SystemExit):
            create_github("token", "name", RepoPrivacy.internal, "desc")
        assert mock_request.call_count == 1
        assert mock_log.call_count == 1
        assert mock_github_get_repo.call_count == 0
