# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)
# mypy: disable-error-code="no-untyped-def"
"""Pytest fixtures to manage and access a local SFTP server."""

import logging
from collections.abc import Callable, Generator
from pathlib import Path

import pytest
from paramiko import SFTPClient, SSHClient

from ..._internal import docker
from .._pytest_helpers import init_work_dir, root_tmp_dir
from ._pytest_helpers import sftp_enabled, skip_if_not_sftp
from ._sftp import (
    IgnorePolicy,
    SFTPAccess,
    configure,
    local_access,
    wait_until_sftp_server_is_live,
)


@pytest.fixture(scope="session")
def sftp_access(request: pytest.FixtureRequest) -> SFTPAccess:
    """Fixture that returns SFTP access parameters.

    Returns
    -------
    :
        A URL and user to connect to the testing SFTP server.
        The user has access to all initial files registered in the
        database and permissions to create new files.
    """
    skip_if_not_sftp(request)
    return local_access()


@pytest.fixture(scope="session")
def sftp_base_dir(
    request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory
) -> Path | None:
    """Fixture that returns the base working directory for the SFTP server setup.

    Returns
    -------
    :
        A path to a directory on the host machine.
        The directory gets populated by the
        :func:`scitacean.testing.sftp.fixtures.sftp_fileserver` fixture.
        It contains the docker configuration and volumes.

        Returns ``None`` if SFTP tests are disabled
    """
    if not sftp_enabled(request):
        return None
    return root_tmp_dir(request, tmp_path_factory) / "scitacean-sftp"


@pytest.fixture(scope="session")
def sftp_data_dir(sftp_base_dir: Path | None) -> Path | None:
    """Fixture that returns the data directory for the SFTP server setup.

    Returns
    -------
    :
        A path to a directory on the host machine.
        The directory is mounted as ``/data`` on the server.

        Returns ``None`` if SFTP tests are disabled
    """
    if sftp_base_dir is None:
        return None
    return sftp_base_dir / "data"


@pytest.fixture
def require_sftp_fileserver(request, sftp_fileserver) -> None:  # noqa: PT004
    """Fixture to declare that a test needs a local SFTP server.

    Like :func:`scitacean.testing.sftp.sftp_fileserver`
    but this skips the test if SFTP tests are disabled.
    """
    skip_if_not_sftp(request)


@pytest.fixture(scope="session")
def sftp_fileserver(
    request: pytest.FixtureRequest,
    sftp_access: SFTPAccess,
    sftp_base_dir: Path | None,
    sftp_data_dir: Path | None,
    sftp_connect_with_username_password,
) -> Generator[bool, None, None]:
    """Fixture to declare that a test needs a local SFTP server.

    If SFTP tests are enabled, this fixture configures and starts an SFTP server
    in a docker container the first time a test requests it.
    The server and container will be stopped and removed at the end of the test session.

    Does nothing if the SFTP tests are disabled.

    Returns
    -------
    :
        True if SFTP tests are enabled and False otherwise.
    """
    if sftp_base_dir is None:
        yield False
        return

    target_dir, counter = init_work_dir(request, sftp_base_dir, name=None)

    try:
        with counter.increment() as count:
            if count == 1:
                _sftp_docker_up(target_dir, sftp_access)
            elif not _sftp_server_is_running():
                raise RuntimeError("Expected SFTP server to be running")
        yield True
    finally:
        with counter.decrement() as count:
            if count == 0:
                _sftp_docker_down(target_dir)


@pytest.fixture(scope="session")
def sftp_connect_with_username_password(
    sftp_access: SFTPAccess,
) -> Callable[[str, int], SFTPClient]:
    """Fixture that returns a function to connect to the testing SFTP server.

    Uses username+password from the test config.

    Returns
    -------
    :
        A function to pass as the ``connect`` argument when constructing a
        :class:`scitacean.transfer.sftp.SFTPFileTransfer`.

    Examples
    --------
    Explicitly connect to the test server:

    .. code-block:: python

        def test_sftp(sftp_access,
                      sftp_connect_with_username_password,
                      sftp_fileserver):
            sftp = SFTPFileTransfer(host=sftp_access.host,
                                    port=sftp_access.port,
                                    connect=sftp_connect_with_username_password)
            with sftp.connect_for_download() as connection:
                # use connection
    """

    def connect(host: str, port: int) -> SFTPClient:
        client = SSHClient()
        client.set_missing_host_key_policy(IgnorePolicy())
        client.connect(
            hostname=host,
            port=port,
            username=sftp_access.user.username,
            password=sftp_access.user.password,
            allow_agent=False,
            look_for_keys=False,
        )
        return client.open_sftp()

    return connect


def _sftp_docker_up(target_dir: Path, sftp_access: SFTPAccess) -> None:
    if _sftp_server_is_running():
        raise RuntimeError("SFTP docker container is already running")
    docker_compose_file = target_dir / "docker-compose.yaml"
    log = logging.getLogger("scitacean.testing")
    log.info("Starting docker container with SFTP server from %s", docker_compose_file)
    configure(target_dir)
    docker.docker_compose_up(docker_compose_file)
    log.info("Waiting for SFTP docker to become accessible")
    wait_until_sftp_server_is_live(sftp_access=sftp_access, max_time=60, n_tries=40)
    log.info("Successfully connected to SFTP server")
    # Give the user write access.
    docker.docker_compose_run(
        docker_compose_file, "scitacean-test-sftp-server", "chown", "1000:1000", "/data"
    )


def _sftp_docker_down(target_dir: Path) -> None:
    # Check if container is running because the fixture can call this function
    # if there was an exception in _sftp_docker_up.
    # In that case, there is nothing to tear down.
    if _sftp_server_is_running():
        docker_compose_file = target_dir / "docker-compose.yaml"
        log = logging.getLogger("scitacean.testing")
        log.info(
            "Stopping docker container with SFTP server from %s", docker_compose_file
        )
        docker.docker_compose_down(docker_compose_file)


def _sftp_server_is_running() -> bool:
    return docker.container_is_running("scitacean-test-sftp")
