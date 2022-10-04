"""Command-line interface."""

import click

from ssb_project_cli import ssb_project


@click.command()
def main() -> None:
    """Run app"""
    ssb_project.main()


if __name__ == "__main__":
    main(prog_name="ssb-project")  # pragma: no cover
