# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Fake file transfer."""

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any, TypeVar

try:
    from pyfakefs.fake_filesystem import FakeFilesystem
except ImportError:
    from typing import TypeAlias

    FakeFilesystem: TypeAlias = Any  # type: ignore[no-redef]

from ..dataset import Dataset
from ..file import File
from ..filesystem import RemotePath
from ..transfer.util import source_folder_for

RemotePathOrStr = TypeVar("RemotePathOrStr", RemotePath, str, RemotePath | str)


# TODO add conditionally_disabled feature and remove custom transfers in tests
class FakeDownloadConnection:
    """'Download' files from a fake file transfer."""

    def __init__(self, fs: FakeFilesystem | None, files: dict[RemotePath, bytes]):
        self.files = files
        self.fs = fs

    def download_file(self, *, remote: RemotePath, local: Path) -> None:
        """Download a single file."""
        if self.fs is not None:
            self.fs.create_file(local, contents=self.files[remote])
        else:
            with open(local, "wb") as f:
                f.write(self.files[remote])

    def download_files(self, *, remote: list[RemotePath], local: list[Path]) -> None:
        """Download multiple files."""
        for r, l in zip(remote, local, strict=True):
            self.download_file(remote=r, local=l)


class FakeUploadConnection:
    """'Upload' files to a fake file transfer."""

    def __init__(
        self,
        files: dict[RemotePath, bytes],
        reverted: dict[RemotePath, bytes],
        source_folder: RemotePath,
    ):
        self.files = files
        self.reverted = reverted
        self._source_folder = source_folder

    def _remote_path(self, filename: RemotePath) -> RemotePath:
        return self._source_folder / filename

    def _upload_file(self, *, remote: RemotePath, local: Path | None) -> RemotePath:
        if local is None:
            raise ValueError(f"No local path for file {remote}")
        remote = self._remote_path(remote)
        with open(local, "rb") as f:
            self.files[remote] = f.read()
        return remote

    def upload_files(self, *files: File) -> list[File]:
        """Upload files."""
        for file in files:
            self._upload_file(remote=file.remote_path, local=file.local_path)
        return list(files)

    def revert_upload(self, *files: File) -> None:
        """Remove uploaded files."""
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
                url="...", token="...", file_transfer=FakeFileTransfer(fs=fs)
            )
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
        fs: FakeFilesystem | None = None,
        files: Mapping[RemotePathOrStr, bytes] | None = None,
        reverted: Mapping[RemotePathOrStr, bytes] | None = None,
        source_folder: str | RemotePath | None = None,
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
        source_folder:
            Upload files to this folder if set.
            Otherwise, upload to the dataset's source_folder.
            Ignored when downloading files.
        """
        self.fs = fs
        self.files = _remote_path_dict(files)
        self.reverted = _remote_path_dict(reverted)
        self._source_folder_pattern = source_folder

    def source_folder_for(self, dataset: Dataset) -> RemotePath:
        """Return the source folder for a given dataset."""
        return source_folder_for(dataset, self._source_folder_pattern)

    @contextmanager
    def connect_for_download(self) -> Iterator[FakeDownloadConnection]:
        """Open a connection for downloads."""
        yield FakeDownloadConnection(fs=self.fs, files=self.files)

    @contextmanager
    def connect_for_upload(self, dataset: Dataset) -> Iterator[FakeUploadConnection]:
        """Open a connection for uploads."""
        yield FakeUploadConnection(
            files=self.files,
            reverted=self.reverted,
            source_folder=self.source_folder_for(dataset),
        )


def _remote_path_dict(
    d: Mapping[RemotePathOrStr, bytes] | None,
) -> dict[RemotePath, bytes]:
    if d is None:
        return {}
    return {RemotePath(path): contents for path, contents in d.items()}
