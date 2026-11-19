# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Base Pytest plugin for Scitacean.

This plugin should not be used directly.
Instead, use one or both of

- ``scitacean.testing.backend.pytest_plugin``
- ``scitacean.testing.sftp.pytest_plugin``

Both include this plugin.
"""

import uuid
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from ._testing_project import TestingProject

# Share the project path across all xdist workers.
_PROJECT_LOCATION = pytest.StashKey[tuple[Path, str]]()
_WORKER_LOCATION = "scitacean_project_location"


@pytest.fixture(scope="session")
def scitacean_testing_project(
    request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory
) -> TestingProject:
    config = request.config
    if hasattr(config, "workerinput"):  # xdist worker
        base_str, name = config.workerinput[_WORKER_LOCATION]
        base = Path(base_str)
    else:  # serial run
        base = tmp_path_factory.getbasetemp()
        name = f"scitacean-test-{uuid.uuid4().hex}"
        config.stash[_PROJECT_LOCATION] = (base, name)

    return TestingProject.get_or_create(
        base=base,
        project_name=name,
        scicat_version=request.config.getoption("--scitacean-backend-version"),
    )


@pytest.hookimpl(optionalhook=True)
def pytest_configure_node(node: Any) -> None:
    """Pass the same project location to every local xdist worker."""
    location = node.config.stash.get(_PROJECT_LOCATION, None)
    if location is None:
        base = node.config._tmp_path_factory.getbasetemp()
        location = (base, f"scitacean-test-{uuid.uuid4().hex}")
        node.config.stash[_PROJECT_LOCATION] = location

    base, name = location
    node.workerinput[_WORKER_LOCATION] = (str(base), name)


@pytest.hookimpl(hookwrapper=True)
def pytest_sessionfinish(
    session: pytest.Session, exitstatus: int
) -> Generator[None, None, None]:
    yield  # Let xdist's session-finish hooks complete first.

    config = session.config
    if hasattr(config, "workerinput"):  # xdist worker
        return

    location = config.stash.get(_PROJECT_LOCATION, None)
    if location is not None:
        base, name = location
        project = TestingProject.load_existing(base, project_name=name)
        if project is not None:
            project.teardown()
