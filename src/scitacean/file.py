# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen
"""Class to represent files."""

from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path, PurePosixPath
from typing import Optional, Union

import dateutil.parser
from pyscicat.model import DataFile

from .error import IntegrityError
from .logging import get_logger
from .typing import Downloader


class File:
    """Store local and remote paths and metadata for a file.

    There are two central properties:

    - ``remote_access_path``: Full path to the remote file if the file exists
      on the file server. Is ``None`` if the file does not exist on the remote.
    - ``local_path``: Path to the file on the local filesystem if it exists.
      Is ``None`` if the file does not exist locally.
    """

    def __init__(
        self,
        *,
        source_folder: Optional[str],
        local_path: Optional[Union[str, Path]],
        model: DataFile,
    ):
        self._local_path = Path(local_path) if local_path is not None else None
        self._source_folder = str(source_folder) if source_folder is not None else None
        # remote_path is stored as model.path
        self._model = model

    @classmethod
    def from_local(
        cls,
        path: Union[str, Path],
        *,
        base_path: Union[str, Path] = "",
        remote_path: Optional[Union[str, PurePosixPath]] = None,
        source_folder: Optional[Union[str, PurePosixPath]] = None,
        checksum_algorithm: str = "md5",
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

        ``remote_path`` can also be overriden, in which case ``path`` and
        ``base_path`` are not used to deduce the "actual remote location".

        Parameters
        ----------
        path:
            Full path the local file.
        base_path:
            Only use ``path.relative_to(base_path)`` to determine the remote location.
        remote_path:
            Path on the remote, relative to ``source_folder``.
        source_folder:
            Base path on the remote.
            Must be ``None`` if the file does not exist on the remote.
        checksum_algorithm:
            Algorithm used to compute the file's checksum. See :mod:`hashlib`.
        remote_uid:
            User ID on the remote. Will be determined automatically on upload.
        remote_gid:
            Group ID on the remote. Will be determined automatically on upload.
        remote_perm:
            File permissions on the remote. Will be determined automatically on upload.
        """
        path = Path(path)
        if not remote_path:
            remote_path = path.relative_to(base_path)
        return File(
            local_path=path,
            source_folder=source_folder,
            model=file_model_from_local_file(
                path,
                remote_path=remote_path,
                checksum_algorithm=checksum_algorithm,
                uid=remote_uid,
                gid=remote_gid,
                perm=remote_perm,
            ),
        )

    @classmethod
    def from_scicat(
        cls,
        model: DataFile,
        *,
        source_folder: Union[str, PurePosixPath],
        local_path: Union[str, Path] = None,
    ) -> File:
        return File(
            source_folder=source_folder,
            local_path=local_path,
            model=model,
        )

    @property
    def source_folder(self) -> Optional[str]:
        """Base path on the remote.

        Is ``None`` if the files is not on the remote.
        """
        return self._source_folder

    @source_folder.setter
    def source_folder(self, value: Optional[str]):
        """Set the base path on the remote.

        Must be consistent with the path in the dataset!
        """
        self._source_folder = value

    @property
    def remote_access_path(self) -> Optional[str]:
        """Full path to the file on the remote if it exists."""
        return (
            None
            if self.source_folder is None
            else os.path.join(self.source_folder, self.model.path)
        )

    @property
    def local_path(self) -> Optional[Path]:
        """Path to the local file if it exists."""
        return self._local_path

    @property
    def checksum(self) -> Optional[str]:
        """Checksum of the file."""
        return self._model.chk

    @property
    def size(self) -> int:
        """Size in bytes."""
        return self._model.size

    @property
    def creation_time(self) -> datetime:
        """Data and time when the file was created."""
        return dateutil.parser.parse(self.model.time)

    @property
    def model(self) -> Optional[DataFile]:
        return self._model

    def provide_locally(
        self,
        directory: Union[str, Path],
        *,
        downloader: Downloader,
        checksum_algorithm: Optional[str],
    ) -> Path:
        """Download the file to the local filesystem."""
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)  # TODO undo if later fails
        local_path = directory / self.model.path
        with downloader.connect_for_download() as con:
            con.download_file(local=local_path, remote=self.remote_access_path)
        self._local_path = local_path
        self._validate_local_file(checksum_algorithm=checksum_algorithm)
        return local_path

    def _validate_local_file(self, *, checksum_algorithm):
        if not self._model.chk:
            get_logger().info(
                "Dataset does not contain a checksum for file '%s'. Skipping check.",
                self._local_path,
            )
            return self._validate_local_file_size()
        if not checksum_algorithm:
            get_logger().warning(
                "File '%s' has a checksum but no algorithm has been defined. "
                "Skipping check. Checksum is %s",
                self._local_path,
                self._model.chk,
            )
            return self._validate_local_file_size()
        actual = checksum_of_file(self._local_path, algorithm=checksum_algorithm)
        if actual != self._model.chk:
            _log_and_raise(
                IntegrityError,
                f"Checksum of file '{self._local_path}' ({actual}) "
                f"does not match checksum stored in dataset "
                f"({self._model.chk}). Using algorithm "
                f"'{checksum_algorithm}'.",
            )

    def _validate_local_file_size(self):
        st = self._local_path.stat()
        actual = st.st_size
        if actual != self._model.size:
            _log_and_raise(
                IntegrityError,
                f"Size of file '{self._local_path}' ({actual}B) does not "
                f"match size stored in dataset ({self._model.size}B)",
            )

    def __repr__(self):
        return (
            f"File(source_folder={self.source_folder}, local_path={self.local_path}, "
            f"model={self.model!r})"
        )


def _log_and_raise(typ, msg):
    get_logger().error(msg)
    raise typ(msg)


def _creation_time_str(st: os.stat_result) -> str:
    """Return the time in UTC when a file was created.

    Uses modification time as SciCat only cares about the latest version of the file
    and not when it was first created on the local system.
    """
    # TODO is this correct on non-linux?
    # TODO is this correct if the file was created in a different timezone (DST)?
    return (
        datetime.fromtimestamp(st.st_mtime)
        .astimezone(timezone.utc)
        .isoformat(timespec="seconds")
    )


def _new_hash(algorithm: str):
    try:
        return hashlib.new(algorithm, usedforsecurity=False)
    except TypeError:
        # Fallback for Python < 3.9
        return hashlib.new(algorithm)


# size based on http://git.savannah.gnu.org/gitweb/?p=coreutils.git;a=blob;f=src/ioblksize.h;h=ed2f4a9c4d77462f357353eb73ee4306c28b37f1;hb=HEAD#l23  # noqa
def checksum_of_file(path: Union[str, Path], *, algorithm: str) -> str:
    chk = _new_hash(algorithm)
    buffer = memoryview(bytearray(128 * 1024))
    with open(path, "rb", buffering=0) as file:
        for n in iter(lambda: file.readinto(buffer), 0):
            chk.update(buffer[:n])
    return chk.hexdigest()


def file_model_from_local_file(
    path: Path,
    *,
    remote_path: PurePosixPath,
    checksum_algorithm: str,
    uid: Optional[str],
    gid: Optional[str],
    perm: Optional[str],
) -> DataFile:
    st = path.stat()
    chk = checksum_of_file(path, algorithm=checksum_algorithm)
    return DataFile(
        path=str(remote_path),
        size=st.st_size,
        time=_creation_time_str(st),
        chk=chk,
        uid=uid,
        gid=gid,
        perm=perm,
    )
