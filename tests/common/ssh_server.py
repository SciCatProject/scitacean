# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)

import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

import fabric
import fabric.config
import paramiko
import pytest
import yaml

from .docker import docker_compose

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
def ssh_access():
    return _load_config()


@pytest.fixture(scope="session")
def ssh_config_dir(request) -> Optional[Path]:
    if not request.config.getoption(_COMMAND_LINE_OPTION):
        yield None
        return

    with tempfile.TemporaryDirectory() as tempdir:
        yield Path(tempdir)


@pytest.fixture(scope="session")
def ssh_data_dir(ssh_config_dir) -> Optional[Path]:
    if ssh_config_dir is None:
        yield None
        return

    yield ssh_config_dir / "data"


@pytest.fixture(scope="session")
def ssh_fileserver(request, ssh_access, ssh_config_dir):
    """Spin up an SSH server.

    Does nothing unless the --ssh-tests command line option is set.
    """
    if not request.config.getoption(_COMMAND_LINE_OPTION):
        yield False
        return

    config_file = configure(ssh_config_dir)
    with docker_compose(config_file):
        wait_until_backend_is_live(ssh_access, max_time=20, n_tries=20)
        yield True


def configure(target_dir: Union[Path, str]) -> Path:
    """Generate a config file for docker compose and symlink seed data."""
    target_dir = Path(target_dir)
    target_seed_dir = target_dir / "data" / "seed"
    target_seed_dir.parent.mkdir()
    target_seed_dir.symlink_to(_SEED_DIR)
    # (target_dir/"data"/"asd").mkdir()

    with open(_SSH_SERVER_DOCKER_CONFIG, "r") as f:
        config = yaml.safe_load(f)
    service = config["services"]["scitacean-test-ssh-server"]

    # Mount the base data dir. This gives the user write access.
    service.setdefault("volumes", []).append(f"{target_dir / 'data'}:/data")
    # Mount the initial data via the symlink created above.
    # This gives the user read access.
    service.setdefault("volumes", []).append(f"{target_seed_dir}:/data/seed")

    target = target_dir / _SSH_SERVER_DOCKER_CONFIG.name
    with open(target, "w") as f:
        yaml.dump(config, f)
    return target


def can_connect(ssh_access: SSHAccess) -> bool:
    try:
        make_client(ssh_access)
    except paramiko.SSHException:
        return False
    return True


def wait_until_backend_is_live(ssh_access: SSHAccess, max_time: float, n_tries: int):
    # The container takes a while to be fully live.
    for _ in range(n_tries):
        if can_connect(ssh_access):
            return
        time.sleep(max_time / n_tries)
    if not can_connect(ssh_access):
        raise RuntimeError("Cannot connect to SSH server")


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


@pytest.fixture()
def ssh_connection_config():
    """Return configuration for fabric.Connection."""
    config = fabric.config.Config()
    config["load_ssh_configs"] = False
    config["connect_kwargs"] = {
        "allow_agent": False,
        "look_for_keys": False,
    }
    return config


@pytest.fixture()
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
