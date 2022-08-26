# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen

from pathlib import Path
from typing import Protocol, Union


class Downloader(Protocol):
    """Download files to the local file system."""

    def get(self, *, remote: Union[str, Path], local: Union[str, Path]):
        ...
