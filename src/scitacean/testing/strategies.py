# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen
from functools import partial
from typing import Optional

from email_validator import validate_email, EmailNotValidError
from scitacean import Dataset, DatasetType, PID
from scitacean._internal.orcid import orcid_checksum
from hypothesis import strategies as st


# email_validator and by extension pydantic is more picky than hypothesis
# so make sure that generated emails actually pass model validation.
def _is_valid_email(email: str) -> bool:
    try:
        validate_email(email, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False


def _email_field_strategy(
    field: Dataset.Field, dataset_type: DatasetType
) -> st.SearchStrategy:
    if field.required(dataset_type):
        return st.emails().filter(_is_valid_email)
    return st.none() | st.emails().filter(_is_valid_email)


def _orcid_field_strategy(
    field: Dataset.Field, dataset_type: DatasetType
) -> st.SearchStrategy:
    def make_orcid(digits: str):
        digits = digits[:-1] + orcid_checksum(digits)
        return "https://orcid.org/" + "-".join(
            digits[i : i + 4] for i in range(0, 16, 4)
        )

    orcid_strategy = st.text(alphabet="0123456789", min_size=16, max_size=16).map(
        make_orcid
    )

    if field.required(dataset_type):
        return orcid_strategy
    return st.none() | orcid_strategy


_SPECIAL_FIELDS = {
    "investigator": _email_field_strategy,
    "contact_email": _email_field_strategy,
    "owner_email": _email_field_strategy,
    "orcid_of_owner": _orcid_field_strategy,
}


def _field_strategy(
    field: Dataset.Field, dataset_type: DatasetType
) -> st.SearchStrategy:
    if (strategy := _SPECIAL_FIELDS.get(field.name)) is not None:
        return strategy(field, dataset_type)

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
        **kwargs,
    )
