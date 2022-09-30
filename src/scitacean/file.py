# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen

from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
from typing import Optional, Union

from pyscicat.model import DataFile

from .error import IntegrityError
from .logging import get_logger
from .typing import Downloader


class File:
    def __init__(
        self,
        *,
        source_path: Union[str, Path],
        source_folder: Optional[Union[str, Path]],
        local_path: Optional[Union[str, Path]],
        model: Optional[DataFile],
    ):
        # TODO sourcePath is not required to be an actual Path. Could be, e.g. URL
        self._source_path = Path(source_path)  # relative to source folder
        self._source_folder = Path(source_folder) if source_folder is not None else None
        self._local_path = Path(local_path) if local_path is not None else None
        self._model = model

    @classmethod
    def from_local(
        cls, path: Union[str, Path], *, relative_to: Union[str, Path] = ""
    ) -> File:
        return File(
            source_path=Path(relative_to) / Path(path).name,
            source_folder=None,
            local_path=path,
            model=None,
        )

    @classmethod
    def from_scicat(cls, model: DataFile, sourceFolder: str) -> File:
        return File(
            source_path=model.path,
            source_folder=sourceFolder,
            local_path=None,
            model=model,
        )

    @property
    def source_path(self) -> Path:
        return self._source_path

    @property
    def source_folder(self) -> Optional[Path]:
        return self._source_folder

    @source_folder.setter
    def source_folder(self, value: Optional[Union[str, Path]]):
        self._source_folder = Path(value) if value is not None else None

    @property
    def remote_access_path(self) -> Optional[str]:
        return (
            None
            if self.source_folder is None
            else self._source_folder / self.source_path
        )

    @property
    def local_path(self) -> Optional[Path]:
        return self._local_path

    @property
    def checksum(self) -> Optional[str]:
        return self._model.chk

    @property
    def model(self) -> Optional[DataFile]:
        return self._model

    def with_model_from_local_file(self, *, checksum_algorithm: str = "md5") -> File:
        assert self._local_path is not None
        st = self._local_path.stat()
        chk = checksum_of_file(self._local_path, algorithm=checksum_algorithm)
        return File(
            source_path=self._source_path,
            source_folder=self._source_folder,
            local_path=self._local_path,
            model=DataFile(
                path=str(self.source_path),
                size=st.st_size,
                time=_creation_time_str(st),
                chk=chk,
            ),
        )

    def provide_locally(
        self,
        directory: Union[str, Path],
        *,
        downloader: Downloader,
        checksum_algorithm: Optional[str],
    ) -> Path:
        directory = Path(directory)
        directory.mkdir(exist_ok=True)  # TODO undo if later fails
        local_path = directory / self.source_path
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
            f"File(source_folder={self.source_folder}, source_path={self.source_path}, "
            f"local_path={self.local_path}, model={self.model!r})"
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


# size based on http://git.savannah.gnu.org/gitweb/?p=coreutils.git;a=blob;f=src/ioblksize.h;h=ed2f4a9c4d77462f357353eb73ee4306c28b37f1;hb=HEAD#l23  # noqa
def checksum_of_file(path: Union[str, Path], *, algorithm: str) -> str:
    chk = hashlib.new(algorithm)
    buffer = memoryview(bytearray(128 * 1024))
    with open(path, "rb", buffering=0) as file:
        for n in iter(lambda: file.readinto(buffer), 0):
            chk.update(buffer[:n])
    return chk.hexdigest()
