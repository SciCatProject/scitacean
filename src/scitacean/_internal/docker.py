# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Helpers to manage docker containers.

Primarily meant for testing.
"""
import json
import os
import subprocess
from contextlib import contextmanager
from typing import Union

_PathLike = Union[str, os.PathLike]


def docker_compose_up(config_file: _PathLike, *services: str):
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


def docker_compose_down(config_file: _PathLike):
    subprocess.check_call(
        ["docker", "compose", "--file", os.fspath(config_file), "down", "--volumes"]
    )


@contextmanager
def docker_compose(config_file: _PathLike, *services: str):
    docker_compose_up(config_file, *services)
    try:
        yield
    finally:
        docker_compose_down(config_file)


def docker_compose_run(config_file: _PathLike, service: str, *cmd: str):
    subprocess.check_call(
        ["docker", "compose", "--file", os.fspath(config_file), "run", service, *cmd]
    )


def container_is_running(name: str) -> bool:
    ps = subprocess.run(
        ["docker", "ps", "--format=json"], stdout=subprocess.PIPE, check=True
    )
    lines = ps.stdout.decode(encoding="utf-8").split("\n")
    containers = [json.loads(line) for line in lines if line]
    for container in containers:
        names = container["Names"]
        if (isinstance(names, str) and names == name) or name in names:
            return True
    return False
