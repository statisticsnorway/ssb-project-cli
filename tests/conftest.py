"""Global fixtures."""
import shutil
import subprocess  # noqa: S404
from pathlib import Path
from typing import Generator

import pytest
from click.testing import Result
from typer.testing import CliRunner

from ssb_project_cli.ssb_project.app import app
from ssb_project_cli.ssb_project.util import execute_command


runner = CliRunner()


@pytest.fixture(scope="module")
def git_config() -> Generator[dict[str, str], None, None]:
    """Set git config values such that ssb-project doesn't require user input."""
    config_base = ["git", "config", "--global"]
    git_config_get = config_base + ["--get"]
    git_config_set = config_base + ["--set"]
    git_config_unset = config_base + ["--unset"]
    config = {"user.name": "Johnnie Walker", "user.email": "johnnie.walker@ssb.no"}
    for key, value in config.items():
        if (
            subprocess.run(git_config_get + [key]).returncode == 1
        ):  # noqa: S603 no untrusted input
            # A '1' return code means the config value is not set. This typically
            # happens in fresh containers such as Github Actions workers. We set
            # these values so that ssb-project doesn't hang waiting for user input.
            subprocess.run(
                git_config_set + [key, value]
            )  # noqa: S603 no untrusted input

    yield config

    try:
        for key, value in config.items():
            if value in subprocess.run(git_config_get + [key]).stdout.decode(
                "utf-8"
            ):  # noqa: S603 no untrusted input
                subprocess.run(
                    git_config_unset + [key]
                )  # noqa: S603 no untrusted input
    except AttributeError:
        # No stdout returned
        pass


@pytest.fixture(scope="module")
def name() -> Path:
    """A name for the project to be created."""
    return Path("integration-test-project")


@pytest.fixture(scope="module")
def project(name: Path, git_config: dict[str, str]) -> Generator[Result, None, None]:
    """Create the project and tidy up after."""
    result = runner.invoke(app, ["create", str(name)], catch_exceptions=False)
    yield result
    # Clean up project directory
    shutil.rmtree(name)
    # Clean up project kernel
    execute_command(
        f"jupyter kernelspec remove -f {name}".split(" "),
        "clean-cmd",
        f"Deleted Jupyter kernel {name}.",
        "Error: Something went wrong while removing the jupyter kernel.",
        None,
    )
