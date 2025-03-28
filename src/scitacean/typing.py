# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 SciCat Project (https://github.com/SciCatProject/scitacean)

"""Definitions for type checking."""

from contextlib import AbstractContextManager
from pathlib import Path
from typing import Protocol

from .dataset import Dataset
from .file import File
from .filesystem import RemotePath


class DownloadConnection(Protocol):
    """An open connection to the file server for downloads."""

    def download_files(self, *, remote: list[RemotePath], local: list[Path]) -> None:
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

    def connect_for_download(
        self, dataset: Dataset, representative_file_path: RemotePath
    ) -> AbstractContextManager[DownloadConnection]:
        """Open a connection to the file server.

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
        RuntimeError
            If files for the given dataset cannot be downloaded
            based on ``representative_file_path``.
        """


class UploadConnection(Protocol):
    """An open connection to the file server for uploads."""

    def upload_files(self, *files: File) -> list[File]:
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

    def source_folder_for(self, dataset: Dataset) -> RemotePath:
        """Files are uploaded to this directory / location.

        This method may derive the source_folder from the given dataset
        or override it entirely and specify its own.

        Parameters
        ----------
        dataset:
            Determine the source folder for this dataset.

        Returns
        -------
        :
            The source folder for ``dataset``.
        """

    def connect_for_upload(
        self, dataset: Dataset, representative_file_path: RemotePath
    ) -> AbstractContextManager[UploadConnection]:
        """Open a connection to the file server.

        Parameters
        ----------
        dataset:
            Dataset whose files will be uploaded.
        representative_file_path:
            A path on the remote to check whether files for this
            dataset can be written.
            The transfer assumes that, if it is possible to write to this path,
            it is possible to write to the paths of all files to be uploaded.

        Returns
        -------
        :
            A connection object that can upload files.

        Raises
        ------
        RuntimeError
            If files for the given dataset cannot be uploaded
            based on ``representative_file_path``.
        """


class FileTransfer(Downloader, Uploader, Protocol):
    """Handler for file down-/uploads."""
