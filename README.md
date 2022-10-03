# SSB Project CLI

[![PyPI](https://img.shields.io/pypi/v/ssb-project-cli.svg)][pypi status]
[![Status](https://img.shields.io/pypi/status/ssb-project-cli.svg)][pypi status]
[![Python Version](https://img.shields.io/pypi/pyversions/ssb-project-cli)][pypi status]
[![License](https://img.shields.io/pypi/l/ssb-project-cli)][license]

[![Read the documentation at https://ssb-project-cli.readthedocs.io/](https://img.shields.io/readthedocs/ssb-project-cli/latest.svg?label=Read%20the%20Docs)][read the docs]
[![Tests](https://github.com/statisticsnorway/ssb-project-cli/workflows/Tests/badge.svg)][tests]
[![Codecov](https://codecov.io/gh/statisticsnorway/ssb-project-cli/branch/main/graph/badge.svg)][codecov]

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)][pre-commit]
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)][black]

[pypi status]: https://pypi.org/project/ssb-project-cli/
[read the docs]: https://ssb-project-cli.readthedocs.io/
[tests]: https://github.com/statisticsnorway/ssb-project-cli/actions?workflow=Tests
[codecov]: https://app.codecov.io/gh/statisticsnorway/ssb-project-cli
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

You can install _SSB Project CLI_ via [pip] from [PyPI]:

```console
pip install ssb-project-cli
```

## Contributing

### Setup

1. [Install dependencies](https://cookiecutter-hypermodern-python.readthedocs.io/en/latest/guide.html#installation)
1. [Install pre-commit hooks](https://cookiecutter-hypermodern-python.readthedocs.io/en/latest/guide.html#running-pre-commit-from-git)
1. Run tests: `nox -r` ([More information here](https://cookiecutter-hypermodern-python.readthedocs.io/en/latest/guide.html#using-nox))
1. Run the help command: `poetry run ssb-project --help`

## License

Distributed under the terms of the [MIT license][license],
_SSB Project CLI_ is free and open source software.

<!-- github-only -->

[license]: https://github.com/statisticsnorway/ssb-project-cli/blob/main/LICENSE
