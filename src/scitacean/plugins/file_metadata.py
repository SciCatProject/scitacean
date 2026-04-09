# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)

"""Plugins for loading file metadata."""

import os
import warnings
from collections.abc import Callable
from pathlib import Path
from typing import TypeAlias

from ..dataset import Dataset
from ..logging import get_logger

FileLoader: TypeAlias = Callable[[Path], Dataset | None]


class _Registry:
    def __init__(self) -> None:
        self._loaders_by_extension: dict[str, list[FileLoader]] = {}

    def update(self, plugin_name: str, loaders: dict[str, FileLoader]) -> None:
        logger = get_logger()

        for extension, loader in loaders.items():
            logger.debug(
                "Registering file metadata loader from plugin '%s' "
                "for extension '%s': %r",
                plugin_name,
                extension,
                getattr(loader, "__qualname__", loader),
            )
            # TODO check for name clashes
            self._loaders_by_extension.setdefault(extension.lower(), []).append(loader)

    def load(self, path: os.PathLike[str] | str) -> Dataset | None:
        p = Path(path)
        extension = p.suffix.lower()
        if not (loaders := self._loaders_by_extension.get(extension)):
            return None

        for loader in loaders:
            try:
                result = loader(p)
                if result is not None:
                    return result
            except Exception as error:
                warnings.warn(
                    f"File metadata loader {loader!r} failed to load file "
                    f"'{p}': {error}",
                    stacklevel=2,
                )

        return None


FILE_LOADERS: _Registry = _Registry()
