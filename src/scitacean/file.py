# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Class to represent files."""

from __future__ import annotations

import dataclasses
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import NoReturn, Optional, Union, cast

from .error import IntegrityError
from .filesystem import RemotePath, checksum_of_file, file_modification_time, file_size
from .logging import get_logger
from .model import DataFile


@dataclasses.dataclass(frozen=True)
class File:
    """Store local and remote paths and metadata for a file.

    There are two central properties:

    - ``remote_path``: Path to the remote file relative to the dataset's
      ``source_folder``. This is always set, even if the file does not exist
      on the remote filesystem.
    - ``local_path``: Path to the file on the local filesystem.
      Is ``None`` if the file does not exist locally.

    Files can be in one of three states and the state can be changed as shown below.
    The state can be queried using :meth:`File.is_on_local`
    and :meth:`File.is_on_remote`.

    .. code-block:: none

         local                                  remote
           │                                      │
           │ uploaded                  downloaded │
           │                                      │
           └───────────> local+remote <───────────┘
    """

    local_path: Optional[Path]
    """Path to the file on the local filesystem."""
    remote_path: RemotePath
    """Path to the file on the remote filesystem."""
    remote_gid: Optional[str]
    """Unix group ID on remote."""
    remote_perm: Optional[str]
    """Unix file mode on remote."""
    remote_uid: Optional[str]
    """Unix user ID on remote."""
    created_at: Optional[datetime] = None
    """Creator of the file entry in SciCat."""
    created_by: Optional[str] = None
    """Creation time of the file entry in SciCat."""
    updated_at: Optional[datetime] = None
    """Last updator of the file entry in SciCat."""
    updated_by: Optional[str] = None
    """Last update time of the file entry in SciCat."""
    checksum_algorithm: Optional[str] = None
    """Algorithm to use for checksums."""
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
        remote_path: Optional[Union[str, RemotePath]] = None,
        remote_uid: Optional[str] = None,
        remote_gid: Optional[str] = None,
        remote_perm: Optional[str] = None,
    ) -> File:
        """Link a file on the local filesystem.

        Given following ``path``, ``base_path``, and ``source_folder``::

            path:                      somewhere/on/local/folder/file.nxs
            base_bath:                 somewhere/on/local
            source_folder:             remote/storage

        the file will be located on the remote at::

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
            remote_path=RemotePath(remote_path),
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
        """Construct a new file object from SciCat models.

        Parameters
        ----------
        model:
            Pydantic model for the file.
        local_path:
            Value for the local path.

        Returns
        -------
        :
            A new file object.
        """
        return File(
            local_path=Path(local_path) if isinstance(local_path, str) else local_path,
            remote_path=RemotePath(model.path),
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
            return file_size(cast(Path, self.local_path))
        return self._remote_size  # type: ignore[return-value]

    @property
    def creation_time(self) -> datetime:
        """The logical creation time of the SciCat file.

        If the file exists on local, return the time the local file was last modified.
        Otherwise, return the stored time in the catalogue.
        """
        if self.is_on_local:
            return file_modification_time(cast(Path, self.local_path))
        return self._remote_creation_time  # type: ignore[return-value]

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
            return self._checksum_cache.get(  # type: ignore[union-attr]
                path=self.local_path,  # type: ignore[arg-type]
                algorithm=self.checksum_algorithm,
            )
        return self._remote_checksum

    def remote_access_path(
        self, source_folder: Union[RemotePath, str]
    ) -> Optional[RemotePath]:
        """Full path to the file on the remote if it exists."""
        return (source_folder / self.remote_path) if self.is_on_remote else None

    @property
    def is_on_remote(self) -> bool:
        """True if the file is on remote."""
        return self._remote_size is not None

    @property
    def is_on_local(self) -> bool:
        """True if the file is on local."""
        return self.local_path is not None

    def make_model(self, *, for_archive: bool = False) -> DataFile:
        """Build a pydantic model for this file.

        Parameters
        ----------
        for_archive:
            Select whether the file is stored in an archive or on regular disk,
            that is whether it belongs to a Datablock or an OrigDatablock.

        Returns
        -------
        :
            A new pydantic model.
        """
        chk = self.checksum()
        # TODO if for_archive: ensure not out of date
        return DataFile(
            path=os.fspath(self.remote_path),
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
        remote_path: Optional[Union[str, RemotePath]] = None,
        remote_uid: Optional[str] = None,
        remote_gid: Optional[str] = None,
        remote_perm: Optional[str] = None,
        remote_creation_time: Optional[datetime] = None,
        remote_size: Optional[int] = None,
    ) -> File:
        """Return new file metadata after an upload.

        Assumes that the input file exists on local.
        The returned object is on both local and remote.

        Parameters
        ----------
        remote_path:
            New remote path.
        remote_uid:
            New user ID on remote, overwrites any current value.
        remote_gid:
            New group ID on remote, overwrites any current value.
        remote_perm:
            New unix permissions on remote, overwrites any current value.
        remote_creation_time:
            Time the file became available on remote.
            Defaults to the current time in UTC.
        remote_size:
            File size on remote.

        Returns
        -------
        :
            A new file object.
        """
        if remote_creation_time is None:
            remote_creation_time = datetime.now().astimezone(timezone.utc)
        args = dict(
            remote_path=RemotePath(remote_path) if remote_path is not None else None,
            remote_gid=remote_gid,
            remote_uid=remote_uid,
            remote_perm=remote_perm,
            _remote_creation_time=remote_creation_time,
        )
        return dataclasses.replace(
            self,
            _remote_size=remote_size if remote_size is not None else self.size,
            _remote_checksum=self.checksum(),
            **{key: val for key, val in args.items() if val is not None},
        )

    def downloaded(self, *, local_path: Union[str, Path]) -> File:
        """Return new file metadata after a download.

        Assumes that the input file exists on remote.
        The returned object is on both local and remote.

        Parameters
        ----------
        local_path:
            New local path.

        Returns
        -------
        :
            A new file object.
        """
        return dataclasses.replace(
            self, local_path=Path(local_path), _checksum_cache=_Checksum()
        )

    def validate_after_download(self) -> None:
        """Check that the file on disk matches the metadata.

        Compares file size and, if possible, its checksum.
        Raises on failure.
        If the function returns without exception, the file is valid.

        Raises
        ------
        IntegrityError
            If a check fails.
        """
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
        actual = checksum_of_file(
            cast(Path, self.local_path), algorithm=self.checksum_algorithm
        )
        if actual != stored:
            _log_and_raise(
                IntegrityError,
                f"Checksum of file '{self.local_path}' ({actual}) "
                f"does not match checksum stored in dataset "
                f"({stored}). Using algorithm "
                f"'{self.checksum_algorithm}'.",
            )

    def _validate_after_download_file_size(self) -> None:
        actual = file_size(cast(Path, self.local_path))
        if actual != self._remote_size:
            get_logger().info(
                "Size of downloaded file '%s' (%d bytes) does not "
                "match size reported in dataset (%d bytes)."
                "This may be due to a difference in file systems and perfectly fine. "
                "Or it is caused by an error during download.",
                self.local_path,
                actual,
                self._remote_size,
            )


def _log_and_raise(typ: type, msg: str) -> NoReturn:
    get_logger().error(msg)
    raise typ(msg)


class _Checksum:
    """Compute and cache the checksum of a file."""

    def __init__(self) -> None:
        self._value: Optional[str] = None
        self._path: Optional[Path] = None
        self._algorithm: Optional[str] = None
        self._access_time: Optional[datetime] = None

    def get(self, *, path: Path, algorithm: str) -> str:
        if self._is_out_of_date(path=path, algorithm=algorithm):
            self._update(path=path, algorithm=algorithm)
        return self._value  # type: ignore[return-value]

    def _is_out_of_date(self, *, path: Path, algorithm: str) -> bool:
        return (
            self._access_time is None
            or path != self._path
            or algorithm != self._algorithm
            or file_modification_time(path) > self._access_time
        )

    def _update(self, *, path: Path, algorithm: str) -> None:
        self._value = checksum_of_file(path, algorithm=algorithm)
        self._path = path
        self._algorithm = algorithm
        self._access_time = datetime.now(tz=timezone.utc)
