"""Command-line interface."""

from dapla_hurtigstart_cli.hurtigstart import hurtigstart_cli


def main() -> None:
    """Hurtigstart."""
    hurtigstart_cli.main()


if __name__ == "__main__":
    main(prog_name="hurtigstart")  # pragma: no cover
