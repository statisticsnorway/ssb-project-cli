"""This module reads in environment variables."""
import os


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
