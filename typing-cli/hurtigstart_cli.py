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
    
    # Type checking
    repo_privacy = repo_privacy.lower()
    accepted_repo_privacy = ["internal", "public", "private"]
    if repo_privacy not in accepted_repo_privacy:
        raise ValueError(f"Access {repo_privacy} not among accepted accesses: {*accepted_repo_privacy,}")
        
    if " " in projectname:
        raise ValueError("Spaces not allowed in projectname, use underscore?")
    
    # 1. Start cookiecutter
    typer.echo(f"Start Cookiecutter for project:{projectname}, in folder {os.getcwd()} or in dapla root?")

    # 2. Create github repo
    if not skip_github:
        typer.echo("Create repo on github.com")

        typer.echo("Set settings on github repo")

    # 4. Add metadata about creation
    typer.echo("Record / log metadata about project-creation to toml-file")
    metadata_path = f"/home/jovyan/{projectname}/pyproject.toml"
    metadata = toml.load(metadata_path )
    metadata["ssb"]["project_creation"]["date"] = datetime.datetime.now().strftime(r"%Y-%m-%d")
    metadata["ssb"]["project_creation"]["privacy"] = repo_privacy
    metadata["ssb"]["project_creation"]["skipped_github"] = skip_github
    metadata["ssb"]["project_creation"]["delete_run"] = False
    with open(metadata_path, "w") as toml_file:
        toml.dump(metadata, toml_file)


@app.command()
def build(  kernel: Optional[str] = "python3",
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

    add_ipykernel = subprocess.run("poetry add ipykernel".split(" "), capture_output = True)
    if add_ipykernel.returncode != 0:
        raise ValueError(f'Returncode of making kernel: {add_ipykernel.returncode}\n{add_ipykernel.stderr.decode("utf-8")}')
    
    make_kernel_cmd = "poetry run python3 -m ipykernel install --user --name".split(" ") + [project_name]
    result = subprocess.run(make_kernel_cmd, capture_output = True)
    if result.returncode != 0:
        raise ValueError(f'Returncode of making kernel: {result.returncode}\n{result.stderr.decode("utf-8")}')
    output = result.stdout.decode("utf-8")
    print(output)
    
    print("You should now have a kernel with poetry venv?")

    workspace_uri = workspace_uri_from_projectname(project_name)
    typer.echo(f"Suggested workspace (bookmark this): {workspace_uri}?clone")
    
    typer.echo("Record / log metadata about project-build to toml-file")
    metadata_path = f"/home/jovyan/{project_name}/pyproject.toml"
    metadata = toml.load(metadata_path)
    metadata["ssb"]["project_build"]["date"] = datetime.datetime.now().strftime(r"%Y-%m-%d")
    metadata["ssb"]["project_build"]["kernel"] = kernel
    metadata["ssb"]["project_build"]["kernel_cmd"] = kernel_cmd
    metadata["ssb"]["project_build"]["workspace_uri_WITH_USERNAME"] = workspace_uri
    with open(metadata_path, "w") as toml_file:
        toml.dump(metadata, toml_file)
    
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
    
    venvs = subprocess.run(["poetry", "env", "list"], capture_output= True)
    if venvs.returncode != 0:
        raise ValueError(venvs.stderr.decode("utf-8"))
    venvs = venvs.stdout.decode("utf-8")
    
    delete_cmds = []
    for venv in venvs.split("\n"):
        if venv:
            print(venv)
            if ((venv.replace("-", "").replace("_",""))
                .startswith(
                    project_name.replace("-", "").replace("_",""))):
                delete_cmds += [['poetry', 'env', 'remove', venv.split(" ")[0]]]
            
    for cmd in delete_cmds:
        deletion = subprocess.run(cmd, capture_output= True)
        if deletion.returncode != 0:
            raise ValueError(deletion.stderr.decode("utf-8"))
        print(deletion.stdout.decode("utf-8"))

    typer.echo("Remove workspace, if it exist, based on project-name")
    for workspace in os.listdir("/home/jovyan/.jupyter/lab/workspaces/"):
        if workspace.replace(["-","_"], "").startswith(project_name.replace(["-","_"], "")):
            os.remove(f"/home/jovyan/.jupyter/lab/workspaces/{workspace}")
    
    
    typer.echo("Record / log metadata about deletion to toml-file")
    metadata_path = f"/home/jovyan/{project_name}/pyproject.toml"
    metadata = toml.load(metadata_path)
    metadata["ssb"]["project_delete"]["date"] = datetime.datetime.now().strftime(r"%Y-%m-%d")
    metadata["ssb"]["project_delete"]["venvs"] = venvs
    metadata["ssb"]["project_delete"]["delete_cmds"] = delete_cmds
    metadata["ssb"]["project_delete"]["workspace_uri_WITH_USERNAME"] = workspace_uri
    with open(metadata_path, "w") as toml_file:
        toml.dump(metadata, toml_file)
    
@app.command()
def workspace():
    typer.echo(workspace_uri_from_projectname(projectname_from_currfolder(os.getcwd())))
    typer.echo("To create/clone the workspace:")
    typer.echo(workspace_uri_from_projectname(projectname_from_currfolder(os.getcwd())) + "?clone" )

def projectname_from_currfolder(curr_path: Optional[str]) -> str:
    # Record for reset later
    curr_dir = os.getcwd()
    # Find root of project, and get projectname from poetry's toml-config
    while "pyproject.toml" not in os.listdir():
        os.chdir("../")
    pyproject = toml.load("./pyproject.toml")
    name = pyproject['tool']['poetry']['name']
    # Reset working directory
    os.chdir(curr_dir)
    return name

def workspace_uri_from_projectname(project_name: str) -> str:
    return f"https://jupyter.dapla.ssb.no/user/{os.environ['JUPYTERHUB_USER']}/lab/workspaces/{project_name}"

def get_kernels_dict() -> dict():
    kernels = subprocess.run(["jupyter", "kernelspec", "list"], capture_output= True)
    if kernels.returncode == 0:
        kernels = kernels.stdout.decode("utf-8")
    else:
        raise ValueError(kernels.stderr.decode("utf-8"))
    kernel_dict = {}
    for kernel in kernels.split("\n")[1:]:
        line = ' '.join(kernel.strip().split())
        if len(line.split(" ")) == 2:
            k, v = line.split(" ")
            kernel_dict[k] = v
    return kernel_dict


if __name__ == "__main__":
    app()