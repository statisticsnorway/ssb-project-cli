"""This module provides the TempTemplateRepo context manager, which can be used to clone a Git repository to a temporary directory and checkout a specific tag."""
import os
import shutil
import stat
from tempfile import TemporaryDirectory
from types import TracebackType
from typing import Optional
from typing import Type

from git import Repo  # type: ignore[attr-defined]


class TempTemplateRepo:
    """A context manager that clones a Git repository to a temporary directory and checks out a specific tag."""

    def __init__(self, template_repo_url: str, template_reference: str) -> None:
        """Initializes a new TemplateRepo object with the specified template_repo_url and template_reference attributes."""
        self.template_repo_url = template_repo_url
        self.template_reference = template_reference

    def __enter__(self) -> "TempTemplateRepo":
        """Clones the template repository specified by template_repo_url to a temporary directory and checks out the tag specified by template_reference."""
        self.temp_dir = TemporaryDirectory()

        # clone the repository
        self.repo = Repo.clone_from(self.template_repo_url, self.temp_dir.name)

        # checkout the specific tag you're interested in
        self.repo.git.checkout(self.template_reference)

        self.subdir = "{{cookiecutter.project_name}}"

        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Cleans up the temporary directory created containing the template repository."""
        # Workaround for https://bugs.python.org/issue26660
        self._unset_readonly_recursive()
        shutil.rmtree(self.temp_dir.name)

    def _unset_readonly_recursive(self) -> None:
        """Unset the read-only bit for files and directories in the temporary directory.

        This fixes the https://bugs.python.org/issue26660 issue in windows tests.
        """
        for root, dirs, files in os.walk(str(self.temp_dir)):
            for directory in dirs:
                directory_path = os.path.join(root, directory)
                os.chmod(directory_path, stat.S_IWRITE)

            for file in files:
                file_path = os.path.join(root, file)
                os.chmod(file_path, stat.S_IWRITE)
