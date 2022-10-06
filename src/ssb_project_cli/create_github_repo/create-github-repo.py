"""Functions for creating a GitHub repository."""
import argparse
import logging
import sys

# Module "git" does not explicitly export attribute "Repo"
from git import Repo  # type: ignore[attr-defined]
from github import Github
from github import GithubException


logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler("create-github-repos.log", mode="w", encoding="utf-8"),
        logging.StreamHandler(),
    ],
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def set_branch_protection_rules(repo: Repo) -> None:
    """Sets branch default protection rules.

    The following rules are set:
    Main branch pull requests requires a minimum of 1 reviewer.
    Reviews that are no longer valid can be dismissed.
    When you dismiss a review, you must add a comment explaining why you dismissed it.

    Args:
        repo: GitHub repository
    """
    main_branch = repo.get_branch("main")
    main_branch.edit_protection(
        required_approving_review_count=1, dismiss_stale_reviews=True
    )
    logging.info(f"main_branch.protected={repo.get_branch('main').protected}")
    protection = main_branch.get_protection()
    logging.info(
        f"{protection.required_pull_request_reviews.required_approving_review_count=}"
    )
    logging.info(f"{protection.required_pull_request_reviews.dismiss_stale_reviews=}")


def get_user_info(g: Github) -> None:
    """Logs user info.

    Logs username, name and email of a GitHub user.

    Args:
        g: GitHub
    """
    user = g.get_user()
    logging.info(f"{user.login=}")
    logging.info(f"{user.name=}")
    logging.info(f"{user.email=}")


def get_org_members(g: Github) -> None:
    """Prints GitHub organization members info.

    Prints username, name and email of members in
     Statistics Norway`s GitHub organization.

    Args:
        g: GitHub
    """
    org = g.get_organization("statisticsnorway")
    for i, member in enumerate(org.get_members()):
        print(f"{i}: {member.login} {member.name} email: {member.email}")


def main(token: str, repo_name: str) -> None:
    """Creates a new repository with a given name.

    Args:
        repo_name: Name of GitHub repository to create
        token: GitHub Personal access token
    """
    org_name = "statisticsnorway"
    logging.info(f"Creating GitHub repo {org_name}/{repo_name} and set defaults.")

    g = Github(token)
    get_user_info(g)

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
    logging.info(f"{repo.clone_url=}")

    set_branch_protection_rules(repo)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=sys.modules[__name__].__doc__)
    parser.add_argument("token", help="GitHub Personal Access Token")
    parser.add_argument("repo_name", help="Name of the GitHub repo to be created")
    args = parser.parse_args()

    main(args.token, args.repo_name)
