# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
from dateutil.parser import parse as parse_datetime
from hypothesis import given, settings
from hypothesis import strategies as st

from scitacean import PID, DatasetType
from scitacean.testing import strategies as sst


@given(sst.datasets())
def test_datasets_makes_valid_dataset(dset):
    _ = dset.make_model()


@settings(max_examples=10)
@given(sst.datasets(dataset_type=DatasetType.RAW))
def test_datasets_can_set_type_to_raw(dset):
    assert dset.type == "raw"


@settings(max_examples=10)
@given(sst.datasets(dataset_type=DatasetType.DERIVED))
def test_datasets_can_set_type_to_derived(dset):
    assert dset.type == "derived"


@settings(max_examples=20)
@given(
    sst.datasets(
        name="my-dataset-name",
        access_groups=["group1", "another-group"],
        source_folder="/the/source/of/truth",
        created_at=parse_datetime("2123-11-29T17:44:56Z"),
        pid=PID(prefix="prefix", pid="some-id"),
        description=None,
    )
)
def test_datasets_can_fix_fields(dset):
    assert dset.name == "my-dataset-name"
    assert dset.access_groups == ["group1", "another-group"]
    assert dset.source_folder == "/the/source/of/truth"
    assert dset.created_at == parse_datetime("2123-11-29T17:44:56Z")
    assert dset.pid == PID(prefix="prefix", pid="some-id")
    assert dset.description is None


@settings(max_examples=20)
@given(
    sst.datasets(
        created_by=st.just("the-creator"),
        owner=st.sampled_from(("owner1", "owner2")),
        name=st.text(min_size=2, max_size=5),
    )
)
def test_datasets_can_set_strategy_for_fields(dset):
    assert dset.created_by == "the-creator"
    assert dset.owner in ("owner1", "owner2")
    assert 2 <= len(dset.name) <= 5
