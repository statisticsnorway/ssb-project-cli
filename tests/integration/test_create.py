"""Integration tests for the create command."""
import shutil
from pathlib import Path
from typing import Generator

import pytest
from click.testing import Result
from typer.testing import CliRunner

from ssb_project_cli.ssb_project.app import app
from ssb_project_cli.ssb_project.clean.clean import get_kernels_dict
from ssb_project_cli.ssb_project.util import execute_command


runner = CliRunner()

NAME = Path("integration-test-project")


@pytest.fixture(scope="module")
def project() -> Generator[Result, None, None]:
    result = runner.invoke(app, ["create", str(NAME)], catch_exceptions=False)
    yield result
    # Clean up project directory
    shutil.rmtree(NAME)
    # Clean up project kernel
    execute_command(
        f"jupyter kernelspec remove -f {NAME}".split(" "),
        "clean-cmd",
        f"Deleted Jupyter kernel {NAME}.",
        "Error: Something went wrong while removing the jupyter kernel.",
        None,
    )


def test_create_exit_code(project: Result) -> None:
    """Create command returns 0 exit code."""
    assert project.exit_code == 0


@pytest.mark.parametrize(
    "expected_path", [".gitattributes", ".cruft.json", "poetry.lock"]
)
def test_create_project_files_created(project: Result, expected_path: Path) -> None:
    """Expected files created."""
    assert (NAME / expected_path).exists()


def test_create_kernel_installed(project: Result) -> None:
    """Expected files created."""
    assert str(NAME) in get_kernels_dict()
