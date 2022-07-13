# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scowl contributors (https://github.com/SciCatProject/scowl)
# @author Jan-Lukas Wynen

from collections.abc import MutableMapping

from pyscicat.model import DerivedDataset


# This wrapper is needed because DerivedDataset.scientificMetadata
# can be None in which case we need to write to the instance of
# DerivedDataset in __setitem__.
class ScientificMetadata(MutableMapping):
    """Dictionary of scientific metadata."""

    def __init__(self, parent: DerivedDataset):
        self._parent = parent

    def _get_dict_or_empty(self) -> dict:
        return self._parent.scientificMetadata or {}

    def __getitem__(self, key: str):
        return self._get_dict_or_empty()[key]

    def __setitem__(self, key: str, value):
        if self._parent.scientificMetadata is None:
            self._parent.scientificMetadata = {key: value}
        else:
            self._parent.scientificMetadata[key] = value

    def __delitem__(self, key: str):
        del self._get_dict_or_empty()[key]

    def __iter__(self):
        return iter(self._get_dict_or_empty())

    def __len__(self):
        return len(self._get_dict_or_empty())

    def __repr__(self):
        return repr(self._get_dict_or_empty())
