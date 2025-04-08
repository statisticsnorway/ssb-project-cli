"""This module reads in environment variables."""

import os
from kvakk_git_tools import ssb_gitconfig  # type: ignore
from rich import print

JUPYTER_IMAGE_SPEC = os.environ.get("JUPYTER_IMAGE_SPEC", "")
PIP_INDEX_URL = os.environ.get("PIP_INDEX_URL", "")
NEXUS_SOURCE_NAME = "nexus"


def running_onprem(image_spec: str) -> bool:
    """Are we running in Jupyter on-prem?

    Args:
        image_spec: Value of the JUPYTER_IMAGE_SPEC environment variable

    Returns:
        True if running on-prem, else False.
    """
    return "onprem" in image_spec


def reset_global_gitconfig() -> None:
    """Reset the global gitconfig using 'kvakk-git-tools' module.

    This function attempts to configure the global gitconfig using the 'kvakk-git-tools' module.
    If the configuration fails, an error message is printed indicating the platform's support status.
    """
    print("\nConfiguring git with 'kvakk-git-tools':")

    try:
        ssb_gitconfig.main(test=False)
    except SystemExit:
        platform = ssb_gitconfig.Platform()
        is_supported_bools = ("is", "is not")
        print(
            f"\n:x:\tYour global gitconfig was not fixed, your platform {is_supported_bools[platform.is_unsupported()]} supported."
        )
