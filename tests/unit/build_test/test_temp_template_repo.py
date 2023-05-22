import os
from unittest.mock import Mock
from unittest.mock import patch

from git import Repo  # type: ignore[attr-defined]

from ssb_project_cli.ssb_project.build.temp_template_repo import TempTemplateRepo
from ssb_project_cli.ssb_project.settings import STAT_TEMPLATE_DEFAULT_REFERENCE
from ssb_project_cli.ssb_project.settings import STAT_TEMPLATE_REPO_URL


@patch("ssb_project_cli.ssb_project.build.temp_template_repo.TempTemplateRepo.__exit__")
def test_temp_template_repo(exit_temp_repo_mock: Mock) -> None:
    # Create a TemplateRepo context manager object
    with TempTemplateRepo(
        STAT_TEMPLATE_REPO_URL, STAT_TEMPLATE_DEFAULT_REFERENCE
    ) as temp_repo:
        # Check that the temporary directory was created and exists
        assert os.path.exists(temp_repo.temp_dir.name)
        # Check that the Git repository was cloned to the temporary directory
        assert os.path.exists(f"{temp_repo.temp_dir.name}/.git")

        # Check that the specified tag was checked out in the cloned Git repository
        assert get_current_tag(temp_repo.repo) == STAT_TEMPLATE_DEFAULT_REFERENCE
        # Check that the name of the subdirectory of interest was set correctly
        assert temp_repo.subdir == "{{cookiecutter.project_name}}"

    # Check that the temporary directory was cleaned by checking if the mocked exit was called.
    # This avoids PermissionErrors on Windows GitHub tests.
    assert exit_temp_repo_mock.called


def get_current_tag(repo: Repo) -> str:
    """Returns the name of the tag for the current commit in the specified Git repository."""
    commit = repo.head.commit
    tags = repo.tags
    tag = next(tag for tag in tags if tag.commit == commit)
    return tag.name
