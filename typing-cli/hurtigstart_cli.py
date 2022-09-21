#!/usr/bin/python3

from typing import Optional
import typer
import os
import toml
import subprocess
import datetime

app = typer.Typer()


@app.command()
def create( projectname: str = "",
            description: str = "",
            repo_privacy: Optional[str] = "Internal",
            skip_github: Optional[bool] = False,
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
    
    typer.echo(f"Start Cookiecutter for project:{projectname}, in folder {os.getcwd()} or in dapla root?")

    if not skip_github:
        typer.echo("Create repo on github.com")

        typer.echo("Set settings on github repo")

    typer.echo("Record / log metadata about project-creation to toml-file")
    metadata_path = f"/home/jovyan/{projectname}/.ssb_project_root.toml"
    metadata = toml.load(metadata_path )
    metadata["project_creation_date"] = datetime.datetime.now().strftime(r"%Y-%m-%d")
    metadata["privacy_creation"] = repo_privacy
    metadata["skipped_github_creation"] = skip_github
    with open(metadata_path, "w") as toml_file:
        toml.dump(metadata, toml_file)


@app.command()
def build(  kernel: Optional[str] = "/opt/conda/share/jupyter/kernels/python3",
            curr_path: Optional[str] = ""
            ):
    """
    1. Check if Cruft recommends updating?
    2. Create Venv from Poetry
    3. Create kernel from venv
    4. Create workspace?
    5. Provide link to workspace?
    """
    if curr_path:
        pre_path = os.getcwd()
        os.chdir(curr_path)

    typer.echo("Recommend taking in changes from template? (date in .ssb_project_root?)")

    typer.echo("Create Venv from Poetry")

    typer.echo("Create kernal from venv")
    kernel_name = kernel_name_from_currfolder(os.getcwd())
    kernel_cmd = f"/opt/dapla/pipenv_kernel.sh create {kernel_name} {kernel}"
    output = subprocess.run(kernel_cmd.split(), check=True, capture_output=True)
    error = output.stderr
    output = output.stdout
    print("Stderr:", error)  # Implement more error handling later?
    print("Stdout:", output)

    if curr_path:
        os.chdir(pre_path)

@app.command()
def delete(name: Optional[str] = None):
    """
    1. Remove kernel
    2. Deactivate venv
    3. Remove venv / uninstall with poetry
    4. Remove workspace, if exists?
    """
    typer.echo("Remove kernel")
    os.remove("/home/jovyan/.local/share/jupyter/kernels/" + kernel_name_from_currfolder(os.getcwd()))

    typer.echo("Deactivate venv")

    typer.echo("Remove venv / uninstall with poetry")

    typer.echo("Remove workspace, if it exist")


def kernel_name_from_currfolder(curr_path: str) -> str:
    # Record for reset later
    curr_dir = os.getcwd()
    # Find root of project, and get projectname from poetry's toml-config
    while ".ssb_project_root" not in os.listdir():
        os.chdir("../")
    pyproject = toml.load("./pyproject.toml")
    name = pyproject['tool.poetry']['name']
    # Reset working directory
    os.chdir(curr_dir)
    return name



if __name__ == "__main__":
    app()