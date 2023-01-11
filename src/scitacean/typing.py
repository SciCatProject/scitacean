# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)

from pathlib import Path
from typing import ContextManager, List, Protocol

from .file import File
from .filesystem import RemotePath
from .pid import PID


class DownloadConnection(Protocol):
    """An open connection to the file server for downloads."""

    def download_files(self, *, remote: List[str], local: List[Path]) -> None:
        """Download files from the file server.

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

    # TODO rename to source_folder (or remove?)
    source_dir: RemotePath
    """Files are uploaded to this directory / location."""

    def upload_files(self, *files: File) -> List[File]:
        """Upload files to the file server.

        Parameters
        ----------
        files:
            Specify which files to upload including local and remote paths.

        Returns
        -------
        :
            Updated files with added remote parameters.
            For each returned file, both ``file.is_on_remote`` and
            ``file.is_on_local`` are true.
        """

    def revert_upload(self, *files: File) -> None:
        """Delete files uploaded by upload_file.

        Only files uploaded by the same connection object may be handled.

        Parameters
        ----------
        files:
            Specify which files to delete.
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
