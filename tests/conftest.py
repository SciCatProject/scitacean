# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)

import hypothesis
import pytest

from scitacean.testing.backend import add_pytest_option as add_backend_option
from scitacean.testing.sftp import add_pytest_option as add_sftp_option

pytest_plugins = (
    "scitacean.testing.backend.fixtures",
    "scitacean.testing.sftp.fixtures",
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


def pytest_addoption(parser: pytest.Parser) -> None:
    add_backend_option(parser)
    add_sftp_option(parser)
