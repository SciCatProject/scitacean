# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 SciCat Project (https://github.com/SciCatProject/scitacean)

"""High-level interface for SciCat."""

import importlib.metadata

try:
    __version__ = importlib.metadata.version(__package__ or __name__)
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"

from ._profile import Profile
from .client import Client
from .datablock import OrigDatablock
from .dataset import Dataset
from .error import (
    FileNotAccessibleError,
    FileUploadError,
    IntegrityError,
    ScicatCommError,
    ScicatLoginError,
)
from .file import File
from .filesystem import RemotePath
from .model import Attachment, DatasetType, Sample
from .pid import PID
from .thumbnail import Thumbnail
from .warning import VisibleDeprecationWarning

__all__ = (
    "PID",
    "Attachment",
    "Client",
    "Dataset",
    "DatasetType",
    "File",
    "FileNotAccessibleError",
    "FileUploadError",
    "IntegrityError",
    "OrigDatablock",
    "Profile",
    "RemotePath",
    "Sample",
    "ScicatCommError",
    "ScicatLoginError",
    "Thumbnail",
    "VisibleDeprecationWarning",
)
