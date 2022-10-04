"""Sphinx configuration."""
project = "SSB Project CLI"
author = "Damir Medakovic"
copyright = "2022, Damir Medakovic"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_click",
    "myst_parser",
]
autodoc_typehints = "description"
html_theme = "furo"
