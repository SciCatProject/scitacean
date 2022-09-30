# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen

from pathlib import Path
from typing import ContextManager, Protocol, Union


class DownloadConnection(Protocol):
    """"""

    def download_file(self, *, remote: Union[str, Path], local: Union[str, Path]):
        ...


class Downloader(Protocol):
    """Download files to the local file system."""

    def connect_for_download(self) -> ContextManager[DownloadConnection]:
        ...


class UploadConnection(Protocol):
    """"""

    source_dir: str

    def upload_file(self, *, remote: Union[str, Path], local: Union[str, Path]) -> str:
        """remote is only part, there is common path"""
        ...

    def revert_upload(self, *, remote: Union[str, Path], local: Union[str, Path] = ""):
        ...


class Uploader(Protocol):
    """"""

    def connect_for_upload(self, dataset_id) -> ContextManager[UploadConnection]:
        ...


class FileTransfer(Downloader, Uploader):
    """"""
