# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Class to represent files."""

from __future__ import annotations

import dataclasses
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import NoReturn, cast

import dateutil.parser

from .error import IntegrityError
from .filesystem import RemotePath, checksum_of_file, file_modification_time, file_size
from .logging import get_logger
from .model import DownloadDataFile, UploadDataFile


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

    local_path: Path | None
    """Path to the file on the local filesystem."""
    remote_path: RemotePath
    """Path to the file on the remote filesystem."""
    remote_gid: str | None
    """Unix group ID on remote."""
    remote_perm: str | None
    """Unix file mode on remote."""
    remote_uid: str | None
    """Unix user ID on remote."""
    checksum_algorithm: str | None = None
    """Algorithm to use for checksums."""
    _remote_size: int | None = dataclasses.field(default=None, repr=False)
    _remote_creation_time: datetime | None = dataclasses.field(default=None, repr=False)
    _remote_checksum: str | None = dataclasses.field(default=None, repr=False)
    _checksum_cache: _Checksum | None = dataclasses.field(
        default=None, compare=False, repr=False
    )

    @classmethod
    def from_local(
        cls,
        path: str | Path,
        *,
        base_path: str | Path = "",
        remote_path: str | RemotePath | None = None,
        remote_uid: str | None = None,
        remote_gid: str | None = None,
        remote_perm: str | None = None,
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
            Full path of the local file.
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

        Returns
        -------
        :
            A new file object.
        """
        path = Path(path)
        if not remote_path:
            remote_path = RemotePath.from_local(path.relative_to(base_path))
        return File(
            local_path=path,
            remote_path=RemotePath(remote_path),
            remote_gid=remote_gid,
            remote_perm=remote_perm,
            remote_uid=remote_uid,
            _checksum_cache=_Checksum(),
        )

    @classmethod
    def from_remote(
        cls,
        remote_path: str | RemotePath,
        size: int,
        creation_time: datetime | str,
        checksum: str | None = None,
        checksum_algorithm: str | None = None,
        remote_uid: str | None = None,
        remote_gid: str | None = None,
        remote_perm: str | None = None,
    ) -> File:
        """Construct a new file object for a remote file.

        The local path of the returned ``File`` is ``None``.

        Parameters
        ----------
        remote_path:
            Path the remote file relative to the dataset's source folder.
        size:
            Size in bytes on the remote filesystem.
        creation_time:
            Date and time the file was created on the remote filesystem.
            If a ``str``, it is parsed using ``dateutil.parser.parse``.
        checksum:
            Checksum of the file.
        checksum_algorithm:
            Algorithm used to compute the given checksum.
            Must be passed when ``checksum is not None``.
        remote_uid:
            User ID on the remote.
        remote_gid:
            Group ID on the remote.
        remote_perm:
            File permissions on the remote.

        Returns
        -------
        :
            A new file object.


        .. versionadded:: 23.10.0
        """
        if checksum is not None and checksum_algorithm is None:
            raise TypeError(
                "Must specify checksum_algorithm when providing a checksum."
            )

        creation_time = (
            creation_time
            if isinstance(creation_time, datetime)
            else dateutil.parser.parse(creation_time)
        )
        return File(
            local_path=None,
            remote_path=RemotePath(remote_path),
            remote_uid=remote_uid,
            remote_gid=remote_gid,
            remote_perm=remote_perm,
            _remote_size=size,
            _remote_creation_time=creation_time,
            _remote_checksum=checksum,
            checksum_algorithm=checksum_algorithm,
        )

    @classmethod
    def from_download_model(
        cls,
        model: DownloadDataFile,
        *,
        checksum_algorithm: str | None = None,
        local_path: str | Path | None = None,
    ) -> File:
        """Construct a new file object from a SciCat download model.

        Parameters
        ----------
        model:
            Pydantic model for the file.
        checksum_algorithm:
            Algorithm to use to compute the checksum of the file.
        local_path:
            Value for the local path.

        Returns
        -------
        :
            A new file object.
        """
        return File(
            checksum_algorithm=checksum_algorithm,
            local_path=Path(local_path) if isinstance(local_path, str) else local_path,
            remote_path=RemotePath(model.path),  # type: ignore[arg-type]
            remote_gid=model.gid,
            remote_perm=model.perm,
            remote_uid=model.uid,
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

    def checksum(self) -> str | None:
        """Return the checksum of the file.

        This can take a long time to compute for large files.

        If the file exists on local, return the current checksum of the local file.
        Otherwise, return the stored checksum in the catalogue.

        Returns
        -------
        :
            The checksum of the file.
        """
        if not self.is_on_local:
            return self._remote_checksum
        if self.checksum_algorithm is None:
            return None
        return self._checksum_cache.get(  # type: ignore[union-attr]
            path=self.local_path,  # type: ignore[arg-type]
            algorithm=self.checksum_algorithm,
        )

    def remote_access_path(self, source_folder: RemotePath | str) -> RemotePath | None:
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

    def local_is_up_to_date(self) -> bool:
        """Check if the file on local is up-to-date.

        Returns
        -------
        :
            True if the file exists on local and its checksum
            matches the stored checksum for the remote file.
        """
        if not self.is_on_remote:
            return True
        if not self.is_on_local:
            return False
        if self.checksum_algorithm is None:
            warnings.warn(
                "No checksum algorithm has been set, using the default 'blake2b' "
                f"to check if local file '{self.local_path}' is up to date. "
                "There is a very low chance that this yields a false positive "
                "and the file is incorrect. Set an algorithm manually to avoid this.",
                stacklevel=2,
            )
            return self._local_is_up_to_date_with_checksum_algorithm("blake2b")
        return self._local_is_up_to_date_with_checksum_algorithm(
            self.checksum_algorithm
        )

    def _local_is_up_to_date_with_checksum_algorithm(self, algorithm: str) -> bool:
        local_checksum = self._checksum_cache.get(  # type: ignore[union-attr]
            path=self.local_path,  # type: ignore[arg-type]
            algorithm=algorithm,
        )
        return self._remote_checksum == local_checksum

    def make_model(self, *, for_archive: bool = False) -> UploadDataFile:
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
        return UploadDataFile(
            path=self.remote_path.posix,
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
        remote_path: str | RemotePath | None = None,
        remote_uid: str | None = None,
        remote_gid: str | None = None,
        remote_perm: str | None = None,
        remote_creation_time: datetime | None = None,
        remote_size: int | None = None,
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
        args = {
            "remote_path": RemotePath(remote_path) if remote_path is not None else None,
            "remote_gid": remote_gid,
            "remote_uid": remote_uid,
            "remote_perm": remote_perm,
            "_remote_creation_time": remote_creation_time,
        }
        return dataclasses.replace(
            self,
            _remote_size=remote_size if remote_size is not None else self.size,
            _remote_checksum=self.checksum(),
            **{key: val for key, val in args.items() if val is not None},  # type: ignore[arg-type]
        )

    def downloaded(self, *, local_path: str | Path) -> File:
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
        self._value: str | None = None
        self._path: Path | None = None
        self._algorithm: str | None = None
        self._access_time: datetime | None = None

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
