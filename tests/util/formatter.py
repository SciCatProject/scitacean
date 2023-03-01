# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)

from scitacean import Dataset
from scitacean.util.formatter import DatasetPathFormatter


def test_dataset_formatter_uses_dataset_fields():
    dset = Dataset(type="raw", owner="magrat")
    fmt = "{type} {owner}"
    formatted = DatasetPathFormatter().format(fmt, dset)
    expected = fmt.format(type=dset.type, owner=dset.owner)
    assert formatted == expected


def test_dataset_formatter_can_access_attrs_of_fields():
    dset = Dataset(type="raw", pid="prefix/actual-id")
    formatted = DatasetPathFormatter().format("{pid.pid}", dset)
    assert formatted == "actual-id"


def test_dataset_formatter_escapes_characters():
    dset = Dataset(type="raw", owner="Harald Blåtand", owner_email="harald@viking.dk")
    formatted = DatasetPathFormatter().format("{owner}-{owner_email}", dset)
    expected = "Harald Bl_xe5tand-harald_viking.dk"
    assert formatted == expected


def test_dataset_formatter_preserves_path_separators():
    dset = Dataset(type="raw", owner="Nanny Ogg")
    formatted = DatasetPathFormatter().format("{type}/{owner}.data", dset)
    assert formatted == "raw/Nanny Ogg.data"
