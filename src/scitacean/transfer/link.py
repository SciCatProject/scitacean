# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)
"""File transfer that creates symlinks."""

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from ..dataset import Dataset
from ..file import File
from ..filesystem import RemotePath
from ..logging import get_logger
from .util import source_folder_for


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
            raise FileNotFoundError(
                f"Unable to link to remote file {remote_path}: File does not exist. "
                "This might mean that your machine does not have direct filesystem "
                "access to the file server. Consider using a different file transfer."
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
    This file transfer does not work on Windows.
    This is due to :class:`RemotePath` not supporting backslashes as
    path separators.
    In practice, this should not be a problem because SciCat file storage
    should never be a Windows server.

    Warning
    -------
    This file transfer cannot upload files.
    Instead, consider copying or moving the files to the SciCat source folder
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
    def connect_for_download(self) -> Iterator[LinkDownloadConnection]:
        """Create a connection for downloads, use as a context manager."""
        yield LinkDownloadConnection()

    @contextmanager
    def connect_for_upload(self, dataset: Dataset) -> Iterator[LinkUploadConnection]:
        """Create a connection for uploads, use as a context manager.

        Parameters
        ----------
        dataset:
            The connection will be used to upload files of this dataset.
            Used to determine the target folder.

        Raises
        ------
        NotImplementedError
            This file transfer does not implement uploading files.
        """
        raise NotImplementedError(
            "`LinkFileTransfer` cannot be used for uploading files. "
            "If you have direct access to the file server, consider either "
            "copying the files into place or writing them directly to the "
            "'remote folder'."
        )


__all__ = ["LinkFileTransfer", "LinkUploadConnection", "LinkDownloadConnection"]
