# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scowl contributors (https://github.com/SciCatProject/scowl)
# @author Jan-Lukas Wynen

from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
from typing import Optional, Union

from pyscicat.model import DataFile


class File:
    def __init__(
        self,
        *,
        source_path: Union[str, Path],
        source_folder: Optional[Union[str, Path]],
        local_path: Optional[Union[str, Path]],
        model: Optional[DataFile],
    ):
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
    def model(self) -> Optional[DataFile]:
        return self._model

    def with_model_from_local_file(self) -> File:
        # TODO checksum once supported by the model
        assert self._local_path is not None
        st = self._local_path.stat()
        return File(
            source_path=self._source_path,
            source_folder=self._source_folder,
            local_path=self._local_path,
            model=DataFile(
                path=str(self.source_path), size=st.st_size, time=_creation_time_str(st)
            ),
        )

    def provide_locally(self, directory: Union[str, Path], *, downloader) -> Path:
        directory = Path(directory)
        directory.mkdir(exist_ok=True)
        local_path = directory / self.source_path
        downloader.get(local=local_path, remote=self.remote_access_path)
        self._local_path = local_path
        return local_path

    def __repr__(self):
        return (
            f"File(source_folder={self.source_folder}, source_path={self.source_path}, "
            f"local_path={self.local_path}, model={self.model!r})"
        )


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
def md5sum(path: Union[str, Path]) -> str:
    md5 = hashlib.md5()
    buffer = memoryview(bytearray(128 * 1024))
    with open(path, "rb", buffering=0) as file:
        for n in iter(lambda: file.readinto(buffer), 0):
            md5.update(buffer[:n])
    return md5.hexdigest()
