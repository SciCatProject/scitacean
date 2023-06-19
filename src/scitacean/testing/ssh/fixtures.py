# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)

import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Optional

import fabric
import fabric.config
import pytest

from ..._internal.docker import docker_compose, docker_compose_run
from ._pytest_helpers import skip_if_not_ssh, ssh_enabled
from ._ssh import IgnorePolicy, configure, local_access, wait_until_server_is_live


@pytest.fixture(scope="session")
def ssh_access(request):
    skip_if_not_ssh(request)
    return local_access()


@pytest.fixture(scope="session")
def ssh_config_dir(request) -> Optional[Path]:
    if not ssh_enabled(request):
        yield None
        return

    # Ideally, we would use tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    # See module docstring for why.
    # But the cleanup option was only added in Python 3.10.
    tmp = Path(tempfile.gettempdir())
    tempdir = tmp / uuid.uuid4().hex
    tempdir.mkdir(exist_ok=False)
    yield Path(tempdir)
    shutil.rmtree(tempdir, ignore_errors=True)


@pytest.fixture(scope="session")
def ssh_data_dir(ssh_config_dir) -> Optional[Path]:
    if ssh_config_dir is None:
        yield None
        return

    yield ssh_config_dir / "data"


@pytest.fixture(scope="session")
def ssh_fileserver(
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

    config_file = configure(ssh_config_dir)
    with docker_compose(config_file):
        wait_until_server_is_live(ssh_access, max_time=20, n_tries=20)
        # Give the user write access.
        docker_compose_run(
            config_file, "scitacean-test-ssh-server", "chown", "1000:1000", "/data"
        )
        yield True


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
