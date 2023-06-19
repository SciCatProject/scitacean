# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
import importlib.resources
import os
import time
from copy import deepcopy
from typing import Any, Union
from urllib.parse import urljoin

import requests
import yaml

from ..._internal.docker import docker_compose_down, docker_compose_up
from . import config

_PathLike = Union[str, os.PathLike]


def _read_yaml(filename: str) -> Any:
    if hasattr(importlib.resources, "files"):
        # Use new API added in Python 3.9
        return yaml.safe_load(
            importlib.resources.files("scitacean.testing.backend")
            .joinpath(filename)
            .read_text()
        )
    # Old API, deprecated as of Python 3.11
    return yaml.safe_load(
        importlib.resources.read_text("scitacean.testing.backend", filename)
    )


def _docker_compose_template() -> dict:
    return _read_yaml("docker-compose-backend-template.yaml")


def _apply_config(template: dict) -> dict:
    res = deepcopy(template)
    scicat = res["services"]["scicat"]
    ports = scicat["ports"][0].split(":")
    scicat["ports"] = [f"{ports[0]}:{config.SCICAT_PORT}"]

    env = scicat["environment"]
    env["PORT"] = config.SCICAT_PORT
    env["PID_PREFIX"] = config.PID_PREFIX
    env["SITE"] = config.SITE

    return res


def configure(target_path: _PathLike) -> None:
    """Build a docker-compose file for the testing backend."""
    c = yaml.dump(_apply_config(_docker_compose_template()))
    if "PLACEHOLDER" in c:
        raise RuntimeError("Incorrect config")

    with open(target_path, "w") as f:
        f.write(c)


def start_backend(docker_compose_file: _PathLike) -> None:
    """Start the docker container with SciCat backend."""
    docker_compose_up(docker_compose_file)


def stop_backend(docker_compose_file: _PathLike) -> None:
    """Stop the docker container with SciCat backend and remove volumes."""
    docker_compose_down(docker_compose_file)


def can_connect() -> bool:
    """Test the connection to the testing SciCat backend."""
    scicat_access = config.local_access("user1")
    try:
        response = requests.post(
            urljoin(scicat_access.url, "Users/login"),
            json=scicat_access.user.credentials,
            timeout=0.5,
        )
    except requests.ConnectionError:
        return False
    return response.ok


def wait_until_backend_is_live(max_time: float, n_tries: int) -> None:
    """Sleep until a connection to the backend can be made.

    The backend takes a few seconds to become usable after the
    docker container was started.
    This function attempts to connect periodically until the connection
    succeeds or ``max_time`` is reached.

    Parameters
    ----------
    max_time:
        Maximum time in seconds to wait for the backend to become usable.
    n_tries:
        Number of connection attempts within ``max_time``.

    Raises
    ------
    RuntimeError
        If no connection can be made within the time limit.
    """
    for _ in range(n_tries):
        if can_connect():
            return
        time.sleep(max_time / n_tries)
    if not can_connect():
        raise RuntimeError("Cannot connect to backend")
