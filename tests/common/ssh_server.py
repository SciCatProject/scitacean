# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Helpers for running tests with an SSH server.

This is primarily meant for testing ``SSHFileTransfer``.

Use the ``ssh_fileserver`` fixture to manage the server and use ``ssh_access`` to
get all required access parameters.
When the server fixture is first used, it initializes the server using these steps:

1. Create a temporary directory with contents
   tmpdir |
          |- docker-compose-ssh-server.yaml
          |- .env
          |- data |       (read-write)
                  |- seed (symlink to data/ssh_server_seed; read-only)
2. Generate .env file to tell docker where to mount data and data/seed as volumes.
3. Start docker.
4. Make data writable by the user in docker.
   This changes the ownership of data on the host to root (on some machines).

The docker container and its volumes are removed at the end of the tests.
The fixture also tries to remove the temporary directory.
This can fail as the owner of its contents (in particular data)
may have been changed to root.
So cleanup can fail and leave the directory behind.

Use the seed directory (``ssh_data_dir/"seed"``) to test downloads.
Corresponds to ``/data/seed`` on the server.

Use the base data directory (``ssh_data_dir``) to test uploads.
Corresponds to ``/data`` on the server.
"""

import shutil
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

import fabric
import fabric.config
import paramiko
import pytest
import yaml

from .docker import docker_compose, docker_compose_run

_SSH_SERVER_DOCKER_CONFIG = (
    Path(__file__).resolve().parent / "docker-compose-ssh-server.yaml"
)
_SEED_DIR = Path(__file__).resolve().parent / "data/ssh_server_seed"
_COMMAND_LINE_OPTION = "--ssh-tests"


@dataclass
class SSHAccess:
    host: str
    port: int
    username: str
    password: str


def _load_config() -> SSHAccess:
    with open(_SSH_SERVER_DOCKER_CONFIG, "r") as f:
        config = yaml.safe_load(f)
    service = config["services"]["scitacean-test-ssh-server"]
    env = {k: v for k, v in map(lambda s: s.split("="), service["environment"])}
    return SSHAccess(
        host="localhost",
        port=service["ports"][0].split(":")[0],
        username=env["USER_NAME"],
        password=env["USER_PASSWORD"],
    )


@pytest.fixture(scope="session")
def ssh_access(request):
    skip_if_not_ssh(request)
    return _load_config()


@pytest.fixture(scope="session")
def ssh_config_dir(request) -> Optional[Path]:
    if not request.config.getoption(_COMMAND_LINE_OPTION):
        yield None
        return

    # Ideally, we would use tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    # But the cleanup option was only added in Python 3.10.
    # See module docstring for why.
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
    request,
    ssh_access,
    ssh_config_dir,
    ssh_connect_with_username_password,
    ssh_data_dir,
):
    """Spin up an SSH server.

    Does nothing unless the --ssh-tests command line option is set.
    """
    if not request.config.getoption(_COMMAND_LINE_OPTION):
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


def configure(target_dir: Union[Path, str]) -> Path:
    """Generate a config file for docker compose and symlink seed data."""
    target_dir = Path(target_dir)
    target_seed_dir = target_dir / "data" / "seed"
    target_seed_dir.parent.mkdir()
    target_seed_dir.symlink_to(_SEED_DIR)

    config_target = target_dir / _SSH_SERVER_DOCKER_CONFIG.name
    shutil.copyfile(_SSH_SERVER_DOCKER_CONFIG, config_target)

    with open(target_dir / ".env", "w") as f:
        f.write(
            f"""DATA_DIR={target_dir / 'data'}
SEED_DIR={target_seed_dir}"""
        )

    return config_target


def can_connect(ssh_access: SSHAccess) -> bool:
    try:
        make_client(ssh_access)
    except paramiko.SSHException:
        return False
    return True


def wait_until_server_is_live(ssh_access: SSHAccess, max_time: float, n_tries: int):
    # The container takes a while to be fully live.
    for _ in range(n_tries):
        if can_connect(ssh_access):
            return
        time.sleep(max_time / n_tries)
    if not can_connect(ssh_access):
        raise RuntimeError("Cannot connect to SSH server")


def cleanup_data_dir(ssh_access, ssh_connect_with_username_password):
    # Delete all directories created by tests.
    # These are owned by root on the host and cannot be deleted by Python's tempfile.
    connection = ssh_connect_with_username_password(
        host=ssh_access.host, port=ssh_access.port
    )
    connection.run(
        "find /data -not -path '/data' -not -path '/data/seed' | xargs rm -rf",
        hide=True,
        in_stream=False,
    )


def skip_if_not_ssh(request):
    if not request.config.getoption(_COMMAND_LINE_OPTION):
        pytest.skip(
            "Tests against an SSH file server are disabled, "
            f"use {_COMMAND_LINE_OPTION} to enable them"
        )


# Every time we create a container, it gets a new host key.
# So simply accept any host keys.
class IgnorePolicy(paramiko.MissingHostKeyPolicy):
    def missing_host_key(self, client, hostname, key):
        return


def make_client(ssh_access: SSHAccess) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(IgnorePolicy())
    client.connect(
        hostname=ssh_access.host,
        port=ssh_access.port,
        username=ssh_access.username,
        password=ssh_access.password,
        allow_agent=False,
        look_for_keys=False,
    )
    return client


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
            user=ssh_access.username,
            config=ssh_connection_config,
            connect_kwargs={
                "password": ssh_access.password,
                **ssh_connection_config.connect_kwargs,
            },
        )
        connection.client.set_missing_host_key_policy(IgnorePolicy())
        return connection

    return connect
