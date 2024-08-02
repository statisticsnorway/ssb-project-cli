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
    result = runner.invoke(
        app, ["create", str(name), "--no-verify"], catch_exceptions=False
    )
    yield result
    print(result.stdout)
    # Clean up project directory
    shutil.rmtree(name)
    # Clean up project kernel
    subprocess.run(f"jupyter kernelspec remove -f {name}".split(" "))


@pytest.fixture(scope="module")
def build_project(create_project: dict[str, str]) -> Result:
    return runner.invoke(app, ["build", "--no-verify"], catch_exceptions=False)


def test_build_project_exit_code(build_project: Result) -> None:
    if build_project.exit_code != 0:
        with open(
            "/home/runner/ssb-project-cli/.error_logs/poetry-install-error-1722599691.txt",
            encoding="utf-8",
        ) as f:
            error_logs = f.read()
            print(error_logs)
    assert build_project.exit_code == 0
