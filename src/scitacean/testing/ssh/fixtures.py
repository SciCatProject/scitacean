# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)

import logging
from pathlib import Path
from typing import Optional

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
def ssh_access(request):
    skip_if_not_ssh(request)
    return local_access()


@pytest.fixture(scope="session")
def ssh_config_dir(request, tmp_path_factory) -> Optional[Path]:
    if not ssh_enabled(request):
        return
    return root_tmp_dir(request, tmp_path_factory) / "scitacean-ssh"


@pytest.fixture(scope="session")
def ssh_data_dir(ssh_config_dir) -> Optional[Path]:
    if ssh_config_dir is None:
        return
    return ssh_config_dir / "data"


@pytest.fixture(scope="session")
def ssh_fileserver(
    request,
    ssh_access,
    ssh_config_dir,
    ssh_connect_with_username_password,
    ssh_data_dir,
):
    """Spin up an SSH server.

    Does nothing unless the SSh tests are explicitly enabled.
    """
    if ssh_config_dir is None:
        yield False
        return

    target_dir, counter = init_work_dir(request, ssh_config_dir, name=None)

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
def ssh_connection_config():
    """Return configuration for fabric.Connection."""
    config = fabric.config.Config()
    config["load_ssh_configs"] = False
    config["connect_kwargs"] = {
        "allow_agent": False,
        "look_for_keys": False,
    }
    return config


@pytest.fixture(scope="session")
def ssh_connect_with_username_password(ssh_access, ssh_connection_config):
    """Return a function to create a connection to the testing SSH server.

    Uses username+password and rejects any other authentication attempt.
    """

    def connect(host: str, port: int, **kwargs):
        if kwargs:
            raise ValueError(
                "connect_with_username_password must only be"
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
