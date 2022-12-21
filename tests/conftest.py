# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen
# flake8: noqa

import tempfile
from dataclasses import dataclass
from typing import Dict

import hypothesis
import pytest

from .common import backend
from .common.docker import docker_compose

# The datasets strategy requires a large amount of memory and time.
# This is not good but hard to avoid.
# So simply disable health checks and accept that tests are slow.
hypothesis.settings.register_profile(
    "scitacean",
    suppress_health_check=[
        hypothesis.HealthCheck.data_too_large,
        hypothesis.HealthCheck.too_slow,
    ],
)


def pytest_addoption(parser):
    parser.addoption(
        "--backend-tests",
        action="store_true",
        default=False,
        help="Select whether to run tests against a real SciCat backend",
    )


@pytest.fixture(scope="session")
def scicat_backend(request, scicat_access):
    """Spin up a SciCat backend and API.

    Does nothing unless the --backend-tests command line option is set.
    """

    if request.config.getoption("--backend-tests"):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = backend.configure(temp_dir)
            with docker_compose(config_file, *backend.SERVICES):
                backend.wait_until_backend_is_live(
                    scicat_access, max_time=20, n_tries=20
                )
                yield True
    else:
        yield False


@dataclass
class SciCatAccess:
    url: str
    functional_credentials: Dict[str, str]


@pytest.fixture(scope="session")
def scicat_access():
    return SciCatAccess(
        url="http://localhost/api/v3/",
        functional_credentials={"username": "ingestor", "password": "aman"},
    )
