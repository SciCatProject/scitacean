# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)

import hypothesis
import pytest

from .common.backend import scicat_access, scicat_backend  # noqa: F401
from .common.ssh_server import ssh_access, ssh_fileserver  # noqa: F401

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


def pytest_addoption(parser: pytest.Parser):
    parser.addoption(
        "--backend-tests",
        action="store_true",
        default=False,
        help="Select whether to run tests against a real SciCat backend",
    )
    parser.addoption(
        "--ssh-tests",
        action="store_true",
        default=False,
        help="Select whether to run tests with an SSH fileserver",
    )
