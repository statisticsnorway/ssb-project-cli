"""Sphinx configuration."""
project = "Dapla Team CLI"
author = "Kenneth Leine Schulstad"
copyright = "2022, Kenneth Leine Schulstad"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_click",
    "myst_parser",
]
autodoc_typehints = "description"
html_theme = "furo"
