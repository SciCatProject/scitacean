# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 SciCat Project (https://github.com/SciCatProject/scitacean)
"""File transfer that selects a suitable transfer."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from contextlib import AbstractContextManager, ExitStack, contextmanager
from dataclasses import dataclass

from ..dataset import Dataset
from ..error import FileNotAccessibleError
from ..filesystem import RemotePath
from ..typing import DownloadConnection, FileTransfer, UploadConnection
from ._util import source_folder_for


class SelectFileTransfer:
    """Upload / download files using a suitable transfer.

    This file transfer selects one transfer out of a list of candidates and delegates
    to that transfer for all operations.
    The candidates are tried in the order they are provided and the first one that
    can connect and access a remote file or folder is used.

    Examples
    --------
    This uses a :class:`LinkFileTransfer <scitacean.transfer.link.LinkFileTransfer>`
    if the files are directly accessible on the local system and falls back to an
    :class:`SFTPFileTransfer <scitacean.transfer.sftp.SFTPFileTransfer>` otherwise.

    .. code-block:: python

        from scitacean.transfer.link import LinkFileTransfer
        from scitacean.transfer.select import SelectFileTransfer
        from scitacean.transfer.sftp import SFTPFileTransfer
        from scitacean import Client

        link_transfer = LinkFileTransfer()
        sftp_transfer = SFTPFileTransfer(host="fileserver")
        transfer = SelectFileTransfer([link_transfer, sftp_transfer])
        client = Client.from_token(url="...", token="...", file_transfer=transfer)
    """

    def __init__(
        self,
        children: Iterable[FileTransfer],
        *,
        source_folder: str | RemotePath | None = None,
    ) -> None:
        """Construct a new file transfer that selects from its children.

        Parameters
        ----------
        children:
            Child file transfers.
            For any given dataset upload or download, the children are tried
            in the given order.
        source_folder:
            Upload files to this folder if set.
            Otherwise, upload to the dataset's source_folder.
            Ignored when downloading files.
        """
        self._children = list(children)
        if not self._children:
            raise ValueError("At least one child transfer must be provided.")
        self._source_folder_pattern = (
            RemotePath(source_folder) if source_folder is not None else None
        )

    def source_folder_for(self, dataset: Dataset) -> RemotePath:
        """Return the source folder used for the given dataset."""
        return source_folder_for(dataset, self._source_folder_pattern)

    def connect_for_download(
        self, dataset: Dataset, representative_file_path: RemotePath
    ) -> AbstractContextManager[DownloadConnection]:
        """Select a child transfer and connect it for downloading files.

        Use this method as a context manager!

        Parameters
        ----------
        dataset:
            The connection will be used to download files of this dataset.
        representative_file_path:
            A path on the remote server to check whether files for this
            dataset can be read.
            The transfer assumes that, if it is possible to read from this path,
            it is possible to read from the paths of all files to be downloaded.

        Returns
        -------
        :
            An open **child** connection.
        """
        return self._connect_first_suitable(  # type: ignore[return-value]
            _connect_for_download,
            dataset,
            representative_file_path,
            "download",
        )

    def connect_for_upload(
        self, dataset: Dataset, representative_file_path: RemotePath
    ) -> AbstractContextManager[UploadConnection]:
        """Select a child transfer and connect it for uploading files.

        Use this method as a context manager!

        Parameters
        ----------
        dataset:
            The connection will be used to upload files of this dataset.
        representative_file_path:
            A path on the remote server to check whether files for this
            dataset can be written.

        Returns
        -------
        :
            An open **child** connection.
        """
        return self._connect_first_suitable(  # type: ignore[return-value]
            _connect_for_upload,
            dataset,
            representative_file_path,
            "upload",
        )

    @contextmanager
    def _connect_first_suitable(
        self,
        connect: Callable[
            [FileTransfer, Dataset, RemotePath],
            AbstractContextManager[DownloadConnection]
            | AbstractContextManager[UploadConnection],
        ],
        dataset: Dataset,
        representative_file_path: RemotePath,
        action: str,
    ) -> Iterator[DownloadConnection] | Iterator[UploadConnection]:
        errors = []
        success = False
        with ExitStack() as connection_cleanup:
            for child in self._children:
                connection_manager = connect(child, dataset, representative_file_path)
                connection_cleanup.push(connection_manager)
                try:
                    # Only catch exceptions from __enter__ so that we don't attempt
                    # a different transfer if the actual download / upload fails
                    # but only if connecting fails.
                    connection = connection_manager.__enter__()
                except (RuntimeError, NotImplementedError) as error:
                    errors.append(error)
                    continue
                success = True
                yield connection
        if not success:
            raise FileNotAccessibleError(
                f"Unable to {action} files for dataset: "
                "no suitable file transfer available.",
                *errors,
                remote_path=representative_file_path,
            )


@dataclass
class _CannotHandleDataset:
    error: RuntimeError


def _connect_for_download(
    transfer: FileTransfer, dataset: Dataset, representative_file_path: RemotePath
) -> AbstractContextManager[DownloadConnection]:
    return transfer.connect_for_download(dataset, representative_file_path)


def _connect_for_upload(
    transfer: FileTransfer, dataset: Dataset, representative_file_path: RemotePath
) -> AbstractContextManager[UploadConnection]:
    return transfer.connect_for_upload(dataset, representative_file_path)
