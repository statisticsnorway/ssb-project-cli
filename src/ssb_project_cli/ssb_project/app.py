"""Command-line-interface for project-operations in dapla-jupterlab."""

import typing as t
from pathlib import Path

import typer
from rich.console import Console
from typing_extensions import Annotated

from ssb_project_cli.ssb_project.util import set_debug_logging

from .build.build import build_project
from .clean.clean import clean_project
from .create.create import create_project
from .create.repo_privacy import RepoPrivacy
from .settings import CURRENT_WORKING_DIRECTORY
from .settings import GITHUB_ORG_NAME
from .settings import HOME_PATH
from .settings import STAT_TEMPLATE_DEFAULT_REFERENCE
from .settings import STAT_TEMPLATE_REPO_URL
from .util import handle_no_kernel_argument


# Don't print with color, it's difficult to read when run in Jupyter
typer.rich_utils.STYLE_OPTION = ""
typer.rich_utils.STYLE_SWITCH = ""
typer.rich_utils.STYLE_NEGATIVE_OPTION = ""
typer.rich_utils.STYLE_NEGATIVE_SWITCH = ""
typer.rich_utils.STYLE_METAVAR = ""
typer.rich_utils.STYLE_METAVAR_SEPARATOR = "dim"
typer.rich_utils.STYLE_USAGE = ""
typer.rich_utils.STYLE_USAGE_COMMAND = "bold"
typer.rich_utils.STYLE_DEPRECATED = ""
typer.rich_utils.STYLE_DEPRECATED_COMMAND = "dim"
typer.rich_utils.STYLE_HELPTEXT_FIRST_LINE = ""
typer.rich_utils.STYLE_HELPTEXT = ""
typer.rich_utils.STYLE_OPTION_HELP = ""
typer.rich_utils.STYLE_OPTION_DEFAULT = "dim"
typer.rich_utils.STYLE_OPTION_ENVVAR = "dim"
typer.rich_utils.STYLE_REQUIRED_SHORT = ""
typer.rich_utils.STYLE_REQUIRED_LONG = ""
typer.rich_utils.STYLE_OPTIONS_PANEL_BORDER = "dim"
console = Console(color_system=None)
print = console.print

app = typer.Typer(
    help="Usage instructions: https://manual.dapla.ssb.no/ssbproject.html",
    rich_markup_mode="rich",
    pretty_exceptions_show_locals=False,  # Locals can contain sensitive information
)


@app.command()
def create(  # noqa: C901, S107
    project_name: str = typer.Argument(..., help="Project name"),  # noqa: B008
    description: str = typer.Argument(  # noqa: B008
        "", help="A short description of your project"
    ),
    repo_privacy: RepoPrivacy = typer.Argument(  # noqa: B008
        RepoPrivacy.internal, help="Visibility of the Github repo"
    ),
    add_github: Annotated[
        bool, typer.Option("--github", help="Create the repo on Github as well")
    ] = False,
    github_token: Annotated[
        str,
        typer.Option(
            help="Your Github Personal Access Token, follow these instructions to create one: https://manual.dapla.ssb.no/git-github.html#personal-access-token-pat"
        ),
    ] = "",
    verify_config: Annotated[
        bool,
        typer.Option(
            "--no-verify",
            help="Verify git configuration files. Use --no-verify to disable verification (defaults to True).",
        ),
    ] = True,
    template_git_url: Annotated[
        str, typer.Option(help="The Cookiecutter template URI.")
    ] = STAT_TEMPLATE_REPO_URL,
    checkout: Annotated[
        t.Optional[str],
        typer.Option(
            help="The git reference to check against. Supports branches, tags and commit hashes.",
        ),
    ] = None,
    name: Annotated[
        t.Optional[str], typer.Option("--name", help="Project author's full name.")
    ] = None,
    email: Annotated[
        t.Optional[str], typer.Option("--email", help="Project author's email.")
    ] = None,
    no_kernel: Annotated[
        bool,
        typer.Option(
            "--no-kernel",
            help="Do not create a kernel after the project is created (defaults to False).",
        ),
    ] = False,
) -> None:
    """:sparkles:  Create a project locally, and optionally on GitHub with the flag --github. The project will follow SSB's best practice for development."""
    if not checkout and template_git_url is STAT_TEMPLATE_REPO_URL:
        checkout = STAT_TEMPLATE_DEFAULT_REFERENCE

    create_project(
        project_name,
        description,
        repo_privacy,
        add_github,
        github_token,
        CURRENT_WORKING_DIRECTORY,
        HOME_PATH,
        GITHUB_ORG_NAME,
        template_git_url,
        checkout,
        name,
        email,
        verify_config,
        handle_no_kernel_argument(no_kernel),
    )


@app.command()
def build(
    path: t.Optional[Path] = typer.Argument(  # noqa: B008
        None,
        help="Project path",
    ),
    verify_config: bool = typer.Option(  # noqa: B008
        True,
        "--no-verify",
        help="Verify git configuration files. Use --no-verify to disable verification (defaults to True).",
        show_default=True,
    ),
    no_kernel: Annotated[
        bool,
        typer.Option(
            "--no-kernel",
            help="Do not install a kernel after the project is built (defaults to False).",
        ),
    ] = False,
) -> None:
    """:wrench:  Create a virtual environment and corresponding Jupyter kernel. Runs in the current folder if no arguments are supplied."""
    build_project(
        path,
        CURRENT_WORKING_DIRECTORY,
        STAT_TEMPLATE_REPO_URL,
        STAT_TEMPLATE_DEFAULT_REFERENCE,
        verify_config,
        handle_no_kernel_argument(no_kernel),
    )


@app.command()
def clean(
    project_name: str = typer.Argument(  # noqa: B008
        ..., help="The name of the project/kernel you want to delete."
    )
) -> None:
    """:broom:  Delete the kernel for the given project name."""
    clean_project(project_name)


def main() -> None:
    """Main function of ssb_project_cli."""
    set_debug_logging()
    app(prog_name="ssb-project")  # pragma: no cover


if __name__ == "__main__":
    main()  # pragma: no cover
