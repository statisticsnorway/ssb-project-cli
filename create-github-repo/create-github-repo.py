import argparse
import logging
import sys

from github import Github, GithubException

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler("create-github-repos.log", mode="w", encoding="utf-8"),
        logging.StreamHandler(),
    ],
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def main(token: str, repo_name: str):
    logging.info("Scanning organization for active public repos...")
    org_name = "statisticsnorway"
    g = Github(token)

    org = g.get_organization(org_name)

    try:
        org.create_repo(
            repo_name,
            private=True,
            auto_init=True,
            gitignore_template="Python",
            license_template="mit",
            description="Test-repo for dapla-hurtigstart at #Hack4ssb 2022",
        )
    except GithubException:
        logging.warning(f"Repo {repo_name} already exists.")
    else:
        logging.info(f"Repo {repo_name} created.")

    repo = g.get_repo(f"{org_name}/{repo_name}")
    logging.info(f"{repo.full_name=}")
    logging.info(f"{repo.private=}")

    # main_branch = repo.get_branch("main")
    # main_branch.edit_protection()
    # protection = main_branch.get_protection()
    # logging.info(f"{protection}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=sys.modules[__name__].__doc__)
    parser.add_argument("token", help="GitHub Personal Access Token")
    parser.add_argument("repo_name", help="Name of the GitHub repo to be created")
    args = parser.parse_args()

    main(args.token, args.repo_name)
