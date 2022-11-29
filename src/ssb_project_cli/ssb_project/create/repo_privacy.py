"""This module contains the RepoPrivacy class."""
from enum import Enum


class RepoPrivacy(str, Enum):
    """Class with predefined privacy enums."""

    internal = "internal"
    private = "private"
    public = "public"
