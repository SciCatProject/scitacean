# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen

from pathlib import Path
from typing import ContextManager, Protocol, Union

from .pid import PID

# TODO docs


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
        """remote is only part, there is common path, returns remote"""
        ...

    def revert_upload(self, *, remote: Union[str, Path], local: Union[str, Path] = ""):
        ...


class Uploader(Protocol):
    """"""

    def connect_for_upload(self, dataset_id: PID) -> ContextManager[UploadConnection]:
        ...


class FileTransfer(Downloader, Uploader):
    """"""
