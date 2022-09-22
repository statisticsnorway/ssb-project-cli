#!/usr/bin/python3

import datetime
import os
import subprocess
from pathlib import Path
from typing import Optional

import git
import toml
import typer
from github import BadCredentialsException, Github, GithubException

app = typer.Typer()
org_name = "statisticsnorway"
debug_without_create_repo = True


def is_github_repo(token: str, repo_name: str) -> bool:
    try:
        Github(token).get_repo(f"{org_name}/{repo_name}")
    except BadCredentialsException:
        raise ValueError("Bad GitHub Credentials.")
    except GithubException:
        return False
    else:
        return True


def mangle_url(url: str, mangle_name: str) -> str:
    """Create url mangled with a string: credential or username."""
    mangle_name = mangle_name + "@"
    split_index = url.find("//") + 2
    return url[:split_index] + mangle_name + url[split_index:]


class TempGitRemote:
    """Context manager class for creating and cleaning up a temporary git remote."""

    def __init__(self, repo: git.Repo, temp_url: str, restore_url: str) -> None:
        self.repo = repo
        self.temp_url = temp_url
        self.restore_url = restore_url

    def __enter__(self) -> None:
        for remote in self.repo.remotes:
            self.repo.delete_remote(remote)
        self.origin = self.repo.create_remote("origin", self.temp_url)
        return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.repo.delete_remote(self.origin)
        self.repo.create_remote("origin", self.restore_url)


def make_git_repo_and_push(github_token: str, github_url: str, repo_dir: Path) -> None:
    repo = git.Repo.init(repo_dir)
    # repo = git.Repo(repo_dir)      # This line is used when debugging
    repo.git.add("-A")
    repo.index.commit("Initial commit")
    repo.git.branch("-M", "main")

    github_username = Github(github_token).get_user().login
    credential_url = mangle_url(github_url, github_token)
    username_url = mangle_url(github_url, github_username)

    with TempGitRemote(repo, credential_url, username_url):
        repo.git.push("--set-upstream", "origin", "main")
    typer.echo(f"Repo successfully pushed to GitHub: {github_url}")


def set_branch_protection_rules(github_token: str, repo_name: str) -> None:
    repo = Github(github_token).get_repo(f"{org_name}/{repo_name}")
    repo.get_branch("main").edit_protection(
        required_approving_review_count=1, dismiss_stale_reviews=True
    )


def create_project_from_template(projectname: str, description: str):
    home_dir = Path.home()
    project_dir = home_dir.joinpath(projectname)
    if project_dir.exists():
        raise ValueError(f"The directory {project_dir} already exists.")
    argv = [
        "cruft",
        "create",
        "https://github.com/statisticsnorway/stat-hurtigstart-template-master",
    ]
    # try:
    subprocess.run(argv, check=True)
    # except subprocess.CalledProcessError:
    #     typer.echo(f"ERROR calling cruft.")
    return project_dir


@app.command()
def create(
    projectname: str = "",
    description: str = "",
    repo_privacy: Optional[str] = "internal",
    skip_github: Optional[bool] = typer.Option(None, "--skip-github/--noskip-github"),
    github_token: Optional[str] = "",
):
    """
    1. Start Cookiecutter which requests inputs from user
    2. Create Repo under Statistics Norway (ask for access token at this point)
    3. Set recommended settings on github repo
    4. Add metadata about creation to .ssb_project_root ?
    """

    # Type checking
    repo_privacy = repo_privacy.lower()
    accepted_repo_privacy = ["internal", "public", "private"]
    if repo_privacy not in accepted_repo_privacy:
        raise ValueError(
            f"Access {repo_privacy} not among accepted accesses: {*accepted_repo_privacy,}"
        )

    if " " in projectname:
        raise ValueError("Spaces not allowed in projectname, use underscore?")

    if not skip_github and not github_token:
        raise ValueError("Needs GitHub token, please specify with --github-token")

    if not debug_without_create_repo:
        if not skip_github and is_github_repo(github_token, projectname):
            raise ValueError(f"The repo {projectname} already exists on GitHub.")

    # 1. Start cookiecutter
    typer.echo(
        f"Start Cookiecutter for project:{projectname}, in folder {os.getcwd()} or in dapla root?"
    )

    create_project_from_template(projectname, description)

    # Create empty folder on root
    # Get content from template to local
    # git init ?
    # git add ?

    # 2. Create github repo
    if not skip_github:
        typer.echo("Create repo on github.com")
        repo_url = create_github(github_token, projectname, repo_privacy, description)

        typer.echo("Make local git repo and push to github.")
        # TODO Replace the line below with the path to the coockiecutter generated files
        git_repo_dir = Path("C:/Users/aei/tmp/stat-hurtigstart-template-master")
        make_git_repo_and_push(github_token, repo_url, git_repo_dir)

        typer.echo("Set branch protection rules.")
        set_branch_protection_rules(github_token, projectname)

    # 4. Add metadata about creation
    # typer.echo("Record / log metadata about project-creation to toml-file")
    # metadata_path = f"/home/jovyan/{projectname}/pyproject.toml"
    # metadata = toml.load(metadata_path)
    # metadata["ssb"]["project_creation"]["date"] = datetime.datetime.now().strftime(
    #     r"%Y-%m-%d"
    # )
    # metadata["ssb"]["project_creation"]["privacy"] = repo_privacy
    # metadata["ssb"]["project_creation"]["skipped_github"] = skip_github
    # if not skip_github:
    #     metadata["ssb"]["project_creation"]["github_uri"] = repo_url
    # metadata["ssb"]["project_creation"]["delete_run"] = False
    # with open(metadata_path, "w") as toml_file:
    #     toml.dump(metadata, toml_file)

    typer.echo(
        f"Projectfolder {projectname} created on dapla root, you may move it if you want to."
    )


@app.command()
def build(kernel: Optional[str] = "python3", curr_path: Optional[str] = ""):
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

    typer.echo("Recommend taking in changes from template? (date from pyproject.toml?)")

    typer.echo("Create Venv from Poetry")

    typer.echo("Create kernel from venv")
    project_name = projectname_from_currfolder(os.getcwd())

    # A new tool for creating venv-kernels from poetry-venvs will not be ready for hack-demo
    kernels = get_kernels_dict()
    # Flip kernel-text to key if full path to kernel given
    if kernel in kernels.values():
        kernel = {v: k for k, v in kernels.items()}[kernel]
    if kernel not in kernels.keys():
        raise ValueError(f"Cant find {kernel}-template among {kernels.keys()}")

    add_ipykernel = subprocess.run(
        "poetry add ipykernel".split(" "), capture_output=True
    )
    if add_ipykernel.returncode != 0:
        raise ValueError(
            f'Returncode of adding ipykernel: {add_ipykernel.returncode}\n{add_ipykernel.stderr.decode("utf-8")}'
        )

    make_kernel_cmd = "poetry run python3 -m ipykernel install --user --name".split(
        " "
    ) + [project_name]
    result = subprocess.run(make_kernel_cmd, capture_output=True)
    if result.returncode != 0:
        raise ValueError(
            f'Returncode of making kernel: {result.returncode}\n{result.stderr.decode("utf-8")}'
        )
    output = result.stdout.decode("utf-8")
    print(output)

    print("You should now have a kernel with poetry venv?")

    workspace_uri = workspace_uri_from_projectname(project_name)
    typer.echo(f"Suggested workspace (bookmark this): {workspace_uri}?clone")

    # typer.echo("Record / log metadata about project-build to toml-file")
    # metadata_path = f"/home/jovyan/{project_name}/pyproject.toml"
    # metadata = toml.load(metadata_path)
    # metadata["ssb"]["project_build"]["date"] = datetime.datetime.now().strftime(r"%Y-%m-%d")
    # metadata["ssb"]["project_build"]["kernel"] = kernel
    # metadata["ssb"]["project_build"]["kernel_cmd"] = kernel_cmd
    # metadata["ssb"]["project_build"]["workspace_uri_WITH_USERNAME"] = workspace_uri
    # with open(metadata_path, "w") as toml_file:
    #    toml.dump(metadata, toml_file)

    # Reset back to the starting directory
    if curr_path:
        os.chdir(pre_path)


@app.command()
def delete():
    """
    1. Remove kernel
    2. Remove venv / uninstall with poetry
    3. Remove workspace, if exists?
    """
    project_name = projectname_from_currfolder(os.getcwd())
    typer.echo("Remove kernel")
    kernels_path = "/home/jovyan/.local/share/jupyter/kernels/"
    for kernel in os.listdir(kernels_path):
        if kernel.startswith(project_name):
            os.remove(kernels_path + project_name)

    # Deactivation not necessary?
    # If you remove the currently activated virtual environment, it will be automatically deactivated.

    typer.echo("Remove venv / uninstall with poetry")

    venvs = subprocess.run(["poetry", "env", "list"], capture_output=True)
    if venvs.returncode != 0:
        raise ValueError(venvs.stderr.decode("utf-8"))
    venvs = venvs.stdout.decode("utf-8")

    delete_cmds = []
    for venv in venvs.split("\n"):
        if venv:
            print(venv)
            if (venv.replace("-", "").replace("_", "")).startswith(
                project_name.replace("-", "").replace("_", "")
            ):
                delete_cmds += [["poetry", "env", "remove", venv.split(" ")[0]]]

    for cmd in delete_cmds:
        deletion = subprocess.run(cmd, capture_output=True)
        if deletion.returncode != 0:
            raise ValueError(deletion.stderr.decode("utf-8"))
        print(deletion.stdout.decode("utf-8"))

    typer.echo("Remove workspace, if it exist, based on project-name")
    for workspace in os.listdir("/home/jovyan/.jupyter/lab/workspaces/"):
        if workspace.replace(["-", "_"], "").startswith(
            project_name.replace(["-", "_"], "")
        ):
            os.remove(f"/home/jovyan/.jupyter/lab/workspaces/{workspace}")

    # typer.echo("Record / log metadata about deletion to toml-file")
    # metadata_path = f"/home/jovyan/{project_name}/pyproject.toml"
    # metadata = toml.load(metadata_path)
    # metadata["ssb"]["project_delete"]["date"] = datetime.datetime.now().strftime(r"%Y-%m-%d")
    # metadata["ssb"]["project_delete"]["venvs"] = venvs
    # metadata["ssb"]["project_delete"]["delete_cmds"] = delete_cmds
    # metadata["ssb"]["project_delete"]["workspace_uri_WITH_USERNAME"] = workspace_uri
    # with open(metadata_path, "w") as toml_file:
    #    toml.dump(metadata, toml_file)


@app.command()
def workspace():
    typer.echo(workspace_uri_from_projectname(projectname_from_currfolder(os.getcwd())))
    typer.echo("To create/clone the workspace:")
    typer.echo(
        workspace_uri_from_projectname(projectname_from_currfolder(os.getcwd()))
        + "?clone"
    )


@app.command()
def create_github(
    github_token: str, repo_name: str, repo_privacy: str, repo_description: str
) -> str:
    # Kjør gitconfig-scripet om brukernavn og passord ikke er satt
    # Flere brukernavn knyttet til samme konto? Sjekke etter "primary email" knyttet til github-konto?

    private_repo = True if repo_privacy != "public" else False

    g = Github(github_token)
    if not debug_without_create_repo:
        g.get_organization(org_name).create_repo(
            repo_name,
            private=private_repo,
            auto_init=False,
            description=repo_description,
        )
    repo_url = g.get_repo(f"{org_name}/{repo_name}").clone_url
    typer.echo(f"GitHub repo created: {repo_url}")
    return repo_url


def projectname_from_currfolder(curr_path: Optional[str]) -> str:
    # Record for reset later
    curr_dir = os.getcwd()
    # Find root of project, and get projectname from poetry's toml-config
    while "pyproject.toml" not in os.listdir():
        os.chdir("../")
    pyproject = toml.load("./pyproject.toml")
    name = pyproject["tool"]["poetry"]["name"]
    # Reset working directory
    os.chdir(curr_dir)
    return name


def workspace_uri_from_projectname(project_name: str) -> str:
    return f"https://jupyter.dapla.ssb.no/user/{os.environ['JUPYTERHUB_USER']}/lab/workspaces/{project_name}"


def get_kernels_dict() -> dict():
    kernels = subprocess.run(["jupyter", "kernelspec", "list"], capture_output=True)
    if kernels.returncode == 0:
        kernels = kernels.stdout.decode("utf-8")
    else:
        raise ValueError(kernels.stderr.decode("utf-8"))
    kernel_dict = {}
    for kernel in kernels.split("\n")[1:]:
        line = " ".join(kernel.strip().split())
        if len(line.split(" ")) == 2:
            k, v = line.split(" ")
            kernel_dict[k] = v
    return kernel_dict


if __name__ == "__main__":
    app()
