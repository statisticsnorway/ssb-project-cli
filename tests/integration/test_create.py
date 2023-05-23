"""Integration tests for the create command."""
import shutil
import subprocess
from pathlib import Path
from typing import Generator

import pytest
from click.testing import Result
from typer.testing import CliRunner

from ssb_project_cli.ssb_project.app import app
from ssb_project_cli.ssb_project.clean.clean import get_kernels_dict


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
    # Clean up project directory
    shutil.rmtree(name)
    # Clean up project kernel
    subprocess.run(f"jupyter kernelspec remove -f {name}".split(" "))


def test_create_exit_code(create_project: Result) -> None:
    """Create command returns 0 exit code."""
    assert create_project.exit_code == 0


@pytest.mark.parametrize(
    "expected_path", [".gitattributes", ".cruft.json", "poetry.lock"]
)
def test_create_project_files_created(
    name: Path, create_project: Result, expected_path: Path
) -> None:
    """Expected files created."""
    assert (name / expected_path).exists()


def test_create_kernel_installed(name: Path, create_project: Result) -> None:
    """Kernel successfully installed."""
    assert str(name) in get_kernels_dict()
