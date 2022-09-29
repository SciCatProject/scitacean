# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen

from urllib.parse import quote_plus

from hypothesis import given, settings
import pytest

from scitacean import Dataset
from scitacean.testing import strategies as sst


@pytest.fixture
def dataset_json():
    return {
        "pid": "01.432.56789/12345678-abcd-0987-0123456789ab",
        "owner": "PonderStibbons",
        "investigator": "Ridcully",
        "contactEmail": "p.stibbons@uu.am",
        "sourceFolder": "/hex/source123",
        "size": 168456,
        "numberOfFiles": 2,
        "creationTime": "2011-08-24T12:34:56Z",
        "type": "derived",
        "datasetName": "Data A38",
        "ownerGroup": "group_o",
        "accessGroups": ["group1", "2nd_group"],
        "inputDatasets": [],
        "usedSoftware": ["EasyScience"],
        # TODO does not always look like this
        "scientificMetadata": {
            "data_type": {"value": "event data", "unit": ""},
            "reference_calibration_dataset": {
                "value": "f1.432.56789/12345678-abcd-0987-0123456789ab",
                "unit": "",
            },
            "temperature": {"value": "123", "unit": "K"},
            "weight": {"value": "42", "unit": "mg"},
        },
    }


@pytest.fixture
def datablocks_json(dataset_json):
    return [
        {
            "id": "fedcba98-5647-a3b2-a0b1c2d3e4f567",
            "size": 168456,
            "ownerGroup": "group_o",
            "accessGroups": ["group1"],
            "datasetId": dataset_json["pid"],
            "dataFileList": [
                {"path": "file1.nxs", "size": 123456, "time": "2022-02-02T12:34:56Z"},
                {
                    "path": "sub/file2.nxs",
                    "size": 45000,
                    "time": "2022-02-02T12:54:32Z",
                },
            ],
        }
    ]


@pytest.fixture
def mock_request(mock_request, local_url, catamel_token, dataset_json, datablocks_json):
    encoded_pid = quote_plus(dataset_json["pid"])

    # TODO client inserts 2 slashes before 'Dataset':
    #  http://localhost:3000/api/v3//Datasets/...
    mock_request.get(
        f"{local_url}/Datasets/{encoded_pid}?access_token={catamel_token}",
        json=dataset_json,
    )
    mock_request.get(
        f"{local_url}/Datasets/{encoded_pid}/"
        f"origdatablocks?access_token={catamel_token}",
        json=datablocks_json,
    )
    return mock_request


@settings(max_examples=10)
@given(
    sst.derived_datasets(owner="Nanny Ogg", usedSoftware=["Magick"], isPublished=True)
)
def test_can_get_dataset_properties(derived_dataset):
    dset = Dataset.new(derived_dataset)
    assert dset.owner == "Nanny Ogg"
    assert dset.usedSoftware == ["Magick"]
    assert dset.isPublished


@settings(max_examples=10)
@given(sst.derived_datasets())
def test_can_set_dataset_properties(derived_dataset):
    dset = Dataset.new(derived_dataset)
    dset.owner = "Esmeralda Weatherwax"
    dset.sourceFolder = "/lancre/coven"
    assert dset.owner == "Esmeralda Weatherwax"
    assert dset.sourceFolder == "/lancre/coven"


# Setting isPublished because the model has a default of False which
# causes a test failure then derived_dataset.isPublished=None
# TODO this isPublished should probably not be optional or not have a default value
@settings(max_examples=10)
@given(sst.derived_datasets(isPublished=True))
def test_setting_dataset_properties_does_not_affect_other_attributes(derived_dataset):
    expected_fields = dict(derived_dataset)
    del expected_fields["owner"]
    dset = Dataset.new(derived_dataset)

    dset.owner = "Granny"
    fields = dict(dset.model)
    del fields["owner"]

    assert fields == expected_fields


@settings(max_examples=10)
@given(sst.derived_datasets())
def test_cannot_access_some_dataset_properties(derived_dataset):
    dset = Dataset.new(derived_dataset)
    with pytest.raises(AttributeError):
        _ = dset.size
    with pytest.raises(AttributeError):
        dset.size = 1
    with pytest.raises(AttributeError):
        _ = dset.numberOfFiles
    with pytest.raises(AttributeError):
        dset.numberOfFiles = 2


@settings(max_examples=10)
@given(sst.derived_datasets())
def test_meta_behaves_like_dict(derived_dataset):
    dset = Dataset.new(derived_dataset)
    assert dset.model.scientificMetadata is None
    assert dset.meta == {}

    dset.meta["a"] = dict(value=3, unit="m")
    dset.meta["b"] = dict(value=-1.2, unit="s")
    assert dset.meta["a"] == dict(value=3, unit="m")
    assert dset.meta["b"] == dict(value=-1.2, unit="s")
    assert dset.model.scientificMetadata["a"] == dict(value=3, unit="m")
    assert dset.model.scientificMetadata["b"] == dict(value=-1.2, unit="s")

    assert len(dset.meta) == 2
    assert list(dset.meta) == ["a", "b"]
    assert list(dset.meta.keys()) == ["a", "b"]
    assert list(dset.meta.values()) == [
        dict(value=3, unit="m"),
        dict(value=-1.2, unit="s"),
    ]
    assert list(dset.meta.items()) == [
        ("a", dict(value=3, unit="m")),
        ("b", dict(value=-1.2, unit="s")),
    ]

    del dset.meta["a"]
    assert "a" not in dset.meta
    assert "a" not in dset.model.scientificMetadata
    assert dset.meta["b"] == dict(value=-1.2, unit="s")
    assert dset.model.scientificMetadata["b"] == dict(value=-1.2, unit="s")


def test_dataset_from_scicat(client, mock_request, dataset_json):
    dset = Dataset.from_scicat(client, dataset_json["pid"])

    assert dset.sourceFolder == "/hex/source123"
    assert dset.creationTime == "2011-08-24T12:34:56Z"
    assert dset.accessGroups == ["group1", "2nd_group"]
    assert dset.meta["temperature"] == {"value": "123", "unit": "K"}
    assert dset.meta["weight"] == {"value": "42", "unit": "mg"}

    assert dset.files[0].local_path is None
    assert dset.files[1].local_path is None
    assert str(dset.files[0].remote_access_path) == "/hex/source123/file1.nxs"
    assert str(dset.files[1].remote_access_path) == "/hex/source123/sub/file2.nxs"
