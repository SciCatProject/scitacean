# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Filesystem utilities.

Local paths are stored as pathlib.Path
Remote paths are stored as scitacean.filesystem.RemotePath
"""

from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Generator, Optional, Union


class RemotePath(os.PathLike):  # type: ignore[type-arg]
    """A path on the remote filesystem.

    Remote paths need not correspond to a regular filesystem path like
    :class:`pathlib.PosixPath` or :class:`pathlib.WindowsPath`.
    Instead, they can be any sequence of segments that are joined by forward slashes,
    e.g. a URL.
    """

    def __init__(self, path: Union[str, RemotePath]):
        """Initialize from a given path."""
        self._path = os.fspath(path)

    def __truediv__(self, other: Union[str, RemotePath]) -> RemotePath:
        """Join two path segments."""
        this = _strip_trailing_slash(os.fspath(self))
        other = _strip_leading_slash(_strip_trailing_slash(os.fspath(other)))
        return RemotePath(f"{this}/{other}")

    def __rtruediv__(self, other: str) -> RemotePath:
        """Join two path segments."""
        return RemotePath(other) / self

    def __str__(self) -> str:
        return self._path

    def __repr__(self) -> str:
        return f"RemotePath({str(self)})"

    def __fspath__(self) -> str:
        """Return the file system representation of the path."""
        return str(self)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, (RemotePath, str)):
            return False
        return self._path == RemotePath(other)._path

    def __hash__(self) -> int:
        return hash(self._path)

    @property
    def name(self) -> str:
        """The name of the file with all directories removed."""
        return self._path.rstrip("/").rsplit("/", 1)[-1]

    @property
    def suffix(self) -> Optional[str]:
        """The file extension including a leading period."""
        parts = self.name.rsplit(".", 1)
        if len(parts) == 1:
            return None
        return "." + parts[1]

    @classmethod
    def __get_validators__(
        cls,
    ) -> Generator[Callable[[Union[str, RemotePath]], RemotePath], None, None]:
        yield cls.validate

    @classmethod
    def validate(cls, value: Union[str, RemotePath]) -> RemotePath:
        """Pydantic validator for RemotePath fields."""
        return RemotePath(value)


def _strip_trailing_slash(s: str) -> str:
    return s[:-1] if s.endswith("/") else s


def _strip_leading_slash(s: str) -> str:
    return s[1:] if s.startswith("/") else s


def file_size(path: Path) -> int:
    """Return the size of a file in bytes."""
    return path.stat().st_size


def file_modification_time(path: Path) -> datetime:
    """Return the time in UTC when a file was last modified."""
    return datetime.fromtimestamp(path.stat().st_mtime).astimezone(timezone.utc)


def _new_hash(algorithm: str) -> Any:
    try:
        return hashlib.new(algorithm, usedforsecurity=False)
    except TypeError:
        # Fallback for Python < 3.9
        return hashlib.new(algorithm)


# size based on http://git.savannah.gnu.org/gitweb/?p=coreutils.git;a=blob;f=src/ioblksize.h;h=ed2f4a9c4d77462f357353eb73ee4306c28b37f1;hb=HEAD#l23  # noqa: E501
def checksum_of_file(path: Union[str, Path], *, algorithm: str) -> str:
    """Compute the checksum of a file.

    Parameters
    ----------
    path:
        Path of the file.
    algorithm:
        Hash algorithm to use. Can be any algorithm supported by :func:`hashlib.new`.

    Returns
    -------
    :
        THe hex digest of the hash.
    """
    chk = _new_hash(algorithm)
    buffer = memoryview(bytearray(128 * 1024))
    with open(path, "rb", buffering=0) as file:
        for n in iter(lambda: file.readinto(buffer), 0):
            chk.update(buffer[:n])
    return chk.hexdigest()  # type: ignore[no-any-return]
