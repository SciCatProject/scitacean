# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Manager for Scitacean testing sessions."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager, nullcontext
from pathlib import Path
from typing import Self

import filelock

from ._logging import get_logger

_PROJECT_TAG_FILENAME = ".SCITACEAN_TESTING_PROJECT"
_DEFAULT_PROJECT_NAME = "scitacean-testing-project"
_PROJECT_LOCK_FILENAME = "scitacean.project.lock"
_DOCKER_LOCK_FILENAME = "docker.lock"
_DOCKER_FOLDER_NAME = "docker"
_DOCKER_TAG_FILENAME = ".SCITACEAN_DOCKER_PROJECT"
_DOCKER_COMPOSE_FILENAME = "docker-compose.yaml"
_DOCKER_STARTED_FILENAME = ".docker-compose-started"


class TestingProject:
    """Manager for a Scitacean testing session."""

    def __init__(
        self, path: Path, *, project_name: str, scicat_version: str | None
    ) -> None:
        self._path = path
        self._project_name = project_name
        self._scicat_version = scicat_version
        self._docker_lock = filelock.FileLock(path / _DOCKER_LOCK_FILENAME)

    @classmethod
    def get_or_create(
        cls,
        base: Path,
        *,
        project_name: str = _DEFAULT_PROJECT_NAME,
        scicat_version: str | None = None,
    ) -> TestingProject:
        """Get an existing project if it exists, else create a new testing project."""
        with cls._project_lock(base):
            if (
                existing := cls.load_existing(
                    base,
                    project_name=project_name,
                    scicat_version=scicat_version,
                    _no_lock=True,
                )
            ) is not None:
                return existing
            return cls.new(
                base,
                project_name=project_name,
                scicat_version=scicat_version,
                _no_lock=True,
            )

    @classmethod
    def new(
        cls,
        base: Path,
        *,
        project_name: str = _DEFAULT_PROJECT_NAME,
        scicat_version: str | None = None,
        _no_lock: bool = False,
    ) -> Self:
        """Create a new testing project."""
        with nullcontext() if _no_lock else cls._project_lock(base):
            return cls(
                _create_project_directory(
                    base, project_name=project_name, tag_filename=_PROJECT_TAG_FILENAME
                ),
                project_name=project_name,
                scicat_version=scicat_version,
            )

    @classmethod
    def load_existing(
        cls,
        base: Path,
        *,
        project_name: str = _DEFAULT_PROJECT_NAME,
        scicat_version: str | None = None,
        _no_lock: bool = False,
    ) -> Self | None:
        """Load an existing testing project if it exists."""
        with nullcontext() if _no_lock else cls._project_lock(base):
            path = _locate_project_directory(
                base, project_name=project_name, tag_filename=_PROJECT_TAG_FILENAME
            )
            if path is None:
                return None
            return cls(path, project_name=path.name, scicat_version=scicat_version)

    @classmethod
    @contextmanager
    def _project_lock(cls, base: Path) -> Generator[None, None, None]:
        """Lock project creation and short-lived shared project operations."""
        # This lock ensures that when there are multiple processes,
        # only one creates a project and the others can await the creation.
        with filelock.FileLock(base / _PROJECT_LOCK_FILENAME):
            yield

    @contextmanager
    def lock(self):
        """Acquire the lock for short-lived project initialization tasks."""
        with self._project_lock(self._path.parent):
            yield

    def _configure_services(self) -> Path:
        """Configure the Docker Compose project without starting its services.

        Does NOT lock.
        """
        from ._services.config import configure_services

        path = _ensure_docker_directory(self.docker_path)
        compose_file = path / _DOCKER_COMPOSE_FILENAME
        if not compose_file.is_file():
            configure_services(
                path,
                docker_filename=_DOCKER_COMPOSE_FILENAME,
                scicat_version=self._scicat_version,
            )
        return compose_file

    def ensure_running(self, service: str) -> None:
        """Ensure that a Docker Compose service is running and healthy."""
        from ._services.docker import (
            docker_compose_service_status,
            docker_compose_up,
        )

        with self._docker_lock:
            compose_file = self._configure_services()
            status = docker_compose_service_status(
                compose_file, service, project_name=self._project_name
            )
            self._path.joinpath(_DOCKER_STARTED_FILENAME).touch()
            if status == "unhealthy":
                raise RuntimeError(
                    f"Docker Compose service {service!r} in project "
                    f"{self._project_name!r} is unhealthy."
                )
            if status == "ready":
                return
            docker_compose_up(compose_file, service, project_name=self._project_name)

    @property
    def path(self) -> Path:
        """Return the path to the testing project."""
        return self._path

    @property
    def project_name(self) -> str:
        """Return the name of the testing project."""
        return self._project_name

    @property
    def docker_path(self) -> Path:
        return self._path / _DOCKER_FOLDER_NAME

    @property
    def _docker_compose_path(self) -> Path:
        return self.docker_path / _DOCKER_COMPOSE_FILENAME

    def teardown(self) -> None:
        """Stop services started by this testing project, if any."""
        started = self._path / _DOCKER_STARTED_FILENAME
        compose_file = self._docker_compose_path
        try:
            with self._docker_lock:
                if started.is_file() and compose_file.is_file():
                    from ._services.docker import docker_compose_down

                    get_logger().info("Tearing down Scitacean testing project")
                    docker_compose_down(compose_file, project_name=self._project_name)
                    started.unlink()
        except Exception as error:
            get_logger().error("Error during teardown: %s", error)
            raise


def _locate_project_directory(
    base: Path, *, project_name: str, tag_filename: str
) -> Path | None:
    """Find a directory of a Scitacean testing project."""
    path = base / project_name
    if not path.exists():
        return None
    if not path.joinpath(tag_filename).exists():
        raise RuntimeError(
            f"Directory {path} exists but is not a Scitacean testing project."
        )
    return path


def _create_project_directory(
    base: Path, *, project_name: str, tag_filename: str
) -> Path:
    """Create a directory for a Scitacean testing project."""
    path = base / project_name
    try:
        path.mkdir(parents=True, exist_ok=False)
    except OSError as error:
        error.add_note(f"When creating Scitacean testing project {project_name}")
        raise
    path.joinpath(tag_filename).touch()
    return path


def _ensure_docker_directory(path: Path) -> Path:
    """Create or validate the directory holding Docker Compose configuration."""
    if not path.exists():
        path.mkdir()
        (path / _DOCKER_TAG_FILENAME).touch()
    elif not (path / _DOCKER_TAG_FILENAME).is_file():
        raise RuntimeError(
            f"Directory {path} exists but is not a Scitacean Docker project."
        )
    return path
