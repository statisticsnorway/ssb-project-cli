"""Sphinx configuration."""
project = "Hack2022 Dapla Hurtigstart"
author = "Arne Sørli"
copyright = "2022, Arne Sørli"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_click",
    "myst_parser",
]
autodoc_typehints = "description"
html_theme = "furo"
