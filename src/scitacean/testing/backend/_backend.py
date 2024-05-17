# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)
import importlib.resources
import os
import time
from copy import deepcopy
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import httpx
import yaml

from ..._internal.docker import docker_compose_down, docker_compose_up
from . import config

_PathLike = str | os.PathLike[str]


def _read_yaml(filename: str) -> Any:
    return yaml.safe_load(
        importlib.resources.files("scitacean.testing.backend")
        .joinpath(filename)
        .read_text()
    )


def _docker_compose_template() -> dict[str, Any]:
    template = _read_yaml("docker-compose-backend-template.yaml")
    return template  # type: ignore[no-any-return]


def _apply_config(
    template: dict[str, Any], account_config_path: Path
) -> dict[str, Any]:
    res = deepcopy(template)
    scicat = res["services"]["scicat"]
    ports = scicat["ports"][0].split(":")
    scicat["ports"] = [f"{ports[0]}:{config.SCICAT_PORT}"]

    env = scicat["environment"]
    env["PORT"] = config.SCICAT_PORT
    env["PID_PREFIX"] = config.PID_PREFIX
    env["SITE"] = config.SITE

    scicat["volumes"] = [
        f"{account_config_path}:/home/node/app/functionalAccounts.json",
    ]

    return res


def configure(target_path: _PathLike) -> None:
    """Build a docker-compose file for the testing backend.

    Parameters
    ----------
    target_path:
        Generate a docker-compose file at this path.
    """
    account_config_path = Path(target_path).parent / "functionalAccounts.json"
    config.dump_account_config(account_config_path)
    c = yaml.dump(_apply_config(_docker_compose_template(), account_config_path))
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


def _can_connect() -> tuple[bool, str]:
    """Test the connection to the testing SciCat backend.

    Returns
    -------
    :
        The first element indicates whether the connection was successful.
        The second element is an error message.
    """
    scicat_access = config.local_access("user1")
    try:
        response = httpx.post(
            urljoin(scicat_access.url, "Users/login"),
            json=scicat_access.user.credentials,
            timeout=0.5,
        )
    except (httpx.NetworkError, httpx.TransportError) as err:
        return False, str(err)
    if response.is_success:
        return True, ""
    return False, str(f"{response}: {response.text}")


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
        if _can_connect()[0]:
            return
        time.sleep(max_time / n_tries)
    ok, err = _can_connect()
    if not ok:
        raise RuntimeError(f"Cannot connect to backend: {err}")
