"""Integration tests for the build command."""
import shutil
import subprocess
from pathlib import Path
from typing import Generator

import pytest
from click.testing import Result
from typer.testing import CliRunner

from ssb_project_cli.ssb_project.app import app


runner = CliRunner()


@pytest.fixture(scope="module")
def create_project(
    name: Path, git_config: dict[str, str]
) -> Generator[Result, None, None]:
    """Create the project and tidy up after."""
    result = runner.invoke(app, ["create", str(name)], catch_exceptions=False)
    yield result
    # Clean up project directory
    shutil.rmtree(name)
    # Clean up project kernel
    subprocess.run(f"jupyter kernelspec remove -f {name}".split(" "))


@pytest.fixture(scope="module")
def build_project(create_project: dict[str, str]) -> Result:
    return runner.invoke(app, ["build"], catch_exceptions=False)


def test_build_project_exit_code(build_project: Result) -> None:
    assert build_project.exit_code == 0
