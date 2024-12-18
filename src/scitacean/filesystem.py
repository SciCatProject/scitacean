# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Filesystem utilities.

Scitacean distinguishes between paths on the local filesystem and
paths on the remote file server.
The former are encoded ad :class:`pathlib.Path`
and the latter as :class:`scitacean.filesystem.RemotePath`.
But conversions from plain strings are usually supported but should be used with care.
"""

from __future__ import annotations

import hashlib
import os
import re
from datetime import datetime, timezone
from pathlib import Path, PurePath
from typing import Any, TypeVar

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema


class RemotePath:
    """A path on the remote filesystem.

    Remote paths do not need to correspond to a regular filesystem path like
    :class:`pathlib.PosixPath` or :class:`pathlib.WindowsPath`.
    Instead, they can be any sequence of segments that are joined by forward slashes,
    e.g. a URL.

    RemotePath is strict about input types in order to prompt the user to think about
    correct, cross-platform handling of paths.
    In particular, there is only limited interoperability with local paths as
    the two should almost never be mixed.
    """

    def __init__(self, *path_segments: str | RemotePath) -> None:
        """Initialize from given path segments."""
        for segment in path_segments:
            if isinstance(segment, (PurePath, Path)):  # type: ignore[unreachable]
                raise TypeError(
                    "OS paths are not supported by RemotePath.__init__. "
                    "use RemotePath.from_local instead."
                )
            if not isinstance(segment, (str, RemotePath)):
                raise TypeError(
                    "Expected str or RemotePath, " f"got {type(segment).__name__}"
                )
        self._path = "/".join(s for segment in path_segments if (s := _posix(segment)))

    @classmethod
    def from_local(cls, path: PurePath) -> RemotePath:
        """Create a RemotePath from a local, OS-specific path.

        On Windows, the drive is preserved which is likely not what you want.
        So it is recommended to use this function only with relative paths.
        """
        return RemotePath(path.as_posix())

    def to_local(self) -> PurePath:
        """Return self as a local, OS-specific path.

        This returns only the file name, discarding all parent path segments.
        """
        return PurePath(self.name)

    def __truediv__(self, other: str | RemotePath) -> RemotePath:
        """Join two path segments."""
        if isinstance(other, (PurePath, Path)):  # type: ignore[unreachable]
            raise TypeError("OS paths are not supported when concatenating RemotePath.")

        if _posix(other).startswith("/"):
            return RemotePath(other)  # other is absolute, do not concatenate

        this = _strip_trailing_slash(self.posix)
        other = _strip_leading_slash(_strip_trailing_slash(_posix(other)))
        return RemotePath(f"{this}/{other}")

    def __rtruediv__(self, other: str) -> RemotePath:
        """Join two path segments."""
        return RemotePath(other) / self

    def __str__(self) -> str:
        """Return a type-qualified representation of the path.

        Use path.posix to get a plain path.
        """
        return repr(self)

    def __repr__(self) -> str:
        return f"RemotePath({self.posix!r})"

    @property
    def posix(self) -> str:
        """Return the path for use on a POSIX filesystem, i.e. with forward slashes."""
        return self._path

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
    def suffix(self) -> str | None:
        """The file extension including a leading period."""
        parts = self.name.rsplit(".", 1)
        if len(parts) == 1:
            return None
        return "." + parts[1]

    @property
    def parent(self) -> RemotePath:
        """The logical parent of the path."""
        parts = self._path.rstrip("/").rsplit("/", 1)
        base = "/" if self._path.startswith("/") else "."
        if len(parts) == 1:
            return RemotePath(base)
        return RemotePath(parts[0] or base)

    def truncated(self, max_length: int = 255) -> RemotePath:
        """Return a new remote path with all path segments truncated.

        Parameters
        ----------
        max_length:
            Maximum length of each segment.
            The default value is the typical maximum length on Linux.

        Returns
        -------
        :
            A new remote path with truncated segments.
        """

        def trunc(seg: str) -> str:
            # First, make sure that the name is short enough to fit the suffix
            # such that the suffix does not get truncated.
            # But keep at least one character of the name.
            # Then make sure the whole segment is short enough, potentially
            # truncating the suffix.
            parts = seg.rsplit(".", 1)
            name = parts[0]
            suffix = "." + parts[1] if len(parts) > 1 else ""
            return (name[: max(1, max_length - len(suffix))] + suffix)[:max_length]

        return RemotePath("/".join(map(trunc, self._path.split("/"))))

    @classmethod
    def validate(cls, value: str | RemotePath) -> RemotePath:
        """Pydantic validator for RemotePath fields."""
        return RemotePath(value)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls,
            core_schema.union_schema(
                [core_schema.is_instance_schema(RemotePath), core_schema.str_schema()]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda p: p.posix if isinstance(p, RemotePath) else str(p),
                info_arg=False,
                return_schema=core_schema.str_schema(),
            ),
        )


def _posix(path: str | RemotePath) -> str:
    return path.posix if isinstance(path, RemotePath) else path


def _strip_trailing_slash(s: str) -> str:
    return s[:-1] if s.endswith("/") else s


def _strip_leading_slash(s: str) -> str:
    return s[1:] if s.startswith("/") else s


def file_size(path: Path) -> int:
    """Return the size of a local file in bytes."""
    return path.stat().st_size


def file_modification_time(path: Path) -> datetime:
    """Return the time in UTC when a local file was last modified."""
    return datetime.fromtimestamp(path.stat().st_mtime).astimezone(timezone.utc)


def _new_hash(algorithm: str) -> Any:
    return hashlib.new(algorithm, usedforsecurity=False)


# size based on http://git.savannah.gnu.org/gitweb/?p=coreutils.git;a=blob;f=src/ioblksize.h;h=ed2f4a9c4d77462f357353eb73ee4306c28b37f1;hb=HEAD#l23  # noqa: E501
def checksum_of_file(path: str | Path, *, algorithm: str) -> str:
    """Compute the checksum of a local file.

    Parameters
    ----------
    path:
        Path of the file on the local filesystem.
    algorithm:
        Hash algorithm to use. Can be any algorithm supported by :func:`hashlib.new`.

    Returns
    -------
    :
        The hex digest of the hash.
    """
    chk = _new_hash(algorithm)
    buffer = memoryview(bytearray(128 * 1024))
    with open(path, "rb", buffering=0) as file:
        for n in iter(lambda: file.readinto(buffer), 0):
            chk.update(buffer[:n])
    return chk.hexdigest()  # type: ignore[no-any-return]


P = TypeVar("P", bound=str | Path | RemotePath)


def escape_path(path: P) -> P:
    """Escape disallowed characters for file paths.

    Replaces

    - Unicode characters using ``"backslashreplace"``.
      See the
      `Python docs <https://docs.python.org/3/library/codecs.html#error-handlers>`_.
    - Non-word characters by '_'. This includes backslashes
      introduced by the above.

    The result should be a valid path name on Linux, macOS, and Windows.

    Parameters
    ----------
    path:
        Input string or path.

    Returns
    -------
    :
        ``path`` with offending characters replaced.
        Has the same type as ``path``.
    """
    s = (
        path.posix if isinstance(path, RemotePath) else os.fspath(path)  # type: ignore[arg-type]
    )
    no_utf = s.encode("ascii", "backslashreplace").decode("ascii")
    return type(path)(re.sub(r"[^\w .\-]", "_", no_utf))  # type: ignore[return-value]
