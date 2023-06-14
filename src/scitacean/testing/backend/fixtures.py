# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)

import os
import tempfile
from typing import Optional, Union

import pytest

from ..._internal.docker import docker_compose
from ...client import Client
from ..client import FakeClient
from . import seed
from ._backend import configure, wait_until_backend_is_live
from ._pytest_helpers import backend_enabled, skip_if_not_backend
from .config import SciCatAccess, local_access

# TODO docs: need to use scicat_backend in order to seed dbase


@pytest.fixture(scope="session")
def scicat_access() -> SciCatAccess:
    return local_access("user1")


@pytest.fixture()
def fake_client(scicat_access) -> FakeClient:
    client = FakeClient.from_credentials(
        url=scicat_access.url, **scicat_access.user.credentials
    )
    client.datasets.update({ds.pid: ds for ds in seed.INITIAL_DATASETS.values()})
    return client


@pytest.fixture()
def real_client(scicat_access, _scicat_backend_base) -> Optional[Client]:
    if not _scicat_backend_base:
        return None
    return Client.from_credentials(
        url=scicat_access.url, **scicat_access.user.credentials
    )


@pytest.fixture(params=["real", "fake"])
def client(
    request, scicat_backend, real_client, fake_client
) -> Union[Client, FakeClient]:
    if request.param == "fake":
        return fake_client
    skip_if_not_backend(request)
    return real_client


@pytest.fixture(scope="session")
def scicat_backend(_scicat_backend_base, scicat_access) -> bool:
    """Spin up a SciCat and seed backend.

    Does nothing unless the backend-tests command line option is set.
    Returns True if backend tests are enabled and False otherwise.
    """
    if _scicat_backend_base:
        client = Client.from_credentials(
            url=scicat_access.url, **scicat_access.user.credentials
        )
    else:
        client = None
    fake_client = FakeClient.from_credentials(
        url=scicat_access.url, **scicat_access.user.credentials
    )

    seed.seed_database(
        client=client, fake_client=fake_client, scicat_access=scicat_access
    )
    yield _scicat_backend_base


@pytest.fixture(scope="session")
def _scicat_backend_base(request) -> bool:
    """Spin up a SciCat backend."""
    if not backend_enabled(request):
        yield False
        return

    with tempfile.TemporaryDirectory() as temp_dir:
        docker_compose_file = os.path.join(temp_dir, "docker-compose.yaml")
        configure(docker_compose_file)
        with docker_compose(docker_compose_file):
            wait_until_backend_is_live(max_time=20, n_tries=20)
            yield True


__all__ = [
    "scicat_access",
    "scicat_backend",
    "_scicat_backend_base",
    "real_client",
    "fake_client",
    "client",
]
