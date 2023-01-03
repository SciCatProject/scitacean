# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Handle input data for tests."""
import json
from functools import lru_cache
from pathlib import Path

from scitacean.model import DerivedDataset, OrigDatablock, RawDataset

_BASE_PATH = Path(__file__).resolve().parent


def _process_field(x):
    if isinstance(x, dict) and "$date" in x:
        return x["$date"]
    if isinstance(x, (dict, list)):
        return _process_json(x)
    return x


def _process_json(raw):
    if isinstance(raw, dict):
        processed = {key: _process_field(val) for key, val in raw.items()}
        try:
            processed["pid"] = processed.pop("_id")
        except KeyError:
            pass
    else:
        processed = [_process_field(val) for val in raw]
    return processed


def _load(filename):
    with open(_BASE_PATH / filename, "r") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_datasets():
    return _load("datasets.json")


def as_dataset_model(dataset_json):
    ds = _process_json(dataset_json)
    if ds["type"] == "derived":
        return DerivedDataset(**ds)
    return RawDataset(**ds)


@lru_cache(maxsize=1)
def load_orig_datablocks():
    return _load("orig_datablocks.json")


def as_orig_datablock_model(orig_datablock_json):
    processed = _process_json(orig_datablock_json)
    processed["id"] = processed.pop("pid")
    return OrigDatablock(**processed)
