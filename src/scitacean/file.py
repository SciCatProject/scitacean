# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen
"""Class to represent files."""

from __future__ import annotations

import dataclasses
import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Union

from .error import IntegrityError
from .logging import get_logger
from .model import DataFile


@dataclasses.dataclass(frozen=True)
class File:
    """Store local and remote paths and metadata for a file.

    There are two central properties:

    - ``remote_path``: Path to the remote file relative to the dataset's
      ``source_folder``.
    - ``local_path``: Path to the file on the local filesystem if it exists.
      Is ``None`` if the file does not exist locally.
    """

    local_path: Optional[Path]
    remote_path: str
    remote_gid: Optional[str]
    remote_perm: Optional[str]
    remote_uid: Optional[str]
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    checksum_algorithm: Optional[str] = None
    _remote_size: Optional[int] = dataclasses.field(default=None, repr=False)
    _remote_creation_time: Optional[datetime] = dataclasses.field(
        default=None, repr=False
    )
    _remote_checksum: Optional[str] = dataclasses.field(default=None, repr=False)
    _checksum_cache: Optional[_Checksum] = dataclasses.field(
        default=None, compare=False, repr=False
    )

    @classmethod
    def from_local(
        cls,
        path: Union[str, Path],
        *,
        base_path: Union[str, Path] = "",
        remote_path: Optional[str] = None,
        remote_uid: Optional[str] = None,
        remote_gid: Optional[str] = None,
        remote_perm: Optional[str] = None,
    ) -> File:
        """Link a file on the local filesystem.

        Given following ``path``, ``base_path``, and ``source_folder`` ::

            path:                      somewhere/on/local/folder/file.nxs
            base_bath:                 somewhere/on/local
            source_folder:             remote/storage

        the file will be located on the remote at ::

            -> remote_path:            folder/file.nxs
            -> actual remote location: remote/storage/folder/file.nxs

        ``remote_path`` can also be overridden, in which case ``path`` and
        ``base_path`` are not used to deduce the "actual remote location".

        Parameters
        ----------
        path:
            Full path the local file.
        base_path:
            Only use ``path.relative_to(base_path)`` to determine the remote location.
        remote_path:
            Path on the remote, relative to ``source_folder``.
        remote_uid:
            User ID on the remote. Will be determined automatically on upload.
        remote_gid:
            Group ID on the remote. Will be determined automatically on upload.
        remote_perm:
            File permissions on the remote. Will be determined automatically on upload.
        """
        path = Path(path)
        if not remote_path:
            remote_path = str(path.relative_to(base_path))
        return File(
            local_path=path,
            remote_path=remote_path,
            remote_gid=remote_gid,
            remote_perm=remote_perm,
            remote_uid=remote_uid,
            _checksum_cache=_Checksum(),
        )

    @classmethod
    def from_scicat(
        cls,
        model: DataFile,
        *,
        local_path: Optional[Union[str, Path]] = None,
    ) -> File:
        return File(
            local_path=Path(local_path) if isinstance(local_path, str) else local_path,
            remote_path=model.path,
            remote_gid=model.gid,
            remote_perm=model.perm,
            remote_uid=model.uid,
            created_at=model.createdAt,
            created_by=model.createdBy,
            updated_at=model.updatedAt,
            updated_by=model.updatedBy,
            _remote_size=model.size,
            _remote_creation_time=model.time,
            _remote_checksum=model.chk,
        )

    @property
    def size(self) -> int:
        """The size in bytes of the file.

        If the file exists on local, return the current size of the local file.
        Otherwise, return the stored size in the catalogue.
        """
        if self.is_on_local:
            return _get_file_size(self.local_path)
        return self._remote_size

    @property
    def creation_time(self) -> datetime:
        """The logical creation time of the SciCat file.

        If the file exists on local, return the time the local file was last modified.
        Otherwise, return the stored time in the catalogue.
        """
        if self.is_on_local:
            return _get_modification_time(self.local_path)
        return self._remote_creation_time

    def checksum(self) -> Optional[str]:
        """Return the checksum of the file.

        This can take a long time to compute for large files.

        If the file exists on local, return the current checksum of the local file.
        Otherwise, return the stored checksum in the catalogue.

        Returns
        -------
        :
            The checksum of the file.
        """
        if self.is_on_local:
            if self.checksum_algorithm is None:
                return None
            return self._checksum_cache.get(
                path=self.local_path, algorithm=self.checksum_algorithm
            )
        return self._remote_checksum

    def remote_access_path(self, source_folder) -> Optional[str]:
        """Full path to the file on the remote if it exists."""
        if not self.is_on_remote:
            return None
        return (
            os.path.join(source_folder, self.remote_path) if self.is_on_remote else None
        )

    @property
    def is_on_remote(self) -> bool:
        return self._remote_size is not None

    @property
    def is_on_local(self) -> bool:
        return self.local_path is not None

    def make_model(self, *, for_archive: bool = False) -> DataFile:
        chk = self.checksum()
        # TODO if for_archive: ensure not out of date
        return DataFile(
            path=self.remote_path,
            size=self.size,
            chk=chk,
            gid=self.remote_gid,
            perm=self.remote_perm,
            time=self.creation_time,
            uid=self.remote_uid,
        )

    def uploaded(
        self,
        *,
        remote_path: Optional[str] = None,
        remote_uid: Optional[str] = None,
        remote_gid: Optional[str] = None,
        remote_perm: Optional[str] = None,
        remote_creation_time: Optional[datetime] = None,
    ) -> File:
        if remote_creation_time is None:
            remote_creation_time = datetime.now().astimezone(timezone.utc)
        args = dict(
            remote_path=remote_path,
            remote_gid=remote_gid,
            remote_uid=remote_uid,
            remote_perm=remote_perm,
            _remote_creation_time=remote_creation_time,
        )
        return dataclasses.replace(
            self,
            _remote_size=self.size,
            _remote_checksum=self.checksum(),
            **{key: val for key, val in args.items() if val is not None},
        )

    def downloaded(self, *, local_path) -> File:
        return dataclasses.replace(
            self, local_path=local_path, _checksum_cache=_Checksum()
        )

    def validate_after_download(self):
        self._validate_after_download_file_size()
        if self._remote_checksum is None:
            get_logger().info(
                "Dataset does not contain a checksum for file '%s'. Skipping check.",
                self.local_path,
            )
            return
        stored = self._remote_checksum
        if not self.checksum_algorithm:
            get_logger().warning(
                "File '%s' has a checksum but no algorithm has been set. "
                "Skipping check. Checksum is %s",
                self.local_path,
                stored,
            )
            return
        actual = checksum_of_file(self.local_path, algorithm=self.checksum_algorithm)
        if actual != stored:
            _log_and_raise(
                IntegrityError,
                f"Checksum of file '{self.local_path}' ({actual}) "
                f"does not match checksum stored in dataset "
                f"({stored}). Using algorithm "
                f"'{self.checksum_algorithm}'.",
            )

    def _validate_after_download_file_size(self):
        actual = _get_file_size(self.local_path)
        if actual != self._remote_size:
            _log_and_raise(
                IntegrityError,
                f"Size of file '{self.local_path}' ({actual}B) does not "
                f"match size stored in dataset ({self._remote_size}B)",
            )


def _get_file_size(path: Path) -> int:
    return path.stat().st_size


def _get_modification_time(path: Path) -> datetime:
    """Return the time in UTC when a file was last modified."""
    # TODO is this correct on non-linux?
    # TODO is this correct if the file was created in a different timezone (DST)?
    return datetime.fromtimestamp(path.stat().st_mtime).astimezone(timezone.utc)


def _log_and_raise(typ, msg):
    get_logger().error(msg)
    raise typ(msg)


def _new_hash(algorithm: str):
    try:
        return hashlib.new(algorithm, usedforsecurity=False)
    except TypeError:
        # Fallback for Python < 3.9
        return hashlib.new(algorithm)


# size based on http://git.savannah.gnu.org/gitweb/?p=coreutils.git;a=blob;f=src/ioblksize.h;h=ed2f4a9c4d77462f357353eb73ee4306c28b37f1;hb=HEAD#l23  # noqa: E501
def checksum_of_file(path: Union[str, Path], *, algorithm: str) -> str:
    chk = _new_hash(algorithm)
    buffer = memoryview(bytearray(128 * 1024))
    with open(path, "rb", buffering=0) as file:
        for n in iter(lambda: file.readinto(buffer), 0):
            chk.update(buffer[:n])
    return chk.hexdigest()


class _Checksum:
    """Compute and cache the checksum of a file."""

    def __init__(self):
        self._value = None
        self._path = None
        self._algorithm = None
        self._access_time = None

    def get(self, *, path: Path, algorithm: str) -> str:
        if self._is_out_of_date(path=path, algorithm=algorithm):
            self._update(path=path, algorithm=algorithm)
        return self._value

    def _is_out_of_date(self, *, path: Path, algorithm: str) -> bool:
        return (
            path != self._path
            or algorithm != self._algorithm
            or _get_modification_time(path) > self._access_time
        )

    def _update(self, *, path: Path, algorithm: str):
        self._value = checksum_of_file(path, algorithm=algorithm)
        self._path = path
        self._algorithm = algorithm
        self._access_time = datetime.now(tz=timezone.utc)
