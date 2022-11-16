# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen
from contextlib import contextmanager
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

try:
    from pyfakefs.fake_filesystem import FakeFilesystem
except ImportError:
    FakeFilesystem = Any

from ..pid import PID


class FakeDownloadConnection:
    def __init__(self, fs: Optional[FakeFilesystem], files: Dict[str, bytes]):
        self.files = files
        self.fs = fs

    def download_file(self, *, remote, local):
        if self.fs is not None:
            self.fs.create_file(local, contents=self.files[remote])
        else:
            with open(local, "wb") as f:
                f.write(self.files[remote])


class FakeUploadConnection:
    def __init__(
        self,
        files: Dict[str, bytes],
        reverted: Optional[Dict[str, bytes]],
        dataset_id: PID,
    ):
        self.files = files
        self.reverted = reverted
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
    """Mimic a file down-/upload handler.

    Files are not transferred to a server but loaded into an internal storage.

    It is possible to use a fake file system as implemented by
    `pyfakefs <https://pypi.org/project/pyfakefs/>`_.

    Examples
    --------
    Using the ``fs`` fixture from pyfakefs in pytest:

    .. code-block:: python

        def test_upload(fs):
            client = FakeClient.from_token(
                url="...",
                token="...",
                file_transfer=FakeFileTransfer(fs=fs))
            dset = ...
            client.upload_new_dataset_now(dset)
            assert client.file_transfer.files[expected_remote_path] == file_content

    See Also
    --------
    scitacean.testing.client.FakeClient:
        Client to mimic a SciCat server.
    """

    def __init__(
        self,
        *,
        fs: Optional[FakeFilesystem] = None,
        files: Optional[Dict[str, bytes]] = None,
        reverted: Optional[Dict[str, bytes]] = None,
    ):
        """Initialize a file transfer.

        Parameters
        ----------
        fs:
            Fake filesystem. If given, files are down-/uploaded to/from this
            filesystem instead of the real one.
            If set to ``None``, the real filesystem is used.
        files:
            Initial files stored "on the server".
            Maps file names to contents.
        reverted:
            Files that have been uploaded and subsequently been removed.
        """
        self.fs = fs
        self.files = {} if files is None else files
        self.reverted = {} if reverted is None else reverted

    @contextmanager
    def connect_for_download(self):
        yield FakeDownloadConnection(fs=self.fs, files=self.files)

    @contextmanager
    def connect_for_upload(self, dataset_id: PID):
        yield FakeUploadConnection(
            files=self.files, reverted=self.reverted, dataset_id=dataset_id
        )
