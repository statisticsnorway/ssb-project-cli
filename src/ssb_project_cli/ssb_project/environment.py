"""Read in environment variables."""
import os


JUPYTER_IMAGE_SPEC = os.environ.get("JUPYTER_IMAGE_SPEC", "")
PIP_INDEX_URL = os.environ.get("PIP_INDEX_URL", "")
