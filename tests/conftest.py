# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 SciCat Project (https://github.com/SciCatProject/scitacean)

import hypothesis
import pytest

from scitacean import Profile
from scitacean.testing.transfer import FakeFileTransfer

pytest_plugins = (
    "scitacean.testing.backend.pytest_plugin",
    "scitacean.testing.sftp.pytest_plugin",
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


@pytest.fixture
def test_profile() -> Profile:
    return Profile(
        url="https://fake.scicat/api/v4",
        file_transfer=FakeFileTransfer(),
        frontend_url="https://fake.scicat",
    )
