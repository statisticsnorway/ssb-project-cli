"""This module provides the TempTemplateRepo context manager, which can be used to clone a Git repository to a temporary directory and checkout a specific tag."""
from tempfile import TemporaryDirectory
from types import TracebackType
from typing import Optional
from typing import Type

from git import Repo  # type: ignore[attr-defined]


class TempTemplateRepo:
    """A context manager that clones a Git repository to a temporary directory and checks out a specific tag."""

    def __init__(self, template_repo_url: str, checkout: str | None) -> None:
        """Initializes a new TemplateRepo object with the specified template_repo_url and checkout attributes."""
        self.template_repo_url = template_repo_url
        self.checkout = checkout

    def __enter__(self) -> "TempTemplateRepo":
        """Clones the template repository specified by template_repo_url to a temporary directory and checks out the tag specified by checkout."""
        self.temp_dir = TemporaryDirectory()

        # clone the repository
        self.repo = Repo.clone_from(self.template_repo_url, self.temp_dir.name)

        if self.checkout:
            # checkout the specific tag you're interested in
            self.repo.git.checkout(self.checkout)

        self.subdir = "{{cookiecutter.project_name}}"

        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Cleans up the temporary directory created containing the template repository."""
        self.temp_dir.cleanup()
