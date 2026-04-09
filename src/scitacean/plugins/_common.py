# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)

import uuid
import warnings
from importlib.metadata import EntryPoint, entry_points

from ..logging import get_logger
from .file_metadata import FILE_LOADERS, FileLoader

_PLUGIN_HOOK_NAME = "_scitacean_plugin_"


class Plugin:
    def __init__(
        self, file_loaders: dict[str, FileLoader], *, name: str | None = None
    ) -> None:
        self.name = name
        self.file_loaders = file_loaders

    def install(self) -> None:
        name = self.name or f"unknown-{uuid.uuid4()}"
        FILE_LOADERS.update(name, self.file_loaders)


def install_plugins() -> None:
    # TODO what happens when a name is used multiple times?
    # Sort by name to make resolution and overriding deterministic.
    discovered = sorted(
        entry_points(group="scitacean.plugin"), key=lambda entry_point: entry_point.name
    )
    get_logger().debug(
        "Discovered plugins: %s", [entry_point.name for entry_point in discovered]
    )

    # First, load all plugins to check for loading errors, then install them.
    plugins = list(filter(lambda p: p is not None, map(_load_plugin, discovered)))
    for plugin in plugins:
        plugin.install()


def _load_plugin(entry_point: EntryPoint) -> Plugin | None:
    loaded = entry_point.load()
    plugin = getattr(loaded, _PLUGIN_HOOK_NAME, None)
    if plugin is None:
        warnings.warn(
            f"Bad plugin: entry point '{entry_point.name}' does not define a "
            f"symbol `{_PLUGIN_HOOK_NAME}`, skipping",
            stacklevel=2,
        )
        return None
    plugin.name = entry_point.name
    return plugin
