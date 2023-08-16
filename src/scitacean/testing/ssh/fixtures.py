# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
# mypy: disable-error-code="no-untyped-def"
"""Pytest fixtures to manage and access a local SSH server."""

import logging
from pathlib import Path
from typing import Callable, Generator, Optional

import fabric
import fabric.config
import pytest

from ..._internal import docker
from .._pytest_helpers import init_work_dir, root_tmp_dir
from ._pytest_helpers import skip_if_not_ssh, ssh_enabled
from ._ssh import (
    IgnorePolicy,
    SSHAccess,
    configure,
    local_access,
    wait_until_ssh_server_is_live,
)


@pytest.fixture(scope="session")
def ssh_access(request: pytest.FixtureRequest) -> SSHAccess:
    """Fixture that returns SSH access parameters.

    Returns
    -------
    :
        A URL and user to connect to the testing SSH server.
        The user has access to all initial files registered in the
        database and permissions to create new files.
    """
    skip_if_not_ssh(request)
    return local_access()


@pytest.fixture(scope="session")
def ssh_base_dir(
    request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory
) -> Optional[Path]:
    """Fixture that returns the base working directory for the SSH server setup.

    Returns
    -------
    :
        A path to a directory on the host machine.
        The directory gets populated by the
        :func:`scitacean.testing.ssh.fixtures.ssh_fileserver` fixture.
        It contains the docker configuration and volumes.

        Returns ``None`` if SSH tests are disabled
    """
    if not ssh_enabled(request):
        return None
    return root_tmp_dir(request, tmp_path_factory) / "scitacean-ssh"


@pytest.fixture(scope="session")
def ssh_data_dir(ssh_base_dir: Optional[Path]) -> Optional[Path]:
    """Fixture that returns the data directory for the SSH server setup.

    Returns
    -------
    :
        A path to a directory on the host machine.
        The directory is mounted as ``/data`` on the server.

        Returns ``None`` if SSH tests are disabled
    """
    if ssh_base_dir is None:
        return None
    return ssh_base_dir / "data"


@pytest.fixture()
def require_ssh_fileserver(request, ssh_fileserver) -> None:
    """Fixture to declare that a test needs a local SSH server.

    Like :func:`scitacean.testing.ssh.ssh_fileserver`
    but this skips the test if SSH tests are disabled.
    """
    skip_if_not_ssh(request)


@pytest.fixture(scope="session")
def ssh_fileserver(
    request: pytest.FixtureRequest,
    ssh_access: SSHAccess,
    ssh_base_dir: Optional[Path],
    ssh_data_dir: Optional[Path],
    ssh_connect_with_username_password,
) -> Generator[bool, None, None]:
    """Fixture to declare that a test needs a local SSH server.

    If SSH tests are enabled, this fixture configures and starts an SSH server
    in a docker container the first time a test requests it.
    The server and container will be stopped and removed at the end of the test session.

    Does nothing if the SSH tests are disabled.

    Returns
    -------
    :
        True if SSH tests are enabled and False otherwise.
    """
    if ssh_base_dir is None:
        yield False
        return

    target_dir, counter = init_work_dir(request, ssh_base_dir, name=None)

    try:
        with counter.increment() as count:
            if count == 1:
                _ssh_docker_up(target_dir, ssh_access)
            elif not _ssh_server_is_running():
                raise RuntimeError("Expected SSH server to be running")
        yield True
    finally:
        with counter.decrement() as count:
            if count == 0:
                _ssh_docker_down(target_dir)


@pytest.fixture(scope="session")
def ssh_connection_config() -> fabric.config.Config:
    """Fixture that returns the configuration for fabric.Connection for tests.

    Can be used to open SSH connections if ``SSHFileTransfer`` is not enough.
    """
    config = fabric.config.Config()
    config["load_ssh_configs"] = False
    config["connect_kwargs"] = {
        "allow_agent": False,
        "look_for_keys": False,
    }
    return config


@pytest.fixture(scope="session")
def ssh_connect_with_username_password(
    ssh_access: SSHAccess, ssh_connection_config: fabric.config.Config
) -> Callable[..., fabric.Connection]:
    """Fixture that returns a function to create a connection to the testing SSH server.

    Uses username+password and rejects any other authentication attempt.

    Returns
    -------
    :
        A function to pass as the ``connect`` argument to
        :meth:`scitacean.transfer.ssh.SSHFileTransfer.connect_for_download`
        or :meth:`scitacean.transfer.ssh.SSHFileTransfer.connect_for_upload`.

    Examples
    --------
    Explicitly connect to the

    .. code-block:: python

        def test_ssh(ssh_access, ssh_connect_with_username_password, ssh_fileserver):
            ssh = SSHFileTransfer(host=ssh_access.host, port=ssh_access.port)
            with ssh.connect_for_download(
                connect=ssh_connect_with_username_password
            ) as connection:
                # use connection
    """

    def connect(host: str, port: int, **kwargs):
        if kwargs:
            raise ValueError(
                "ssh_connect_with_username_password must only be"
                f" used without extra arguments. Got {kwargs=}"
            )
        connection = fabric.Connection(
            host=host,
            port=port,
            user=ssh_access.user.username,
            config=ssh_connection_config,
            connect_kwargs={
                "password": ssh_access.user.password,
                **ssh_connection_config.connect_kwargs,
            },
        )
        connection.client.set_missing_host_key_policy(IgnorePolicy())
        return connection

    return connect


def _ssh_docker_up(target_dir: Path, ssh_access: SSHAccess) -> None:
    if _ssh_server_is_running():
        raise RuntimeError("SSH docker container is already running")
    docker_compose_file = target_dir / "docker-compose.yaml"
    log = logging.getLogger("scitacean.testing")
    log.info("Starting docker container with SSH server from %s", docker_compose_file)
    configure(target_dir)
    docker.docker_compose_up(docker_compose_file)
    log.info("Waiting for SSH docker to become accessible")
    wait_until_ssh_server_is_live(ssh_access=ssh_access, max_time=20, n_tries=20)
    log.info("Successfully connected to SSH server")
    # Give the user write access.
    docker.docker_compose_run(
        docker_compose_file, "scitacean-test-ssh-server", "chown", "1000:1000", "/data"
    )


def _ssh_docker_down(target_dir: Path) -> None:
    # Check if container is running because the fixture can call this function
    # if there was an exception in _ssh_docker_up.
    # In that case, there is nothing to tear down.
    if _ssh_server_is_running():
        docker_compose_file = target_dir / "docker-compose.yaml"
        log = logging.getLogger("scitacean.testing")
        log.info(
            "Stopping docker container with SSH server from %s", docker_compose_file
        )
        docker.docker_compose_down(docker_compose_file)


def _ssh_server_is_running() -> bool:
    return docker.container_is_running("scitacean-test-ssh")
