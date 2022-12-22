# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen
"""Filesystem utilities.

Local paths are stored as pathlib.Path
Remote paths are stored as scitacean.filesystem.RemotePath
"""

from __future__ import annotations

import os
from typing import Callable, Generator, Optional, Union


class RemotePath(os.PathLike):
    """A path on the remote filesystem.

    Remote paths need not correspond to a regular filesystem path like
    :class:`pathlib.PosixPath` or :class:`pathlib.WindowsPath`.
    Instead, they can be any sequence of segments that are joined by forward slashes,
    e.g. a URL.
    """

    def __init__(self, path: Union[str, RemotePath]):
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

    def __fspath__(self) -> str:
        """Return the file system representation of the path."""
        return str(self)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, (RemotePath, str)):
            return False
        return str(self) == str(other)

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
        return RemotePath(value)


def _strip_trailing_slash(s: str) -> str:
    return s[:-1] if s.endswith("/") else s


def _strip_leading_slash(s: str) -> str:
    return s[1:] if s.startswith("/") else s
