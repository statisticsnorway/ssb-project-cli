import sys
from pathlib import Path

from ssb_project_cli.ssb_project.poetry import poetry_relax_upgrade
from ssb_project_cli.ssb_project.util import get_project_name_and_root_path


def upgrade_project(
    path: Path | None,
    working_directory: Path,
) -> None:
    if path is None:
        project_directory = working_directory
    else:
        project_directory = working_directory / path

    project_name, project_root = get_project_name_and_root_path(project_directory)

    if project_name is None or project_root is None:
        print(
            ":x:\tCould not find project root. Please run ssb-project within a project directory."
        )
        sys.exit()
    poetry_relax_upgrade(project_root)
