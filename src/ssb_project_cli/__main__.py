"""Command-line interface."""

from ssb_project_cli.ssb_project import app
import click


@click.command()
def main() -> None:
    """Run app."""
    app.main()


if __name__ == "__main__":
    main(prog_name="ssb-project")  # pragma: no cover
