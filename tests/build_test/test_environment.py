"""Tests for the environment module."""
import pytest

from ssb_project_cli.ssb_project.build.environment import running_onprem


ENVIRONMENT = "ssb_project_cli.ssb_project.build.environment"


@pytest.mark.parametrize(
    "image_spec,expected_result",
    [
        ("prod-bip/ssb/statistikktjenester/jupyterlab-onprem:0.1.3", True),
        ("rod-bip/ssb/dapla/dapla-jupyterlab:1.3.7", False),
    ],
)
def test_running_onprem(image_spec: str, expected_result: bool) -> None:
    assert running_onprem(image_spec) == expected_result
