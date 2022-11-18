# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen

"""
These tests use Dataset instead of DatasetFields in order to test the
public interface and make sure that Dataset does not break any behavior.
"""

from datetime import datetime, timedelta, timezone

import dateutil.parser
from hypothesis import given, settings, strategies as st
import pytest
from scitacean.model import DerivedDataset, RawDataset
from scitacean import Dataset, DatasetType


def test_init_dataset_with_only_type():
    dset = Dataset(type="raw")
    assert dset.type == DatasetType.RAW


@pytest.mark.parametrize(
    "typ", ("raw", "derived", DatasetType.RAW, DatasetType.DERIVED)
)
def test_init_dataset_accepted_types(typ):
    dset = Dataset(type=typ)
    assert dset.type == typ


def test_init_dataset_raises_for_bad_type():
    with pytest.raises(ValueError):
        Dataset(type="bad-type")  # noqa


def test_init_dataset_needs_type():
    with pytest.raises(TypeError):
        Dataset()  # noqa


def test_init_dataset_sets_creation_time():
    expected = datetime.now(tz=timezone.utc)
    dset = Dataset(type="raw")
    assert abs(dset.creation_time - expected) < timedelta(seconds=30)


def test_init_dataset_can_set_creation_time():
    dt = dateutil.parser.parse("2022-01-10T11:14:52.623Z")
    dset = Dataset(type="derived", creation_time=dt)
    assert dset.creation_time == dt

    dt = dateutil.parser.parse("2022-01-10T11:14:52+02:00")
    dset = Dataset(type="derived", creation_time=dt)
    assert dset.creation_time == dt

    dt = "1994-03-21T22:51:33-01:00"
    dset = Dataset(type="derived", creation_time=dt)
    assert dset.creation_time == dateutil.parser.parse(dt)

    dset = Dataset(type="derived", creation_time="now")
    assert abs(dset.creation_time - datetime.now(tz=timezone.utc)) < timedelta(
        seconds=30
    )


def test_init_dataset_default_values():
    dset = Dataset(type="derived")
    assert dset.history == []
    assert dset.is_published is False
    assert dset.meta == {}


@pytest.mark.parametrize("field", Dataset.fields(read_only=True), ids=lambda f: f.name)
def test_cannot_set_read_only_fields(field):
    dset = Dataset(type="raw")
    with pytest.raises(AttributeError):
        setattr(dset, field.name, None)


@pytest.mark.parametrize(
    "field",
    filter(lambda f: f.name != "type", Dataset.fields(read_only=False)),
    ids=lambda f: f.name,
)
@given(st.data())
@settings(max_examples=10)
def test_can_init_writable_fields(field, data):
    value = data.draw(st.from_type(field.type))
    dset = Dataset(type="raw", **{field.name: value})
    assert getattr(dset, field.name) == value


@pytest.mark.parametrize("field", Dataset.fields(read_only=False), ids=lambda f: f.name)
@given(st.data())
@settings(max_examples=10)
def test_can_set_writable_fields(field, data):
    value = data.draw(st.from_type(field.type))
    dset = Dataset(type="raw")
    setattr(dset, field.name, value)
    assert getattr(dset, field.name) == value


@pytest.mark.parametrize(
    "field",
    filter(lambda f: not f.read_only and f.name != "creation_time", Dataset.fields()),
    ids=lambda f: f.name,
)
def test_can_set_writable_fields_to_none(field):
    dset = Dataset(type="raw")
    setattr(dset, field.name, None)
    assert getattr(dset, field.name) is None


def test_cannot_set_creation_time_to_none():
    dset = Dataset(type="raw")
    with pytest.raises(TypeError):
        dset.creation_time = None


def test_fields_type_filter_derived():
    assert all(field.used_by_derived for field in Dataset.fields(type="derived"))


def test_fields_type_filter_raw():
    assert all(field.used_by_raw for field in Dataset.fields(type="raw"))


def test_fields_read_only_filter_true():
    assert all(field.read_only for field in Dataset.fields(read_only=True))


def test_fields_read_only_filter_false():
    assert all(not field.read_only for field in Dataset.fields(read_only=False))


def test_fields_read_only__and_type_filter():
    assert all(
        not field.read_only and field.used_by_raw
        for field in Dataset.fields(read_only=False, type="raw")
    )


def test_make_raw_model():
    dset = Dataset(
        type="raw",
        contact_email="p.stibbons@uu.am",
        creation_time="2142-04-02T16:44:56",
        owner="Ponder Stibbons;Mustrum Ridcully",
        owner_group="faculty",
        investigator="Ponder Stibbons",
        source_folder="/hex/source62",
        creation_location="ANK/UU",
        shared_with=["librarian", "hicks"],
    )
    expected = RawDataset(
        contactEmail="p.stibbons@uu.am",
        creationTime=dateutil.parser.parse("2142-04-02T16:44:56"),
        owner="Ponder Stibbons;Mustrum Ridcully",
        ownerGroup="faculty",
        principalInvestigator="Ponder Stibbons",
        sourceFolder="/hex/source62",
        type=DatasetType.RAW,
        history=[],
        isPublished=False,
        scientificMetadata={},
        creationLocation="ANK/UU",
        sharedWith=["librarian", "hicks"],
    )
    assert dset.make_dataset_model() == expected


def test_make_derived_model():
    dset = Dataset(
        type="derived",
        contact_email="p.stibbons@uu.am",
        creation_time="2142-04-02T16:44:56",
        owner="Ponder Stibbons;Mustrum Ridcully",
        owner_group="faculty",
        investigator="Ponder Stibbons",
        source_folder="/hex/source62",
        meta={"weight": {"value": 5.23, "unit": "kg"}},
        input_datasets=["623-122"],
        used_software=["scitacean", "magick"],
    )
    expected = DerivedDataset(
        contactEmail="p.stibbons@uu.am",
        creationTime=dateutil.parser.parse("2142-04-02T16:44:56"),
        owner="Ponder Stibbons;Mustrum Ridcully",
        ownerGroup="faculty",
        investigator="Ponder Stibbons",
        sourceFolder="/hex/source62",
        type=DatasetType.DERIVED,
        history=[],
        isPublished=False,
        scientificMetadata={"weight": {"value": 5.23, "unit": "kg"}},
        inputDatasets=["623-122"],
        usedSoftware=["scitacean", "magick"],
    )
    assert dset.make_dataset_model() == expected


@pytest.mark.parametrize(
    "field",
    filter(
        lambda f: not f.used_by_raw, Dataset.fields(type="derived", read_only=False)
    ),
    ids=lambda f: f.name,
)
@given(st.data())
@settings(max_examples=10)
def test_make_raw_model_raises_if_derived_field_set(field, data):
    dset = Dataset(
        type="raw",
        contact_email="p.stibbons@uu.am",
        creation_time="2142-04-02T16:44:56",
        owner="Mustrum Ridcully",
        owner_group="faculty",
        investigator="Ponder Stibbons",
        source_folder="/hex/source62",
    )
    setattr(dset, field.name, data.draw(st.from_type(field.type)))
    with pytest.raises(ValueError):
        dset.make_dataset_model()


@pytest.mark.parametrize(
    "field",
    filter(
        lambda f: not f.used_by_derived, Dataset.fields(type="raw", read_only=False)
    ),
    ids=lambda f: f.name,
)
@given(st.data())
@settings(max_examples=10)
def test_make_derived_model_raises_if_raw_field_set(field, data):
    dset = Dataset(
        type="derived",
        contact_email="p.stibbons@uu.am",
        creation_time="2142-04-02T16:44:56",
        owner="Ponder Stibbons",
        owner_group="faculty",
        investigator="Ponder Stibbons",
        source_folder="/hex/source62",
        input_datasets=["623-122"],
        used_software=["scitacean", "magick"],
    )
    setattr(dset, field.name, data.draw(st.from_type(field.type)))
    with pytest.raises(ValueError):
        dset.make_dataset_model()
