# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen

from pathlib import Path
from typing import ContextManager, Protocol, Union

from .pid import PID


class DownloadConnection(Protocol):
    """An open connection to the file server for downloads."""

    def download_file(self, *, remote: Union[str, Path], local: Union[str, Path]):
        """Download a file from the file server.

        Parameters
        ----------
        remote:
            The full path to the file on the server.
        local:
            Desired path of the file on the local filesystem.
        """


class Downloader(Protocol):
    """Handler for file downloads."""

    def connect_for_download(self) -> ContextManager[DownloadConnection]:
        """Open a connection to the file server.

        Returns
        -------
        :
            A connection object that can download files.
        """


class UploadConnection(Protocol):
    """An open connection to the file server for uploads."""

    source_dir: str
    """Files are uploaded to this directory / location."""

    def upload_file(self, *, remote: Union[str, Path], local: Union[str, Path]) -> str:
        """Upload a file to the file server.

        Parameters
        ----------
        remote:
            The file needs to be uploaded to ``source_dir/remote``.
        local:
            Path of the file on the local filesystem.

        Returns
        -------
        :
            The full remote path ``source_dir/remote``.
        """

    def revert_upload(self, *, remote: Union[str, Path], local: Union[str, Path] = ""):
        """Delete a file uploaded by upload_file.

        Only files uploaded by the same connection object may be handled.

        Parameters
        ----------
        remote:
            The file needs to be uploaded to ``source_dir/remote``.
        local:
            Path of the file on the local filesystem.
        """


class Uploader(Protocol):
    """Handler for file uploads."""

    def connect_for_upload(self, dataset_id: PID) -> ContextManager[UploadConnection]:
        """Open a connection to the file server.

        Parameters
        ----------
        dataset_id:
            ID of the dataset whose file will be uploaded.

        Returns
        -------
        :
            A connection object that can upload files.
        """


class FileTransfer(Downloader, Uploader):
    """Handler for file down-/uploads."""
