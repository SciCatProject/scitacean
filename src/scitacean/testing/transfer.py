# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen
from contextlib import contextmanager
import os
from pathlib import Path
from typing import Dict, Optional, Union

from ..pid import PID


class FakeDownloadConnection:
    def __init__(self, fs, files: Dict[str, bytes]):
        self.files = files
        self.fs = fs

    def download_file(self, *, remote, local):
        self.fs.create_file(local, contents=self.files[remote])


class FakeUploadConnection:
    def __init__(
        self,
        fs,
        files: Dict[str, bytes],
        reverted: Optional[Dict[str, bytes]],
        dataset_id: PID,
    ):
        self.files = files
        self.reverted = reverted
        self.fs = fs
        self._dataset_id = dataset_id

    @property
    def source_dir(self) -> str:
        return f"/remote/{self._dataset_id.pid}/"

    def _remote_path(self, filename) -> str:
        return os.path.join(self.source_dir, filename)

    def upload_file(self, *, remote: Union[str, Path], local: Union[str, Path]) -> str:
        remote = self._remote_path(remote)
        with open(local, "rb") as f:
            self.files[remote] = f.read()
        return remote

    def revert_upload(self, *, remote: Union[str, Path], local: Union[str, Path] = ""):
        remote = self._remote_path(remote)
        self.reverted[remote] = self.files.pop(remote)


class FakeFileTransfer:
    def __init__(
        self,
        *,
        fs,
        files: Optional[Dict[str, bytes]] = None,
        reverted: Optional[Dict[str, bytes]] = None,
    ):
        self.files = {} if files is None else files
        self.reverted = {} if reverted is None else reverted
        self.fs = fs

    @contextmanager
    def connect_for_download(self):
        yield FakeDownloadConnection(self.files, self.fs)

    @contextmanager
    def connect_for_upload(self, dataset_id: PID):
        yield FakeUploadConnection(self.fs, self.files, self.reverted, dataset_id)
