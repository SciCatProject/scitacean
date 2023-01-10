# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)

import importlib.metadata

try:
    __version__ = importlib.metadata.version(__package__ or __name__)
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"

from .client import Client
from .datablock import OrigDatablockProxy
from .dataset import Dataset
from .error import FileUploadError, IntegrityError, ScicatCommError, ScicatLoginError
from .file import File
from .filesystem import RemotePath
from .model import DatasetType
from .pid import PID

__all__ = (
    "Client",
    "Dataset",
    "DatasetType",
    "File",
    "FileUploadError",
    "IntegrityError",
    "OrigDatablockProxy",
    "PID",
    "RemotePath",
    "ScicatCommError",
    "ScicatLoginError",
)
