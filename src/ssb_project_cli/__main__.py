"""Command-line interface."""

from ssb_project_cli import ssb_project
import click


@click.command()
def main() -> None:
    """Run app"""
    ssb_project.main()


if __name__ == "__main__":
    main(prog_name="ssb-project")  # pragma: no cover
