# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)
# ruff: noqa: S603, S607
"""Helpers to manage docker containers.

Primarily meant for testing.
"""

import json
import os
import subprocess
from typing import Any

_PathLike = str | os.PathLike[str]


def docker_compose_up(config_file: _PathLike, *services: str) -> None:
    subprocess.check_call(
        [
            "docker",
            "compose",
            "--file",
            os.fspath(config_file),
            "up",
            "--detach",
            "--force-recreate",
            *services,
        ]
    )


def docker_compose_down(config_file: _PathLike) -> None:
    subprocess.check_call(
        ["docker", "compose", "--file", os.fspath(config_file), "down", "--volumes"]
    )


def docker_compose_run(config_file: _PathLike, service: str, *cmd: str) -> None:
    subprocess.check_call(
        ["docker", "compose", "--file", os.fspath(config_file), "run", service, *cmd]
    )


def _try_parse_json(s: str) -> Any:
    # The precise output of `docker ps` can vary.
    # So parse it leniently; if a line isn't valid JSON, it surely does not
    # contain a container name.
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return None


def container_is_running(name: str) -> bool:
    ps = subprocess.run(
        ["docker", "ps", "--format=json"], stdout=subprocess.PIPE, check=True
    )
    lines = ps.stdout.decode(encoding="utf-8").split("\n")
    containers = [x for line in lines if (x := _try_parse_json(line))]
    for container in containers:
        names = container["Names"]
        if (isinstance(names, str) and names == name) or name in names:
            return True
    return False
