# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen

from datetime import timedelta
from pathlib import Path

from dateutil.parser import parse as parse_time
from hypothesis import given, settings
import pytest
from scitacean import Dataset, DatasetType, model
from scitacean.testing import strategies as sst

from .common.files import make_file


# TODO remove fixtures?
@pytest.fixture
def ownable():
    return model.Ownable(ownerGroup="uu", accessGroups=["group1", "2nd_group"])


@pytest.fixture
def derived_dataset_model(ownable):
    return model.DerivedDataset(
        pid="01.432.56789/12345678-abcd-0987-0123456789ab",
        owner="PonderStibbons",
        investigator="Ridcully",
        contactEmail="p.stibbons@uu.am",
        sourceFolder="/hex/source123",
        size=168456,
        numberOfFiles=2,
        creationTime=parse_time("2011-08-24T12:34:56Z"),
        datasetName="Data A38",
        inputDatasets=[],
        usedSoftware=["EasyScience"],
        scientificMetadata={
            "data_type": "event data",
            "temperature": {"value": "123", "unit": "K"},
            "weight": {"value": "42", "unit": "mg"},
        },
        **ownable.dict(),
    )


@pytest.fixture
def orig_datablock_model(derived_dataset_model, ownable):
    return model.OrigDatablock(
        id="fedcba98-5647-a3b2-a0b1c2d3e4f567",
        size=168456,
        datasetId=derived_dataset_model.pid,
        dataFileList=[
            model.DataFile(
                path="file1.nxs", size=123456, time=parse_time("2022-02-02T12:34:56Z")
            ),
            model.DataFile(
                path="sub/file2.nxs",
                size=45000,
                time=parse_time("2022-02-02T12:54:32Z"),
            ),
        ],
        **ownable.dict(),
    )


@pytest.mark.parametrize("typ", (DatasetType.RAW, DatasetType.DERIVED))
def test_new_dataset_has_no_files(typ):
    dset = Dataset(type=typ)
    assert len(list(dset.files)) == 0
    assert dset.number_of_files == 0
    assert dset.number_of_files_archived == 0
    assert dset.packed_size == 0
    assert dset.size == 0


@pytest.mark.parametrize("typ", (DatasetType.RAW, DatasetType.DERIVED))
def test_add_local_file_to_new_dataset(typ, fs):
    file_data = make_file(fs, "local/folder/data.dat")

    dset = Dataset(type=typ)
    dset.add_local_files("local/folder/data.dat")

    assert len(list(dset.files)) == 1
    assert dset.number_of_files == 1
    assert dset.number_of_files_archived == 0
    assert dset.packed_size == 0
    assert dset.size == file_data["size"]

    f = next(iter(dset.files))
    assert f.source_folder is None
    assert f.remote_access_path is None
    assert f.local_path == Path("local/folder/data.dat")
    assert f.size == file_data["size"]

    assert abs(file_data["creation_time"] - f.creation_time) < timedelta(seconds=1)
    assert abs(file_data["creation_time"] - f.make_model().time) < timedelta(seconds=1)


@pytest.mark.parametrize("typ", (DatasetType.RAW, DatasetType.DERIVED))
def test_add_multiple_local_files_to_new_dataset(typ, fs):
    file_data0 = make_file(fs, "common/location1/data.dat")
    file_data1 = make_file(fs, "common/song.mp3")

    dset = Dataset(type=typ)
    dset.add_local_files("common/location1/data.dat", "common/song.mp3")

    assert len(list(dset.files)) == 2
    assert dset.number_of_files == 2
    assert dset.number_of_files_archived == 0
    assert dset.packed_size == 0
    assert dset.size == file_data0["size"] + file_data1["size"]

    f0 = [f for f in dset.files if f.local_path.suffix == ".dat"][0]
    assert f0.source_folder is None
    assert f0.remote_access_path is None
    assert f0.local_path == Path("common/location1/data.dat")
    assert f0.size == file_data0["size"]
    assert f0.make_model().path == "common/location1/data.dat"

    f1 = [f for f in dset.files if f.local_path.suffix == ".mp3"][0]
    assert f1.source_folder is None
    assert f1.remote_access_path is None
    assert f1.local_path == Path("common/song.mp3")
    assert f1.size == file_data1["size"]
    assert f1.make_model().path == "common/song.mp3"


@pytest.mark.parametrize("typ", (DatasetType.RAW, DatasetType.DERIVED))
def test_add_multiple_local_files_to_new_dataset_with_base_path(typ, fs):
    file_data0 = make_file(fs, "common/location1/data.dat")
    file_data1 = make_file(fs, "common/song.mp3")

    dset = Dataset(type=typ)
    dset.add_local_files(
        "common/location1/data.dat", "common/song.mp3", base_path="common"
    )

    assert len(list(dset.files)) == 2
    assert dset.number_of_files == 2
    assert dset.number_of_files_archived == 0
    assert dset.packed_size == 0
    assert dset.size == file_data0["size"] + file_data1["size"]

    f0 = [f for f in dset.files if f.local_path.suffix == ".dat"][0]
    assert f0.source_folder is None
    assert f0.remote_access_path is None
    assert f0.local_path == Path("common/location1/data.dat")
    assert f0.size == file_data0["size"]
    assert f0.make_model().path == "location1/data.dat"

    f1 = [f for f in dset.files if f.local_path.suffix == ".mp3"][0]
    assert f1.source_folder is None
    assert f1.remote_access_path is None
    assert f1.local_path == Path("common/song.mp3")
    assert f1.size == file_data1["size"]
    assert f1.make_model().path == "song.mp3"


@settings(max_examples=100)
@given(sst.datasets())
def test_dataset_models_roundtrip(initial):
    models = initial.make_models()
    rebuilt = Dataset.from_models(
        dataset_model=models.dataset, orig_datablock_models=models.orig_datablock_models
    )
    assert initial == rebuilt


# TODO do roundtrip
# @settings(max_examples=10)
# @given(sst.derived_datasets())
# def test_make_scicat_models_creates_correct_dataset(derived_dataset):
#     derived_dataset.pid = "some-pid"
#     # The default arg of isPublished messes with model creation in Dataset
#     derived_dataset.isPublished = False
#     dset = Dataset.new(model=derived_dataset)
#     mod = dset.make_scicat_models().dataset
#     assert mod == derived_dataset
#

# @settings(max_examples=10)
# @given(sst.derived_datasets())
# def test_make_scicat_models_datablock_without_files(derived_dataset):
#     derived_dataset.pid = "some-pid"
#     dset = Dataset.new(model=derived_dataset)
#     mod = dset.make_scicat_models().datablock
#     assert mod.id is None
#     assert mod.size == 0
#     assert len(mod.dataFileList) == 0
#     assert mod.datasetId == "some-pid"
#
#
# def test_make_scicat_models_datablock_with_files(derived_dataset_model, fs):
#     f0 = make_file(fs, "base/folder/events.nxs")
#     f1 = make_file(fs, "base/folder/log/wtf.log")
#
#     dset = Dataset.new(model=derived_dataset_model)
#     dset.add_local_files(
#         "base/folder/events.nxs", "base/folder/log/wtf.log", base_path="base/folder"
#     )
#
#     mod = dset.make_scicat_models().datablock
#
#     assert mod.id is None
#     assert mod.size == f0["size"] + f1["size"]
#     assert len(mod.dataFileList) == 2
#     assert mod.datasetId == str(dset.pid)
#
#     assert mod.dataFileList[0].path == "events.nxs"
#     assert mod.dataFileList[0].size == f0["size"]
#     assert mod.dataFileList[1].path == "log/wtf.log"
#     assert mod.dataFileList[1].size == f1["size"]
#
#
# @settings(max_examples=10)
# @given(sst.derived_datasets(pid=None))
# def test_make_scicat_models_requires_pid(derived_dataset):
#     dset = Dataset.new(model=derived_dataset)
#     with pytest.raises(ValueError):
#         _ = dset.make_scicat_models()
#
#
# # inputDatasets is only allowed in derived datasets
# @settings(max_examples=10)
# @given(sst.derived_datasets(pid="0987-poi", inputDatasets=["abcd-1234"]))
# def test_make_derived_scicat_models_fails_with_raw_dataset_type(derived_dataset):
#     dset = Dataset.new(model=derived_dataset)
#     dset.dataset_type = model.DatasetType.raw
#     with pytest.raises(TypeError):
#         _ = dset.make_scicat_models()
#
#
# # sampleId is only allowed in raw datasets
# @settings(max_examples=10)
# @given(sst.raw_datasets(pid="abcd-1234", sampleId="sample-xyz"))
# def test_make_raw_scicat_models_fails_with_derived_dataset_type(raw_dataset):
#     dset = Dataset.new(model=raw_dataset)
#     dset.dataset_type = model.DatasetType.derived
#     with pytest.raises(TypeError):
#         _ = dset.make_scicat_models()
