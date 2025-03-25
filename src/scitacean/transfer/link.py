# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 SciCat Project (https://github.com/SciCatProject/scitacean)
"""File transfer that creates symlinks."""

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from ..dataset import Dataset
from ..error import FileNotAccessibleError
from ..file import File
from ..filesystem import RemotePath
from ..logging import get_logger
from ._util import source_folder_for


class LinkDownloadConnection:
    """Connection for 'downloading' files by creating symlinks.

    Should be created using
    :meth:`scitacean.transfer.link.LinkFileTransfer.connect_for_download`.
    """

    def download_files(self, *, remote: list[RemotePath], local: list[Path]) -> None:
        """Download files from the given remote path."""
        for r, l in zip(remote, local, strict=True):
            self.download_file(remote=r, local=l)

    def download_file(self, *, remote: RemotePath, local: Path) -> None:
        """Download a file from the given remote path."""
        get_logger().info(
            "Linking file %s to %s",
            remote,
            local,
        )
        remote_path = Path(remote.posix)
        if not remote_path.exists():
            raise FileNotAccessibleError(
                f"Unable to link to remote file {remote_path}: File does not exist. "
                "This might mean that your machine does not have direct filesystem "
                "access to the file server. Consider using a different file transfer.",
                remote_path=remote,
            )
        local.symlink_to(remote_path)


class LinkUploadConnection:
    """Connection for 'uploading' files with symlinks.

    Should be created using
    :meth:`scitacean.transfer.link.LinkFileTransfer.connect_for_upload`.

    Is not actually implemented!
    """

    def __init__(self, *, source_folder: RemotePath) -> None:
        self._source_folder = source_folder

    @property
    def source_folder(self) -> RemotePath:
        """The source folder this connection uploads to."""
        return self._source_folder

    def remote_path(self, filename: str | RemotePath) -> RemotePath:
        """Return the complete remote path for a given path."""
        return self.source_folder / filename

    def upload_files(self, *files: File) -> list[File]:
        """Upload files to the remote folder."""
        raise NotImplementedError()

    def revert_upload(self, *files: File) -> None:
        """Remove uploaded files from the remote folder."""
        raise NotImplementedError()


class LinkFileTransfer:
    """Upload / download files by creating symlinks.

    This file transfer does not actually upload or download files.
    Instead, it requires that the 'remote' file system is directly
    accessible from the 'local' file system.
    It creates symlinks in the local download folder to the
    'remote' files.

    Note
    ----
    A note on terminology:
    In Scitacean, 'remote' refers to the file server where the data files
    are stored that belong to SciCat datasets.
    In contrast, 'local' refers to the file system of the machine that
    runs the Python process.
    The two filesystems can be the same.
    However, Scitacean maintains a strict separation between the two and
    uses 'downloaders' and 'uploaders' to transfer between them even if that
    transfer is a simple symlink.

    See also the documentation of :class:`scitacean.File`.

    Warning
    -------
    This file transfer does not work on Windows because it converts between
    :class:`RemotePath` and :class:`pathlib.Path`.
    This requires that both use the same directory separators.
    Since :class:`RemotePath` uses UNIX-style forward slashes, it is
    incompatible with Windows paths.
    In practice, this should not be a problem because SciCat file storage
    should never be a Windows server.

    Warning
    -------
    This file transfer cannot upload files.
    Instead, consider copying or moving the files to the SciCat source folder,
    e.g., by using :scitacean.transfer.copy.CopyFileTransfer`
    or writing the files there directly from your workflow.

    Attempting to upload files will raise ``NotImplementedError``.

    Examples
    --------
    Given a dataset with ``source_folder="/dataset/source"`` and a file with path
    ``"file1.dat"``, this

    .. code-block:: python

        client = Client.from_token(
            url="...",
            token="...",
            file_transfer=LinkFileTransfer()
        )
        ds = client.get_dataset(pid="...")
        ds = client.download_files(ds, target="/downloads")

    creates the following symlink:

    .. code-block::

        /downloads/file1.dat -> /dataset/source/file1.dat
    """

    def __init__(
        self,
        *,
        source_folder: str | RemotePath | None = None,
    ) -> None:
        """Construct a new Link file transfer.

        Parameters
        ----------
        source_folder:
            Upload files to this folder if set.
            Otherwise, upload to the dataset's source_folder.
            Ignored when downloading files.
        """
        self._source_folder_pattern = (
            RemotePath(source_folder) if source_folder is not None else None
        )

    def source_folder_for(self, dataset: Dataset) -> RemotePath:
        """Return the source folder used for the given dataset."""
        return source_folder_for(dataset, self._source_folder_pattern)

    @contextmanager
    def connect_for_download(
        self, dataset: Dataset, representative_file_path: RemotePath
    ) -> Iterator[LinkDownloadConnection]:
        """Create a connection for downloads, use as a context manager.

        Parameters
        ----------
        dataset:
            The dataset for which to download files.
        representative_file_path:
            A path to a file that can be used to check whether files for this
            dataset are accessible.
            The transfer assumes that, if this path is accessible,
            all files for this dataset are.

        Returns
        -------
        :
            A connection object that can download files.

        Raises
        ------
        FileNotAccessibleError
            If files for the given dataset cannot be accessed
            based on ``representative_file_path``.
        """
        source_folder = self.source_folder_for(dataset)
        if not Path(source_folder.posix).exists():
            raise FileNotAccessibleError(
                "Cannot directly access the source folder",
                remote_path=source_folder,
            )
        if not Path((source_folder / representative_file_path).posix).exists():
            raise FileNotAccessibleError(
                "Cannot directly access the file", remote_path=representative_file_path
            )
        yield LinkDownloadConnection()

    @contextmanager
    def connect_for_upload(
        self, dataset: Dataset, representative_file_path: RemotePath
    ) -> Iterator[LinkUploadConnection]:
        """Create a connection for uploads, use as a context manager.

        Parameters
        ----------
        dataset:
            The connection will be used to upload files of this dataset.
            Used to determine the target folder.
        representative_file_path:
            A path on the remote to check whether files for this
            dataset can be written.
            The transfer assumes that, if it is possible to write to this path,
            it is possible to write to the paths of all files to be uploaded.

        Raises
        ------
        NotImplementedError
            This file transfer does not implement uploading files.
        """
        raise NotImplementedError(
            "`LinkFileTransfer` cannot be used for uploading files. "
            "If you have direct access to the file server, consider either "
            "copying the files into place or writing them directly to the "
            "'remote folder'. See also scitacean.transfer.copy.CopyFileTransfer.",
        )
        # This is needed to make this function a context manager:
        yield LinkUploadConnection(source_folder=self.source_folder)  # type: ignore[unreachable]


__all__ = ["LinkDownloadConnection", "LinkFileTransfer", "LinkUploadConnection"]
