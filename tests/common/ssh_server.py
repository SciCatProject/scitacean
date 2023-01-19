# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)

from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml

from .docker import docker_compose

_SSH_SERVER_DOCKER_CONFIG = (
    Path(__file__).resolve().parent / "docker-compose-ssh-server.yaml"
)


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
def ssh_fileserver(request, ssh_access):
    """Spin up an SSH server.

    Does nothing unless the --ssh-tests command line option is set.
    """
    if not request.config.getoption("--ssh-tests"):
        yield False

    with docker_compose(_SSH_SERVER_DOCKER_CONFIG):
        yield True
