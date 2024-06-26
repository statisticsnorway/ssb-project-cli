"""Global fixtures."""

import subprocess  # noqa: S404
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture(scope="module")
def git_config() -> Generator[dict[str, str], None, None]:
    """Set git config values such that ssb-project doesn't require user input."""
    config_base = ["git", "config", "--global"]
    git_config_get = config_base + ["--get"]
    git_config_unset = config_base + ["--unset"]
    config = {"user.name": "Johnnie Walker", "user.email": "johnnie.walker@ssb.no"}
    for key, value in config.items():
        if subprocess.run(git_config_get + [key]).returncode == 1:
            # A '1' return code means the config value is not set. This typically
            # happens in fresh containers such as Github Actions workers. We set
            # these values so that ssb-project doesn't hang waiting for user input.
            subprocess.run(config_base + [key, value])

    yield config

    try:
        for key, value in config.items():
            # If we have set values to our known test values, unset them once we're done
            if value in subprocess.run(git_config_get + [key]).stdout.decode("utf-8"):
                subprocess.run(git_config_unset + [key])
    except AttributeError:
        # No stdout returned
        pass


@pytest.fixture(scope="module")
def name() -> Path:
    """A name for the project to be created."""
    return Path("integration-test-project")
