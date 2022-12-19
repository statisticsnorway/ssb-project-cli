"""Integration tests for the create command."""
from pathlib import Path

import pytest
from click.testing import Result

from ssb_project_cli.ssb_project.clean.clean import get_kernels_dict


def test_create_exit_code(project: Result) -> None:
    """Create command returns 0 exit code."""
    assert project.exit_code == 0


@pytest.mark.parametrize(
    "expected_path", [".gitattributes", ".cruft.json", "poetry.lock"]
)
def test_create_project_files_created(
    name: Path, project: Result, expected_path: Path
) -> None:
    """Expected files created."""
    assert (name / expected_path).exists()


def test_create_kernel_installed(name: Path, project: Result) -> None:
    """Kernel successfully installed."""
    assert str(name) in get_kernels_dict()
