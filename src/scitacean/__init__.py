# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen

import importlib.metadata

try:
    __version__ = importlib.metadata.version(__package__ or __name__)
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"

from .client import Client
from .dataset import Dataset
from .error import ScicatCommError, ScicatLoginError
from .file import File
from .pid import PID
from ._dataset_fields import DatasetType

__all__ = (
    "Client",
    "Dataset",
    "DatasetType",
    "File",
    "PID",
    "ScicatCommError",
    "ScicatLoginError",
)
