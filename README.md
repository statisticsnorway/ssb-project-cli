# Hack2022 Dapla Hurtigstart

[![PyPI](https://img.shields.io/pypi/v/hack2022-dapla-hurtigstart.svg)][pypi_]
[![Status](https://img.shields.io/pypi/status/hack2022-dapla-hurtigstart.svg)][status]
[![Python Version](https://img.shields.io/pypi/pyversions/hack2022-dapla-hurtigstart)][python version]
[![License](https://img.shields.io/pypi/l/hack2022-dapla-hurtigstart)][license]

[![Read the documentation at https://hack2022-dapla-hurtigstart.readthedocs.io/](https://img.shields.io/readthedocs/hack2022-dapla-hurtigstart/latest.svg?label=Read%20the%20Docs)][read the docs]
[![Tests](https://github.com/statisticsnorway/hack2022-dapla-hurtigstart/workflows/Tests/badge.svg)][tests]
[![Codecov](https://codecov.io/gh/statisticsnorway/hack2022-dapla-hurtigstart/branch/main/graph/badge.svg)][codecov]

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)][pre-commit]
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)][black]

[pypi_]: https://pypi.org/project/hack2022-dapla-hurtigstart/
[status]: https://pypi.org/project/hack2022-dapla-hurtigstart/
[python version]: https://pypi.org/project/hack2022-dapla-hurtigstart
[read the docs]: https://hack2022-dapla-hurtigstart.readthedocs.io/
[tests]: https://github.com/statisticsnorway/hack2022-dapla-hurtigstart/actions?workflow=Tests
[codecov]: https://app.codecov.io/gh/statisticsnorway/hack2022-dapla-hurtigstart
[pre-commit]: https://github.com/pre-commit/pre-commit
[black]: https://github.com/psf/black

## Features

![Help text](docs/assets/cli_help_screenshot.png)

- Create a new project quickly and easily with `ssb-project create`.
- Your colleagues can quickly get started when you share the project with them with `ssb-project build`.
- Includes:
  - Local directory structure
  - Virtual Environment
  - Kernel for use on Jupyter
  - Github repo (if desired)
- The project will follow the most recent SSB guidelines for security and quality.
- It will always be possible to update existing projects as guidelines change.

## Installation

-TODO</br>
You can install _Hack2022 Dapla Hurtigstart_ via [pip] from [PyPI]:

```console
pip install hack2022-dapla-hurtigstart
```

## Contributing

### Setup

1. [Install dependencies](https://cookiecutter-hypermodern-python.readthedocs.io/en/latest/guide.html#installation)
1. [Install pre-commit hooks](https://cookiecutter-hypermodern-python.readthedocs.io/en/latest/guide.html#running-pre-commit-from-git)
1. Run tests: `nox -r` ([More information here](https://cookiecutter-hypermodern-python.readthedocs.io/en/latest/guide.html#using-nox))
1. Run the help command: `poetry run ssb-project --help`

## License

Distributed under the terms of the [MIT license][license],
_Hack2022 Dapla Hurtigstart_ is free and open source software.

<!-- github-only -->

[license]: https://github.com/statisticsnorway/hack2022-dapla-hurtigstart/blob/main/LICENSE
