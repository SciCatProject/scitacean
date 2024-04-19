# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Hypothesis strategies for generating datasets.

This module defines a number of
`Hypothesis <https://hypothesis.readthedocs.io/en/latest/>`_ strategies to
generate test inputs.

Note
----
The ``datasets`` strategy can require a lot of time and memory due to the number of
parameters of ``Dataset``.
This can trip up Hypothesis' health checks, so you may need to disable them.
This can be done, e.g., by placing the following in ``conftest.py``:

.. code-block:: python

    import hypothesis

    hypothesis.settings.register_profile(
        "scitacean",
        suppress_health_check=[
            hypothesis.HealthCheck.data_too_large,
            hypothesis.HealthCheck.too_slow,
        ],
    )

Select the 'scitacean' profile during tests using the
``--hypothesis-profile=scitacean`` command line option.
"""

import string
from functools import partial
from typing import Any

from email_validator import EmailNotValidError, ValidatedEmail, validate_email
from hypothesis import strategies as st

from .. import PID, Dataset, DatasetType, RemotePath, model
from .._internal.orcid import orcid_checksum


# email_validator and by extension pydantic is more picky than hypothesis
# so make sure that generated emails actually pass model validation.
def _validate_email(email: str) -> ValidatedEmail | None:
    try:
        return validate_email(email, check_deliverability=False)
    except EmailNotValidError:
        return None


def _is_valid_email(validated_email: ValidatedEmail | None) -> bool:
    return validated_email is not None


def emails() -> st.SearchStrategy[str]:
    """A strategy for generating email addresses as strings.

    This differs from :func:`hypothesis.strategies.emails` in that it

    - all letters are lowercase,
    - uses only normalized email addresses, i.e., with utf-8 characters
      for internationalized names and never ASCII-encoding (see Punycode).

    This is done to match the behavior of ``pydantic.EmailStr`` and to allow for
    roundtrip tests through :class:`scitacean.Client`.

    Returns
    -------
    :
        String of email addresses.

    See Also
    --------
    scitacean.testing.strategies.multi_emails
    """
    return (
        st.emails()
        .map(lambda s: s.lower())
        .map(_validate_email)
        .filter(_is_valid_email)
        .map(lambda m: m.normalized)  # type: ignore[union-attr]
    )


def multi_emails(max_emails: int = 2) -> st.SearchStrategy[str]:
    """A strategy for generating multiple email addresses as strings.

    Parameters
    ----------
    max_emails:
        Maximum number of emails to generate.

    Returns
    -------
    :
        String of one or more, semicolon-separated email addresses.

    See Also
    --------
    scitacean.testing.strategies.emails
    """
    return st.lists(
        emails(),
        min_size=1,
        max_size=max_emails,
    ).map(lambda email: ";".join(email))


def _email_field_strategy(field: Dataset.Field) -> st.SearchStrategy[str | None]:
    if field.required:
        return multi_emails()
    return st.none() | multi_emails()


def orcids() -> st.SearchStrategy[str]:
    """A strategy for generating ORCID ids.

    The generated ids are structurally valid, but do not necessarily exist.

    Returns
    -------
    :
        Strings of ORCID ids.
    """

    def make_orcid(digits: str) -> str:
        digits = digits[:-1] + orcid_checksum(digits)
        return "https://orcid.org/" + "-".join(
            digits[i : i + 4] for i in range(0, 16, 4)
        )

    return st.text(alphabet="0123456789", min_size=16, max_size=16).map(make_orcid)


def _orcid_field_strategy(field: Dataset.Field) -> st.SearchStrategy[str | None]:
    if field.required:
        return orcids()
    return st.none() | orcids()


def _scientific_metadata_strategy(
    field: Dataset.Field,
) -> st.SearchStrategy[dict[str, Any]]:
    return st.dictionaries(
        keys=st.text(),
        values=st.text() | st.dictionaries(keys=st.text(), values=st.text()),
    )


def _job_parameters_strategy(
    field: Dataset.Field,
) -> st.SearchStrategy[dict[str, str] | None]:
    return st.from_type(dict[str, str] | None)  # type: ignore[arg-type]


def _lifecycle_strategy(
    field: Dataset.Field,
) -> st.SearchStrategy[model.Lifecycle | None]:
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

    typ = field.type if field.required else field.type | None
    return st.from_type(typ)  # type:ignore[arg-type]


def _make_dataset(
    *, type: DatasetType, args: dict[str, Any], read_only: dict[str, Any]
) -> Dataset:
    dset = Dataset(type=type, **args)
    for key, val in read_only.items():
        setattr(dset, "_" + key, val)
    return dset


def datasets(
    type: DatasetType | None = None, for_upload: bool = False, **fields: Any
) -> st.SearchStrategy[Dataset]:
    """A strategy for generating datasets.

    This strategy can populate all dataset fields.
    However, there are some limitations:

    - Some complex models may be uninitialized, e.g., ``lifecycle``.
    - Fields of type ``dict`` only have string values, e.g., ``meta`` will only
      be a ``dict[str, str]`` instead of the broader value types allowed by SciCat.
    - The dataset has no files.

    Parameters
    ----------
    type:
        The type of dataset to generate.
        If ``None``, a random dataset type will be chosen.
    for_upload:
        If ``True``, the dataset can be uploaded because only writable fields
        will be set.
        Otherwise, read-only fields may be set as well.
    fields:
        Concrete values or specific search strategies for dataset fields.

    Returns
    -------
    :
        Datasets.

    Examples
    --------
    To draw arbitrary datasets, use

    .. code-block:: python

        from hypothesis import given
        from scitacean.testing import strategies as sst

        @given(ds=sst.datasets())
        def test_dataset(ds):
            # use ds

    Limit to derived datasets that can be uploaded:

    .. code-block:: python

        @given(ds=sst.datasets(type="derived", for_upload=True))
        def test_derived_upload(ds):
            client = ...
            client.upload_new_dataset_now(ds)

    Fields can be fixed to specific values or generated from specific strategies.
    All other fields are generated as normal.

    .. code-block:: python

        @given(ds=sst.datasets(
            owner="librarian",
            owner_group=st.sampled_from(("library", "faculty"))
        ))
        def test_dataset_owner(ds):
            assert ds.owner == "librarian"
            assert ds.owner_group in ("library", "faculty")
            # other tests

    It is also possible to fix read-only fields:

    .. code-block:: python

        @given(ds=sst.datasets(pid=PID.parse("abcd-12")))
        def test_dataset_fixed_pid(ds):
            assert ds.pid.prefix is None
            # other tests
    """
    if type is None:
        return st.sampled_from(DatasetType).flatmap(
            partial(datasets, for_upload=for_upload, **fields)
        )

    def make_fixed_arg(key: str) -> st.SearchStrategy[Any]:
        val = fields[key]
        return val if isinstance(val, st.SearchStrategy) else st.just(val)

    def make_arg(field: Dataset.Field) -> st.SearchStrategy[Any]:
        if field.name in fields:
            return make_fixed_arg(field.name)
        return _field_strategy(field)

    def make_args(read_only: bool) -> dict[str, st.SearchStrategy[Any]]:
        return {
            field.name: make_arg(field)
            for field in Dataset.fields(read_only=read_only, dataset_type=type)
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
        type=st.just(type),
        args=args,
        read_only=read_only,
    )
