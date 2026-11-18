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
_LOCK_FILENAME = "project.lock"
_CREATION_LOCK_FILENAME = "scitacean.project-creation.lock"


class TestingProject:
    """Manager for a Scitacean testing session."""

    def __init__(self, path: Path, *, project_name: str) -> None:
        self._path = path
        self._project_name = project_name
        self._lock = filelock.FileLock(path / _LOCK_FILENAME)

    @classmethod
    def get_or_create(
        cls, base: Path, *, project_name: str = _DEFAULT_PROJECT_NAME
    ) -> TestingProject:
        """Get an existing project if it exists, else create a new testing project."""
        with cls._creation_lock(base):
            if (
                existing := cls.load_existing(
                    base, project_name=project_name, _no_lock=True
                )
            ) is not None:
                return existing
            return cls.new(base, project_name=project_name, _no_lock=True)

    @classmethod
    def new(
        cls,
        base: Path,
        *,
        project_name: str = _DEFAULT_PROJECT_NAME,
        _no_lock: bool = False,
    ) -> Self:
        """Create a new testing project."""
        with nullcontext() if _no_lock else cls._creation_lock(base):
            return cls(
                _create_project_directory(
                    base, project_name=project_name, tag_filename=_PROJECT_TAG_FILENAME
                ),
                project_name=project_name,
            )

    @classmethod
    def load_existing(
        cls,
        base: Path,
        *,
        project_name: str = _DEFAULT_PROJECT_NAME,
        _no_lock: bool = False,
    ) -> Self | None:
        """Load an existing testing project if it exists."""
        with nullcontext() if _no_lock else cls._creation_lock(base):
            path = _locate_project_directory(
                base, project_name=project_name, tag_filename=_PROJECT_TAG_FILENAME
            )
            if path is None:
                return None
            return cls(path, project_name=path.name)

    @classmethod
    @contextmanager
    def _creation_lock(cls, base: Path) -> Generator[None, None, None]:
        """Get the lock for creating or opening a testing project."""
        # This lock ensures that when there are multiple processes,
        # only one creates a project and the others can await the creation.
        with filelock.FileLock(base / _CREATION_LOCK_FILENAME):
            yield

    @contextmanager
    def lock(self):
        """Acquire the project lock."""
        with self._lock:
            yield

    @property
    def path(self) -> Path:
        """Return the path to the testing project."""
        return self._path

    @property
    def project_name(self) -> str:
        """Return the name of the testing project."""
        return self._project_name

    def teardown(self) -> None:
        get_logger().info("Tearing down Scitacean testing project")
        for task in reversed(self._teardown_stack):
            try:
                task()
            except Exception as error:
                get_logger().error("Error during teardown: %s", error)


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
