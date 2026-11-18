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
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from .._logging import get_logger
from .._testing_project import TestingProject
from .config import configure_services

_PROJECT_FOLDER_NAME = "docker"
_PROJECT_TAG_FILENAME = ".SCITACEAN_DOCKER_PROJECT"
_DOCKER_COMPOSE_FILENAME = "docker-compose.yaml"


class DockerComposeProject:
    """Manages the docker-compose project for tests."""

    def __init__(self, base_project: TestingProject) -> None:
        self._base_project = base_project

    @classmethod
    def get_or_create(
        cls, base_project: TestingProject, *, scicat_version: str | None = None
    ) -> DockerComposeProject:
        """Get an existing project if it exists, else create a new testing project."""
        with base_project.lock():
            project_path = base_project.path.joinpath(_PROJECT_FOLDER_NAME)
            if (
                not project_path.exists()
                and not project_path.joinpath(_PROJECT_TAG_FILENAME).exists()
            ):
                _create_project_directory(project_path)
                configure_services(
                    project_path,
                    docker_filename=_DOCKER_COMPOSE_FILENAME,
                    scicat_version=scicat_version,
                )
        return DockerComposeProject(base_project)

    def ensure_running(self, service: str) -> None:
        """Ensure that a service is running and healthy."""
        with self._base_project.lock():
            status = _docker_compose_service_status(
                self._compose_file_path,
                service,
                project_name=self._base_project.project_name,
            )
            if status == "ready":
                return
            if status == "unhealthy":
                raise RuntimeError(
                    f"Docker Compose service {service!r} in project "
                    f"{self._base_project.project_name!r} is unhealthy."
                )
            _docker_compose_up(
                self._compose_file_path,
                service,
                project_name=self._base_project.project_name,
            )

    @property
    def _compose_file_path(self) -> Path:
        return self.path.joinpath(_DOCKER_COMPOSE_FILENAME)

    @property
    def path(self) -> Path:
        """Return the path to the docker compose project."""
        return self._base_project.path.joinpath(_PROJECT_FOLDER_NAME)

    @contextmanager
    def lock(self) -> Generator[None, None, None]:
        """Acquire the project lock."""
        with self._base_project.lock():
            yield

    def teardown(self) -> None:
        """Stop the services for this project, if Compose was configured."""
        with self._base_project.lock():
            if self._compose_file_path.is_file():
                _docker_compose_down(
                    self._compose_file_path,
                    project_name=self._base_project.project_name,
                )


def _create_project_directory(project_path) -> None:
    """Create a directory for a Scitacean Docker project."""
    try:
        project_path.mkdir(parents=True, exist_ok=False)
    except OSError as error:
        error.add_note(f"When creating Scitacean Docker testing project {project_path}")
        raise
    project_path.joinpath(_PROJECT_TAG_FILENAME).touch()


def _docker_compose_service_status(
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


def _docker_compose_up(
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


def _docker_compose_down(config_file: os.PathLike[str], *, project_name: str) -> None:
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
