# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)

import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional, Type, Union

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

# TODO docs: need to use scicat_backend in order to seed dbase
#      docs: possible to hang during creation if docker already running


@pytest.fixture(scope="session")
def scicat_access() -> SciCatAccess:
    return local_access("user1")


@pytest.fixture()
def fake_client(scicat_access) -> FakeClient:
    client = FakeClient.from_credentials(
        url=scicat_access.url, **scicat_access.user.credentials
    )
    client.datasets.update({ds.pid: ds for ds in seed.INITIAL_DATASETS.values()})
    client.orig_datablocks.update(
        {dbs[0].datasetId: dbs for dbs in seed.INITIAL_ORIG_DATABLOCKS.values()}
    )
    return client


@pytest.fixture()
def real_client(scicat_access, scicat_backend) -> Optional[Client]:
    if not scicat_backend:
        return None
    return Client.from_credentials(
        url=scicat_access.url, **scicat_access.user.credentials
    )


@pytest.fixture(params=["real", "fake"])
def client(request, scicat_backend) -> Union[Client, FakeClient]:
    if request.param == "fake":
        return request.getfixturevalue("fake_client")
    skip_if_not_backend(request)
    return request.getfixturevalue("real_client")


@pytest.fixture()
def require_scicat_backend(request, scicat_backend) -> None:
    skip_if_not_backend(request)


@pytest.fixture(scope="session")
def scicat_backend(
    request: pytest.FixtureRequest, tmp_path_factory, scicat_access
) -> bool:
    """Spin up a SciCat and seed backend.

    Returns True if backend tests are enabled and False otherwise.
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
    counter: Union[FileCounter, NullCounter],
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
    counter: Union[FileCounter, NullCounter],
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
    client_class: Union[Type[Client], Type[FakeClient]],
    scicat_access: SciCatAccess,
    target_dir: Path,
) -> None:
    client = client_class.from_credentials(
        url=scicat_access.url, **scicat_access.user.credentials
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
    wait_until_backend_is_live(max_time=20, n_tries=20)
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
