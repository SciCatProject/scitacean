# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)

"""Plugins for Scitacean."""

from ._common import Plugin, install_plugins
from .file_metadata import FileLoader

__all__ = ["FileLoader", "Plugin", "install_plugins"]
