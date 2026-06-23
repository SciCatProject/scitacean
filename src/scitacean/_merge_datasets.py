# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable
from typing import Any, TypeVar

from .dataset import Dataset

_T = TypeVar("_T")


def _require_unique(a: _T | None, b: _T | None) -> _T | None:
    if a == b:
        return a
    return None


def _merge_list(a: list[_T] | None, b: list[_T] | None) -> list[_T] | None:
    if a is None:
        return b
    if b is None:
        return a

    # Manual loop to preserve order.
    result = list(a)
    for x in b:
        if x not in result:
            result.append(x)
    return result


def _drop_field(_a: _T | None, _b: _T | None) -> _T | None:
    return None


_MERGE_IMPL: defaultdict[str, Callable[[Any, Any], Any]] = defaultdict(
    lambda: _require_unique,
    used_software=_merge_list,
    input_datasets=_merge_list,
    keywords=_merge_list,
    relationships=_merge_list,
    shared_with=_merge_list,
    techniques=_merge_list,
    access_groups=_merge_list,
    # TODO extend for api v4 lists
    # These need special handling and have cross dependencies:
    # contact_email=
    # principal_investigator=
    #     owner=
    #     owner_email=
    #     orcid_of_owner=
    lifecycle=_drop_field,
)


def merge_datasets(datasets: Iterable[Dataset]) -> Dataset:
    """Merge multiple datasets into one."""
    inputs = iter(datasets)
    try:
        first = next(inputs)
    except StopIteration:
        return Dataset(type="raw")
    result = Dataset(
        **{field.name: first[field.name] for field in Dataset.fields(read_only=False)},
        meta=dict(first.meta),
    )

    for dataset in inputs:
        for field in Dataset.fields(read_only=False):
            name = field.name
            result[name] = _MERGE_IMPL[name](result[name], dataset[name])

    return result
