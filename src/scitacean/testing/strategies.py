# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
from functools import partial
from typing import Dict, Optional

from email_validator import EmailNotValidError, validate_email
from hypothesis import strategies as st

from scitacean import PID, Dataset, DatasetType
from scitacean._internal.orcid import orcid_checksum


# email_validator and by extension pydantic is more picky than hypothesis
# so make sure that generated emails actually pass model validation.
def _is_valid_email(email: str) -> bool:
    try:
        validate_email(email, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False


def multi_emails():
    # Convert to lowercase because that is what pydantic does.
    return st.lists(
        st.emails().filter(_is_valid_email).map(lambda s: s.lower()), min_size=1
    ).map(lambda email: ";".join(email))


def _email_field_strategy(
    field: Dataset.Field, dataset_type: DatasetType
) -> st.SearchStrategy:
    if field.required(dataset_type):
        return multi_emails()
    return st.none() | multi_emails()


def orcids():
    def make_orcid(digits: str):
        digits = digits[:-1] + orcid_checksum(digits)
        return "https://orcid.org/" + "-".join(
            digits[i : i + 4] for i in range(0, 16, 4)
        )

    return st.text(alphabet="0123456789", min_size=16, max_size=16).map(make_orcid)


def _orcid_field_strategy(
    field: Dataset.Field, dataset_type: DatasetType
) -> st.SearchStrategy:
    if field.required(dataset_type):
        return orcids()
    return st.none() | orcids()


def _scientific_metadata_strategy(
    field: Dataset.Field, dataset_type: DatasetType
) -> st.SearchStrategy:
    assert field.type == Dict  # nosec (testing code -> assert is safe)
    return st.dictionaries(
        keys=st.text(),
        values=st.text() | st.dictionaries(keys=st.text(), values=st.text()),
    )


_SPECIAL_FIELDS = {
    "investigator": _email_field_strategy,
    "contact_email": _email_field_strategy,
    "owner_email": _email_field_strategy,
    "orcid_of_owner": _orcid_field_strategy,
    "meta": _scientific_metadata_strategy,
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
