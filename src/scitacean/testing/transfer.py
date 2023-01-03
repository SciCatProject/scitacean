# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    from pyfakefs.fake_filesystem import FakeFilesystem
except ImportError:
    FakeFilesystem = Any

from ..file import File
from ..filesystem import RemotePath
from ..pid import PID


class FakeDownloadConnection:
    def __init__(self, fs: Optional[FakeFilesystem], files: Dict[RemotePath, bytes]):
        self.files = files
        self.fs = fs

    def download_file(self, *, remote, local):
        if self.fs is not None:
            self.fs.create_file(local, contents=self.files[remote])
        else:
            with open(local, "wb") as f:
                f.write(self.files[remote])

    def download_files(self, *, remote: List[str], local: List[Path]):
        for r, l in zip(remote, local):
            self.download_file(remote=r, local=l)


class FakeUploadConnection:
    def __init__(
        self,
        files: Dict[RemotePath, bytes],
        reverted: Dict[RemotePath, bytes],
        dataset_id: PID,
    ):
        self.files = files
        self.reverted = reverted
        self._dataset_id = dataset_id

    @property
    def source_dir(self) -> RemotePath:
        return RemotePath("/remote") / self._dataset_id.pid

    def _remote_path(self, filename: RemotePath) -> RemotePath:
        return self.source_dir / filename

    def _upload_file(self, *, remote: RemotePath, local: Path) -> RemotePath:
        remote = self._remote_path(remote)
        with open(local, "rb") as f:
            self.files[remote] = f.read()
        return remote

    def upload_files(self, *files: File) -> List[File]:
        for file in files:
            self._upload_file(remote=file.remote_path, local=file.local_path)
        return files

    def revert_upload(self, *files: File):
        for file in files:
            remote = self._remote_path(file.remote_path)
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
        self.files = _remote_path_dict(files)
        self.reverted = _remote_path_dict(reverted)

    @contextmanager
    def connect_for_download(self):
        yield FakeDownloadConnection(fs=self.fs, files=self.files)

    @contextmanager
    def connect_for_upload(self, dataset_id: PID):
        yield FakeUploadConnection(
            files=self.files, reverted=self.reverted, dataset_id=dataset_id
        )


def _remote_path_dict(
    d: Optional[Dict[Union[str, RemotePath], bytes]]
) -> Dict[RemotePath, bytes]:
    if d is None:
        return {}
    return {RemotePath(path): contents for path, contents in d.items()}
