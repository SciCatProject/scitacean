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
    assert dset.input_datasets == []
    assert dset.is_published is False
    assert dset.meta == {}


@pytest.mark.parametrize(
    "field", filter(lambda f: f.read_only, Dataset.fields()), ids=lambda f: f.name
)
def test_cannot_set_read_only_fields(field):
    dset = Dataset(type="raw")
    with pytest.raises(AttributeError):
        setattr(dset, field.name, None)


@pytest.mark.parametrize(
    "field",
    filter(lambda f: not f.read_only and f.name != "type", Dataset.fields()),
    ids=lambda f: f.name,
)
@given(st.data())
@settings(max_examples=10)
def test_can_init_writable_fields(field, data):
    value = data.draw(st.from_type(field.type))
    dset = Dataset(type="raw", **{field.name: value})
    assert getattr(dset, field.name) == value


@pytest.mark.parametrize(
    "field", filter(lambda f: not f.read_only, Dataset.fields()), ids=lambda f: f.name
)
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
