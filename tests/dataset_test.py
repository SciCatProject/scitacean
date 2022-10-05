# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen

from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote_plus

from hypothesis import given, settings
import pytest
from pyscicat import model

from scitacean import Dataset
from scitacean.testing import strategies as sst

from .common.files import make_file


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
        "scientificMetadata": {
            "data_type": "event data",
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
def single_derived_dataset(dataset_json):
    return model.DerivedDataset(**dataset_json)


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
def test_can_get_dataset_properties_derived(derived_dataset):
    dset = Dataset.new(model=derived_dataset)
    assert dset.owner == "Nanny Ogg"
    assert dset.used_software == ["Magick"]
    assert dset.data_format is None  # only used for raw datasets
    assert dset.is_published
    assert dset.license == derived_dataset.license


@settings(max_examples=10)
@given(sst.raw_datasets(owner="Nanny Ogg", dataFormat="SpellBook", isPublished=True))
def test_can_get_dataset_properties_raw(raw_dataset):
    dset = Dataset.new(model=raw_dataset)
    assert dset.owner == "Nanny Ogg"
    assert dset.used_software is None  # only used for derived datasets
    assert dset.data_format == "SpellBook"
    assert dset.is_published
    assert dset.license == raw_dataset.license


@settings(max_examples=10)
@given(sst.derived_datasets())
def test_can_set_dataset_properties(derived_dataset):
    dset = Dataset.new(model=derived_dataset)
    dset.owner = "Esmeralda Weatherwax"
    dset.source_folder = "/lancre/coven"
    assert dset.owner == "Esmeralda Weatherwax"
    assert dset.source_folder == "/lancre/coven"


@settings(max_examples=10)
@given(sst.derived_datasets())
def test_cannot_access_some_dataset_properties(derived_dataset):
    # Some of DataFile's properties are exposed in a read only way.
    dset = Dataset.new(model=derived_dataset)
    with pytest.raises(AttributeError):
        dset.size = 1  # noqa
    with pytest.raises(AttributeError):
        dset.files = [model.DataFile(path="path", size=4)]  # noqa


def test_can_access_scientific_metadata(single_derived_dataset):
    dset = Dataset.new(model=single_derived_dataset)
    assert dset.meta["temperature"] == {"value": "123", "unit": "K"}
    assert dset.meta["data_type"] == "event data"


def test_can_add_more_metadata_in_new(single_derived_dataset):
    dset = Dataset.new(model=single_derived_dataset, meta={"mood": "grumpy"})
    assert dset.meta["temperature"] == {"value": "123", "unit": "K"}
    assert dset.meta["data_type"] == "event data"
    assert dset.meta["mood"] == "grumpy"


def test_only_explicit_metadata_in_new(single_derived_dataset):
    single_derived_dataset.scientificMetadata = None
    dset = Dataset.new(model=single_derived_dataset, meta={"mood": "grumpy"})
    assert "temperature" not in dset.meta
    assert "data_type" not in dset.meta
    assert dset.meta["mood"] == "grumpy"


@settings(max_examples=10)
@given(sst.derived_datasets())
def test_new_dataset_has_no_files(derived_dataset):
    dset = Dataset.new(model=derived_dataset)
    assert len(dset.files) == 0
    assert dset.size == 0


def test_add_local_file_to_new_dataset(single_derived_dataset, fs):
    f = make_file(fs, "local/folder/data.dat")

    dset = Dataset.new(model=single_derived_dataset)
    dset.add_local_files("local/folder/data.dat")

    assert len(dset.files) == 1
    assert dset.size == f["size"]

    assert dset.files[0].source_folder is None
    assert dset.files[0].remote_access_path is None
    assert dset.files[0].local_path == Path("local/folder/data.dat")
    assert dset.files[0].size == f["size"]

    assert abs(f["creation_time"] - dset.files[0].creation_time) < timedelta(seconds=1)
    t = datetime.fromisoformat(dset.files[0].model.time)
    assert abs(f["creation_time"] - t) < timedelta(seconds=1)


def test_add_multiple_local_files_to_new_dataset(single_derived_dataset, fs):
    f0 = make_file(fs, "common/location1/data.dat")
    f1 = make_file(fs, "common/song.mp3")

    dset = Dataset.new(model=single_derived_dataset)
    dset.add_local_files("common/location1/data.dat", "common/song.mp3")

    assert len(dset.files) == 2
    assert dset.size == f0["size"] + f1["size"]

    assert dset.files[0].source_folder is None
    assert dset.files[0].remote_access_path is None
    assert dset.files[0].local_path == Path("common/location1/data.dat")
    assert dset.files[0].size == f0["size"]
    assert dset.files[0].model.path == "common/location1/data.dat"

    assert dset.files[1].source_folder is None
    assert dset.files[1].remote_access_path is None
    assert dset.files[1].local_path == Path("common/song.mp3")
    assert dset.files[1].size == f1["size"]
    assert dset.files[1].model.path == "common/song.mp3"


def test_add_multiple_local_files_to_new_dataset_with_base_path(
    single_derived_dataset, fs
):
    f0 = make_file(fs, "common/location1/data.dat")
    f1 = make_file(fs, "common/song.mp3")

    dset = Dataset.new(model=single_derived_dataset)
    dset.add_local_files(
        "common/location1/data.dat", "common/song.mp3", base_path="common"
    )

    assert len(dset.files) == 2
    assert dset.size == f0["size"] + f1["size"]

    assert dset.files[0].source_folder is None
    assert dset.files[0].remote_access_path is None
    assert dset.files[0].local_path == Path("common/location1/data.dat")
    assert dset.files[0].size == f0["size"]
    assert dset.files[0].model.path == "location1/data.dat"

    assert dset.files[1].source_folder is None
    assert dset.files[1].remote_access_path is None
    assert dset.files[1].local_path == Path("common/song.mp3")
    assert dset.files[1].size == f1["size"]
    assert dset.files[1].model.path == "song.mp3"


def test_dataset_from_scicat(client, mock_request, dataset_json):
    dset = Dataset.from_scicat(client, dataset_json["pid"])

    assert dset.source_folder == "/hex/source123"
    assert dset.creation_time == "2011-08-24T12:34:56Z"
    assert dset.access_groups == ["group1", "2nd_group"]
    assert dset.meta["temperature"] == {"value": "123", "unit": "K"}
    assert dset.meta["data_type"] == "event data"

    assert dset.files[0].source_folder == "/hex/source123"
    assert dset.files[0].remote_access_path == "/hex/source123/file1.nxs"
    assert dset.files[0].local_path is None
    assert dset.files[1].source_folder == "/hex/source123"
    assert dset.files[1].remote_access_path == "/hex/source123/sub/file2.nxs"
    assert dset.files[1].local_path is None


@settings(max_examples=10)
@given(sst.derived_datasets())
def test_make_scicat_models_creates_correct_dataset(derived_dataset):
    derived_dataset.pid = "some-pid"
    # The default arg of isPublished messes with model creation in Dataset
    derived_dataset.isPublished = False
    dset = Dataset.new(model=derived_dataset)
    mod = dset.make_scicat_models().dataset
    assert mod == derived_dataset


@settings(max_examples=10)
@given(sst.derived_datasets())
def test_make_scicat_models_datablock_without_files(derived_dataset):
    derived_dataset.pid = "some-pid"
    dset = Dataset.new(model=derived_dataset)
    mod = dset.make_scicat_models().datablock
    assert mod.id is None
    assert mod.size == 0
    assert len(mod.dataFileList) == 0
    assert mod.datasetId == dset.pid


def test_make_scicat_models_datablock_with_files(single_derived_dataset, fs):
    f0 = make_file(fs, "base/folder/events.nxs")
    f1 = make_file(fs, "base/folder/log/wtf.log")

    dset = Dataset.new(model=single_derived_dataset)
    dset.add_local_files(
        "base/folder/events.nxs", "base/folder/log/wtf.log", base_path="base/folder"
    )

    mod = dset.make_scicat_models().datablock

    assert mod.id is None
    assert mod.size == f0["size"] + f1["size"]
    assert len(mod.dataFileList) == 2
    assert mod.datasetId == dset.pid

    assert mod.dataFileList[0].path == "events.nxs"
    assert mod.dataFileList[0].size == f0["size"]
    assert mod.dataFileList[1].path == "log/wtf.log"
    assert mod.dataFileList[1].size == f1["size"]


@settings(max_examples=10)
@given(sst.derived_datasets(pid=None))
def test_make_scicat_models_requires_pid(derived_dataset):
    dset = Dataset.new(model=derived_dataset)
    with pytest.raises(ValueError):
        _ = dset.make_scicat_models()


# inputDatasets is only allowed in derived datasets
@settings(max_examples=10)
@given(sst.derived_datasets(pid="0987-poi", inputDatasets=["abcd-1234"]))
def test_make_derived_scicat_models_fails_with_raw_dataset_type(derived_dataset):
    dset = Dataset.new(model=derived_dataset)
    dset.dataset_type = model.DatasetType.raw
    with pytest.raises(TypeError):
        _ = dset.make_scicat_models()


# sampleId is only allowed in raw datasets
@settings(max_examples=10)
@given(sst.raw_datasets(pid="abcd-1234", sampleId="sample-xyz"))
def test_make_raw_scicat_models_fails_with_derived_dataset_type(raw_dataset):
    dset = Dataset.new(model=raw_dataset)
    dset.dataset_type = model.DatasetType.derived
    with pytest.raises(TypeError):
        _ = dset.make_scicat_models()
