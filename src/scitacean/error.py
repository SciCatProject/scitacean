# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Exception classes."""

from .filesystem import RemotePath


class FileUploadError(RuntimeError):
    """Raised when file upload fails."""


class IntegrityError(RuntimeError):
    """Raised when a dataset or file is broken."""


class ScicatCommError(RuntimeError):
    """Raised when communication with SciCat fails."""


class ScicatLoginError(RuntimeError):
    """Raised when login to SciCat server fails."""


class FileNotAccessibleError(RuntimeError):
    """Raised when a remote file is inaccessible."""

    def __init__(self, *args: object, remote_path: RemotePath) -> None:
        super().__init__(*args)
        self._remote_path = remote_path

    @property
    def remote_path(self) -> RemotePath:
        """The remote path of the inaccessible file."""
        return self._remote_path
