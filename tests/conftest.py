# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)

import hypothesis
import pytest

from scitacean.testing.backend import add_pytest_option as add_backend_option
from scitacean.testing.backend.fixtures import *  # noqa: F403

from .common.ssh_server import (  # noqa: F401
    ssh_access,
    ssh_config_dir,
    ssh_connect_with_username_password,
    ssh_connection_config,
    ssh_data_dir,
    ssh_fileserver,
)

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
    add_backend_option(parser)
    parser.addoption(
        "--ssh-tests",
        action="store_true",
        default=False,
        help="Select whether to run tests with an SSH fileserver",
    )
