# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen
from functools import partial
from typing import Optional

from scitacean import Dataset, DatasetType, PID
from hypothesis import strategies as st


def _field_strategy(
    field: Dataset.Field, dataset_type: DatasetType
) -> st.SearchStrategy:
    return st.from_type(
        field.type if field.required(dataset_type) else Optional[field.type]
    )


def datasets(dataset_type: Optional[DatasetType] = None, **fixed) -> st.SearchStrategy:
    if dataset_type is None:
        return st.sampled_from(DatasetType).flatmap(partial(datasets, **fixed))

    def make_fixed_arg(key):
        val = fixed[key]
        return val if isinstance(val, st.SearchStrategy) else st.just(val)

    def make_arg(field):
        if field.name in fixed:
            return make_fixed_arg(field.name)
        return _field_strategy(field, dataset_type=dataset_type)

    def make_args(read_only):
        return {
            field.name: make_arg(field)
            for field in Dataset.fields(read_only=read_only, dataset_type=dataset_type)
            if field.name != "type"
        }

    kwargs = make_args(read_only=False)
    read_only_arg = st.fixed_dictionaries(make_args(read_only=True))
    return st.builds(
        Dataset,
        type=st.just(dataset_type),
        _read_only=read_only_arg,
        _pid=st.from_type(PID),
        **kwargs
    )
