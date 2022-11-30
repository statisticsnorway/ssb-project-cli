"""This module contains the TempGitRemote class."""
from types import TracebackType
from typing import Optional
from typing import Type

from git import Repo  # type: ignore[attr-defined]


class TempGitRemote:
    """Context manager class for creating and cleaning up a temporary git remote."""

    def __init__(self, repo: Repo, temp_url: str, restore_url: str) -> None:
        """Inits a TempGitRepo.

        Args:
            repo: Git repository
            temp_url: Temp url
            restore_url: Restore url
        """
        self.repo = repo
        self.temp_url = temp_url
        self.restore_url = restore_url

    def __enter__(self) -> None:
        """Deletes remote in Repository and creates remote at temp_url."""
        for remote in self.repo.remotes:
            self.repo.delete_remote(remote)
        self.origin = self.repo.create_remote("origin", self.temp_url)
        return None

    # Look up
    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Deletes remote self.origin and creates a remote named origin with an url."""
        self.repo.delete_remote(self.origin)
        self.repo.create_remote("origin", self.restore_url)
