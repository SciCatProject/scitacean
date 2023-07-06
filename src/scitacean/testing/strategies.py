# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
import string
from functools import partial
from typing import Any, Dict, Optional

from email_validator import EmailNotValidError, ValidatedEmail, validate_email
from hypothesis import strategies as st

from .. import PID, Dataset, DatasetType, RemotePath, model
from .._internal.orcid import orcid_checksum


# email_validator and by extension pydantic is more picky than hypothesis
# so make sure that generated emails actually pass model validation.
def _validate_email(email: str) -> Optional[ValidatedEmail]:
    try:
        return validate_email(email, check_deliverability=False)
    except EmailNotValidError:
        return None


def _is_valid_email(validated_email: Optional[ValidatedEmail]) -> bool:
    return validated_email is not None


def emails() -> st.SearchStrategy[str]:
    # pydantic.EmailStr converts the input:
    #  - Converts to lower case.
    #  - Uses the normalized email, i.e., with utf-8 characters,
    #    not ASCII (see Punycode) for internationalized names.
    # So we do the same here to make round trips work.
    return (
        st.emails()
        .map(lambda s: s.lower())
        .map(_validate_email)
        .filter(_is_valid_email)
        .map(lambda m: m.normalized)
    )


def multi_emails() -> st.SearchStrategy[str]:
    return st.lists(
        emails(),
        min_size=1,
        max_size=2,
    ).map(lambda email: ";".join(email))


def _email_field_strategy(field: Dataset.Field) -> st.SearchStrategy[Optional[str]]:
    if field.required:
        return multi_emails()
    return st.none() | multi_emails()


def orcids() -> st.SearchStrategy[str]:
    def make_orcid(digits: str) -> str:
        digits = digits[:-1] + orcid_checksum(digits)
        return "https://orcid.org/" + "-".join(
            digits[i : i + 4] for i in range(0, 16, 4)
        )

    return st.text(alphabet="0123456789", min_size=16, max_size=16).map(make_orcid)


def _orcid_field_strategy(field: Dataset.Field) -> st.SearchStrategy[Optional[str]]:
    if field.required:
        return orcids()
    return st.none() | orcids()


def _scientific_metadata_strategy(
    field: Dataset.Field,
) -> st.SearchStrategy[Dict[str, Any]]:
    return st.dictionaries(
        keys=st.text(),
        values=st.text() | st.dictionaries(keys=st.text(), values=st.text()),
    )


def _job_parameters_strategy(
    field: Dataset.Field,
) -> st.SearchStrategy[Optional[Dict[str, str]]]:
    return st.from_type(Optional[Dict[str, str]])


def _lifecycle_strategy(
    field: Dataset.Field,
) -> st.SearchStrategy[Optional[model.Lifecycle]]:
    # Lifecycle contains fields that have `Any` types which `st.from_type` can't handle.
    return st.sampled_from((None, model.Lifecycle()))


_SPECIAL_FIELDS = {
    "contact_email": _email_field_strategy,
    "history": lambda field: st.none(),
    "job_parameters": _job_parameters_strategy,
    "lifecycle": _lifecycle_strategy,
    "owner_email": _email_field_strategy,
    "orcid_of_owner": _orcid_field_strategy,
    "meta": _scientific_metadata_strategy,
}

st.register_type_strategy(
    RemotePath,
    st.text(
        alphabet=string.ascii_lowercase + string.ascii_uppercase + string.digits + "/."
    ).map(RemotePath),
)

st.register_type_strategy(
    PID,
    st.builds(
        PID,
        prefix=st.text(alphabet=st.characters(blacklist_characters="/")) | st.none(),
        pid=st.text(),
    ),
)


def _field_strategy(field: Dataset.Field) -> st.SearchStrategy[Any]:
    if (strategy := _SPECIAL_FIELDS.get(field.name)) is not None:
        return strategy(field)

    typ = field.type if field.required else Optional[field.type]
    return st.from_type(typ)  # type:ignore[arg-type]


def _make_dataset(*, type: DatasetType, args: dict, read_only: dict) -> Dataset:
    dset = Dataset(type=type, **args)
    for key, val in read_only.items():
        setattr(dset, "_" + key, val)
    return dset


def datasets(
    dataset_type: Optional[DatasetType] = None, for_upload: bool = False, **fixed: Any
) -> st.SearchStrategy[Dataset]:
    if dataset_type is None:
        return st.sampled_from(DatasetType).flatmap(
            partial(datasets, for_upload=for_upload, **fixed)
        )

    def make_fixed_arg(key: str) -> st.SearchStrategy[Any]:
        val = fixed[key]
        return val if isinstance(val, st.SearchStrategy) else st.just(val)

    def make_arg(field: Dataset.Field) -> st.SearchStrategy[Any]:
        if field.name in fixed:
            return make_fixed_arg(field.name)
        return _field_strategy(field)

    def make_args(read_only: bool) -> Dict[str, st.SearchStrategy[Any]]:
        return {
            field.name: make_arg(field)
            for field in Dataset.fields(read_only=read_only, dataset_type=dataset_type)
            if field.name != "type"
        }

    args = st.fixed_dictionaries(
        {
            **make_args(read_only=False),
            "checksum_algorithm": st.sampled_from(("blake2b", "sha256")),
        }
    )
    if not for_upload:
        read_only = st.fixed_dictionaries(make_args(read_only=True))
    else:
        read_only = st.just({})
    return st.builds(
        _make_dataset,
        type=st.just(dataset_type),
        args=args,
        read_only=read_only,
    )
