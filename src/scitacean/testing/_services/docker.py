# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)
# ruff: noqa: S603, S607
"""Helpers to manage docker containers.

Primarily meant for testing.
"""

from __future__ import annotations

import json
import os
import subprocess

from .._logging import get_logger


def docker_compose_service_status(
    config_file: os.PathLike[str], service: str, *, project_name: str
) -> str:
    result = subprocess.run(
        [
            "docker",
            "compose",
            "--file",
            os.fspath(config_file),
            "--project-name",
            project_name,
            "ps",
            "--all",
            "--format",
            "json",
            service,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    if not result.stdout.strip():
        return "missing"
    try:
        containers = json.loads(result.stdout)
    except json.JSONDecodeError:
        # Compose can emit one JSON object per line instead of an array.
        containers = [
            json.loads(line) for line in result.stdout.splitlines() if line.strip()
        ]

    if isinstance(containers, dict):
        containers = [containers]
    if not containers:
        return "missing"

    states = [
        (container.get("State"), container.get("Health", ""))
        for container in containers
        if isinstance(container, dict)
    ]
    if len(states) != len(containers):
        raise ValueError("Unexpected container entry from `docker compose ps`.")
    if any(state == "running" and health == "unhealthy" for state, health in states):
        return "unhealthy"
    if all(
        state == "running" and health in ("", "healthy") for state, health in states
    ):
        return "ready"
    return "not-ready"


def docker_compose_up(
    config_file: os.PathLike[str], *services: str, project_name: str
) -> None:
    get_logger().info(
        f"Starting docker containers in project {project_name} from file "
        f"{config_file} with services {services}."
    )
    subprocess.check_call(
        [
            "docker",
            "compose",
            "--file",
            os.fspath(config_file),
            "--project-name",
            project_name,
            "up",
            "--detach",
            "--wait",
            "--wait-timeout",
            "120",
            *services,
        ]
    )


def docker_compose_down(config_file: os.PathLike[str], *, project_name: str) -> None:
    # `docker compose down` returns successfully when no containers are running.
    get_logger().info(
        f"Stopping all docker containers in project {project_name} from file "
        f"{config_file}."
    )
    subprocess.check_call(
        [
            "docker",
            "compose",
            "--file",
            os.fspath(config_file),
            "--project-name",
            project_name,
            "down",
            "--volumes",
        ]
    )
