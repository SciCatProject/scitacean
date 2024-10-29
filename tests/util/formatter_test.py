# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)

import pytest

from scitacean import PID, Dataset
from scitacean.util.formatter import DatasetPathFormatter


def test_dataset_formatter_uses_dataset_fields() -> None:
    dset = Dataset(type="raw", owner="magrat")
    fmt = "{type} {owner}"
    formatted = DatasetPathFormatter().format(fmt, dset=dset)
    expected = fmt.format(type=dset.type, owner=dset.owner)
    assert formatted == expected


def test_dataset_formatter_can_access_attrs_of_fields() -> None:
    dset = Dataset(type="raw")
    dset._pid = PID.parse("prefix/actual-id")  # type: ignore[assignment]
    formatted = DatasetPathFormatter().format("{pid.pid}", dset=dset)
    assert formatted == "actual-id"


def test_dataset_formatter_supports_special_uid() -> None:
    dset = Dataset(type="raw", owner="magrat")
    fmt = "id: {uid}"

    formatted = DatasetPathFormatter().format(fmt, uid="super-unique")
    expected = "id: super-unique"
    assert formatted == expected

    formatted = DatasetPathFormatter().format(fmt, dset=dset, uid="super-unique")
    expected = "id: super-unique"
    assert formatted == expected


def test_dataset_formatter_supports_dset_and_uid() -> None:
    dset = Dataset(type="raw", owner="ogg")
    fmt = "{uid}({owner})"

    formatted = DatasetPathFormatter().format(fmt, dset=dset, uid="abcd")
    expected = "abcd(ogg)"
    assert formatted == expected


def test_dataset_formatter_escapes_characters() -> None:
    dset = Dataset(type="raw", owner="Harald Blåtand", owner_email="harald@viking.dk")
    formatted = DatasetPathFormatter().format("{owner}-{owner_email}", dset=dset)
    expected = "Harald Bl_xe5tand-harald_viking.dk"
    assert formatted == expected


def test_dataset_formatter_preserves_path_separators() -> None:
    dset = Dataset(type="raw", owner="Nanny Ogg")
    formatted = DatasetPathFormatter().format("{type}/{owner}.data", dset=dset)
    assert formatted == "raw/Nanny Ogg.data"


def test_dataset_formatter_does_not_allow_none() -> None:
    dset = Dataset(type="raw", owner=None)
    with pytest.raises(ValueError, match="format path"):
        DatasetPathFormatter().format("{owner}", dset=dset)
