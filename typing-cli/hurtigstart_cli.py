from typing import Optional
import typer

app = typer.Typer()


@app.command()
def create( projectname: str = "",
            description: str = "",
            repo_privacy: Optional[str] = "Internal"
                                ):
    """
    1. Start Cookiecutter which requests inputs from user
    2. Create Repo under Statistics Norway (ask for access token at this point)
    3. Set recommended settings on github repo
    4. Add metadata about creation to .ssb_project_root ?
    """
    repo_privacy = repo_privacy.lower()
    accepted_repo_privacy = ["internal", "public", "private"]
    if repo_privacy not in accepted_repo_privacy:
        raise ValueError(f"Access {repo_privacy} not among accepted accesses: {*accepted_repo_privacy,}")

    typer.echo(f"Start Cookiecutter for project:{projectname}")

    typer.echo("Create repo on github.com")

    typer.echo("Set settings on github repo")

    typer.echo("Record / log metadata about creation")


@app.command()
def build(path: Optional[str] = ""):
    """
    1. Check if Cruft recommends updating?
    2. Create Venv from Poetry
    3. Create kernel from venv
    4. Create workspace?
    5. Provide link to workspace?
    """
    typer.echo("Recommend taking in changes from template? (date in .ssb_project_root?)")

    typer.echo("Create Venv from Poetry")

    typer.echo("Create kernal from venv")

@app.command()
def delete(name: Optional[str] = None):
    """
    1. Remove kernel
    2. Deactivate venv
    3. Remove venv / uninstall with poetry
    4. Remove workspace, if exists?
    """
    typer.echo("Remove kernel")

    typer.echo("Deactivate venv")

    typer.echo("Remove venv / uninstall with poetry")

    typer.echo("Remove workspace, if it exists?")

if __name__ == "__main__":
    app()