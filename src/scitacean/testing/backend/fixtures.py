# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)
# mypy: disable-error-code="no-untyped-def"
"""Pytest fixtures to manage and access a local SciCat backend."""

import logging
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

import pytest

from ..._internal import docker
from ..._internal.file_counter import FileCounter, NullCounter
from ...client import Client
from .._pytest_helpers import init_pytest_work_dir
from ..client import FakeClient
from . import seed
from ._backend import configure, wait_until_backend_is_live
from ._pytest_helpers import backend_enabled, skip_if_not_backend
from .config import SciCatAccess, local_access


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
    client = FakeClient.from_credentials(
        url=scicat_access.url,
        **scicat_access.user.credentials,
    )
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
        {
            a[0].datasetId: a  # type: ignore[misc]
            for a in seed.INITIAL_ATTACHMENTS.values()
        }
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
    return Client.from_credentials(
        url=scicat_access.url,
        **scicat_access.user.credentials,
    )


@pytest.fixture(params=["real", "fake"])
def client(request, scicat_backend) -> Client | FakeClient:
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
    skip_if_not_backend(request)
    return request.getfixturevalue("real_client")  # type: ignore[no-any-return]


@pytest.fixture
def require_scicat_backend(request, scicat_backend) -> None:  # noqa: PT004
    """Fixture to declare that a test needs a local scicat backend.

    Like :func:`scitacean.testing.backend.scicat_backend`
    but this skips the test if backend tests are disabled.
    """
    skip_if_not_backend(request)


@pytest.fixture(scope="session")
def scicat_backend(request, tmp_path_factory, scicat_access):
    """Fixture to declare that a test needs a local scicat backend.

    If backend tests are enabled, this fixture spins up the backend in a docker
    container the first time a test requests it.
    The backend will be stopped and removed at the end of the test session.
    :mod:`scitacean.testing.backend.seed` is used to initialize the database.

    If backend tests are disabled, this fixture prepares the seed for use with
    :func:`scitacean.testing.backend.fixtures.fake_client`.

    Returns
    -------
    :
        True if backend tests are enabled and False otherwise.
    """
    target_dir, counter = init_pytest_work_dir(
        request, tmp_path_factory, name="scitacean-scicat-backend"
    )

    if not backend_enabled(request):
        with _prepare_without_backend(
            scicat_access=scicat_access, counter=counter, target_dir=target_dir
        ):
            yield False
    else:
        with _prepare_with_backend(
            scicat_access=scicat_access, target_dir=target_dir, counter=counter
        ):
            yield True


@contextmanager
def _prepare_without_backend(
    scicat_access: SciCatAccess,
    counter: FileCounter | NullCounter,
    target_dir: Path,
) -> Generator[None, None, None]:
    with counter.increment() as count:
        if count == 1:
            _seed_database(
                FakeClient, scicat_access=scicat_access, target_dir=target_dir
            )
        else:
            seed.seed_worker(target_dir)
    yield


@contextmanager
def _prepare_with_backend(
    scicat_access: SciCatAccess,
    counter: FileCounter | NullCounter,
    target_dir: Path,
) -> Generator[None, None, None]:
    try:
        with counter.increment() as count:
            if count == 1:
                _backend_docker_up(target_dir)
                _seed_database(
                    Client, scicat_access=scicat_access, target_dir=target_dir
                )
            elif not _backend_is_running():
                raise RuntimeError("Expected backend to be running")
            else:
                seed.seed_worker(target_dir)
        yield
    finally:
        with counter.decrement() as count:
            if count == 0:
                _backend_docker_down(target_dir)


def _seed_database(
    client_class: type[Client] | type[FakeClient],
    scicat_access: SciCatAccess,
    target_dir: Path,
) -> None:
    client = client_class.from_credentials(
        url=scicat_access.url,
        **scicat_access.user.credentials,
    )
    seed.seed_database(client=client, scicat_access=scicat_access)
    seed.save_seed(target_dir)


def _backend_docker_up(target_dir: Path) -> None:
    if _backend_is_running():
        raise RuntimeError("SciCat docker container is already running")
    docker_compose_file = target_dir / "docker-compose.yaml"
    log = logging.getLogger("scitacean.testing")
    log.info(
        "Starting docker container with SciCat backend from %s", docker_compose_file
    )
    configure(docker_compose_file)
    docker.docker_compose_up(docker_compose_file)
    log.info("Waiting for SciCat docker to become accessible")
    wait_until_backend_is_live(max_time=60, n_tries=40)
    log.info("Successfully connected to SciCat backend")


def _backend_docker_down(target_dir: Path) -> None:
    # Check if container is running because the fixture can call this function
    # if there was an exception in _backend_docker_up.
    # In that case, there is nothing to tear down.
    if _backend_is_running():
        docker_compose_file = target_dir / "docker-compose.yaml"
        log = logging.getLogger("scitacean.testing")
        log.info(
            "Stopping docker container with SciCat backend from %s", docker_compose_file
        )
        docker.docker_compose_down(docker_compose_file)


def _backend_is_running() -> bool:
    return docker.container_is_running("scitacean-test-scicat")


__all__ = [
    "scicat_access",
    "scicat_backend",
    "real_client",
    "fake_client",
    "client",
]
