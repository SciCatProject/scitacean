# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Pytest plugin for SciCat backend tests with Scitacean."""

from pathlib import Path

import pytest

from ...client import Client
from .._logging import get_logger
from .._testing_project import TestingProject
from ..client import FakeClient
from . import seed
from .config import SciCatAccess, local_access

pytest_plugins = ("scitacean.testing._pytest_plugin",)


COMMAND_LINE_OPTION = "--backend-tests"


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add command-line options to pytest to control backend tests."""
    parser.addoption(
        COMMAND_LINE_OPTION,
        action="store_true",
        default=False,
        help="Select whether to run tests against a real SciCat backend",
    )
    parser.addoption(
        "--scitacean-backend-version",
        default=None,
        help="Specify a version for the SciCat backend",
    )


@pytest.fixture(scope="session")
def scicat_access() -> SciCatAccess:
    """Fixture that returns SciCat access parameters.

    Returns
    -------
    :
        A URL and user to connect to the testing backend.
        The user has access to all initial datasets in the database and permissions
        to create new datasets.
    """
    return local_access("user1")


@pytest.fixture
def fake_client(scicat_access: SciCatAccess) -> FakeClient:
    """Fixture that returns a fake client.

    The client is seeded from the same data as the backend.
    But only if the backend has been requested.
    So any test that uses ``fake_client`` explicitly and requires the seed,
    must also request the ``require_scicat_backend`` fixture.

    Returns
    -------
    :
        A fake client that potentially contains the seed data.
        See :mod:`scitacean.testing.backend.seed`.
    """
    client = scicat_access.make_client(FakeClient)
    client.datasets.update(
        {ds.pid: ds for ds in seed.INITIAL_DATASETS.values()}  # type: ignore[misc]
    )
    client.orig_datablocks.update(
        {
            dbs[0].datasetId: dbs  # type: ignore[misc]
            for dbs in seed.INITIAL_ORIG_DATABLOCKS.values()
        }
    )
    client.attachments.update(
        {a[0].relationships[0].targetId: a for a in seed.INITIAL_ATTACHMENTS.values()}  # type: ignore[index]
    )
    return client


@pytest.fixture
def real_client(scicat_access: SciCatAccess, scicat_backend: bool) -> Client | None:
    """Fixture that returns a real client if backend tests are enabled.

    Returns
    -------
    :
        If backend tests are enabled, a real client that is connected to
        the testing backend.
        Otherwise, it returns None.
    """
    if not scicat_backend:
        return None
    return scicat_access.make_client(Client)


@pytest.fixture(params=["real", "fake"])
def client(request: pytest.FixtureRequest, scicat_backend: bool) -> Client | FakeClient:
    """Fixture that returns a real and a fake client.

    Using this fixture makes tests run twice, once with a real client
    and once with a fake client.
    If backend tests are disabled, the test with a real client gets skipped.

    Returns
    -------
    :
        A real client and a fake client.
    """
    if request.param == "fake":
        return request.getfixturevalue("fake_client")  # type: ignore[no-any-return]
    _skip_if_not_backend(request)
    return request.getfixturevalue("real_client")  # type: ignore[no-any-return]


@pytest.fixture(scope="session")
def scicat_backend(
    request: pytest.FixtureRequest,
    scitacean_testing_project: TestingProject,
    scicat_access: SciCatAccess,
) -> bool:
    """Fixture to declare that a test needs a local scicat backend.

    If backend tests are enabled, this fixture spins up the backend in a docker
    container the first time a test requests it.
    The backend will be stopped and removed at the end of the test session.
    :mod:`scitacean.testing.backend.seed` is used to initialize the database.

    If backend tests are disabled, this fixture prepares the seed for use with
    :func:`scitacean.testing.backend.pytest_plugin.fake_client`.

    Returns
    -------
    :
        True if backend tests are enabled and False otherwise.
    """
    backend_enabled = _backend_enabled(request)
    if backend_enabled:
        get_logger().info("Preparing SciCat with real backend")
        client_class: type[Client | FakeClient] = Client
        scitacean_testing_project.ensure_running("scicat")
    else:
        get_logger().info("Preparing SciCat without real backend")
        client_class = FakeClient

    with scitacean_testing_project.lock():
        if seed.is_seeded(scitacean_testing_project.path):
            seed.seed_worker(scitacean_testing_project.path)
        else:
            _seed_database(
                client_class,
                scicat_access=scicat_access,
                target_dir=scitacean_testing_project.path,
            )

    return backend_enabled


@pytest.fixture
def require_scicat_backend(
    request: pytest.FixtureRequest, scicat_backend: bool
) -> None:
    """Fixture to declare that a test needs a local scicat backend.

    Like :func:`scitacean.testing.backend.pytest_plugin.scicat_backend`
    but this skips the test if backend tests are disabled.
    """
    _skip_if_not_backend(request)


def _seed_database(
    client_class: type[Client] | type[FakeClient],
    scicat_access: SciCatAccess,
    target_dir: Path,
) -> None:
    client = scicat_access.make_client(client_class)
    seed.seed_database(client=client, scicat_access=scicat_access)
    seed.save_seed(target_dir)


def _skip_if_not_backend(request: pytest.FixtureRequest) -> None:
    """Mark the current test to be skipped if backend tests are disabled."""
    if not _backend_enabled(request):
        pytest.skip(
            "Tests against a real backend are disabled, "
            f"use {COMMAND_LINE_OPTION} to enable them"
        )


def _backend_enabled(request: pytest.FixtureRequest) -> bool:
    """Return True if backend tests are enabled."""
    return bool(request.config.getoption(COMMAND_LINE_OPTION))
