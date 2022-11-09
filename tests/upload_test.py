# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen

from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path

from pyscicat.client import ScicatCommError
from pyscicat import model
import pytest
from scitacean import Dataset
from scitacean.testing.client import FakeClient

from .common.files import make_file

# TODO source_folder changed / populated in file after upload


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
        size=0,
        numberOfFiles=0,
        creationTime="2011-08-24T12:34:56Z",
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
def client():
    return FakeClient(file_transfer=None)


@pytest.fixture
def dataset(derived_dataset_model, fs):
    make_file(fs, path="file.nxs")
    make_file(fs, path="the_log_file.log")
    dset = Dataset.new(model=derived_dataset_model)
    dset.add_local_files("file.nxs", "the_log_file.log")
    return dset


class FakeUpload:
    def __init__(self, dataset_id=None):
        self.uploaded = []
        self.reverted = []
        self.dataset_id = dataset_id

    def __call__(self, dataset_id):
        self.dataset_id = dataset_id
        return self

    @property
    def source_dir(self):
        return "/remote/upload"

    def upload_file(self, local, remote):
        self.uploaded.append({"local": local, "remote": remote})

    def revert_upload(self, local, remote):
        item = {"local": local, "remote": remote}
        del self.uploaded[self.uploaded.index(item)]
        self.reverted.append(item)

    @contextmanager
    def connect_for_upload(self, pid):
        yield self


def test_upload_assigns_fixes_fields(client, dataset):
    finalized = dataset.upload_new_dataset_now(client, uploader=FakeUpload())
    expected = deepcopy(dataset)
    expected.pid = finalized.pid
    expected.source_folder = FakeUpload().source_dir
    assert finalized == expected


def test_upload_creates_dataset_and_datablock(client, dataset):
    finalized = dataset.upload_new_dataset_now(client, uploader=FakeUpload())
    assert client.datasets[finalized.pid] == finalized.make_scicat_models().dataset
    assert client.orig_datablocks[finalized.pid] == [
        finalized.make_scicat_models().datablock
    ]


def test_upload_uploads_files_to_source_folder(client, dataset):
    uploader = FakeUpload()
    dataset.upload_new_dataset_now(client, uploader=uploader)
    assert sorted(uploader.uploaded, key=lambda d: d["local"]) == [
        {"local": Path("file.nxs"), "remote": "/remote/upload/file.nxs"},
        {
            "local": Path("the_log_file.log"),
            "remote": "/remote/upload/the_log_file.log",
        },
    ]


def test_upload_does_not_create_dataset_if_file_upload_fails(client, dataset):
    class RaisingUpload(FakeUpload):
        def upload_file(self, *, local, remote):
            raise RuntimeError("Fake upload failure")

        @contextmanager
        def connect_for_upload(self, pid):
            yield self

    with pytest.raises(RuntimeError):
        dataset.upload_new_dataset_now(client, uploader=RaisingUpload())

    assert dataset.pid not in client.datasets
    assert dataset.pid not in client.orig_datablocks


def test_upload_cleans_up_files_if_dataset_ingestion_fails(dataset):
    client = FakeClient(
        disable={"create_dataset_model": ScicatCommError("Ingestion failed")}
    )
    uploader = FakeUpload()
    with pytest.raises(ScicatCommError):
        dataset.upload_new_dataset_now(client, uploader=uploader)

    assert not uploader.uploaded


def test_failed_datablock_upload_does_not_revert(dataset):
    client = FakeClient(
        disable={"create_orig_datablock": ScicatCommError("Ingestion failed")}
    )
    uploader = FakeUpload()
    with pytest.raises(RuntimeError):
        dataset.upload_new_dataset_now(client, uploader=uploader)

    uploaded_dset = next(iter(client.datasets.values()))
    dataset.pid = uploaded_dset.pid
    dataset.source_folder = uploaded_dset.sourceFolder
    assert uploaded_dset == dataset.make_scicat_models().dataset
    assert uploader.uploaded
    assert not uploader.reverted
