# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen

from contextlib import contextmanager

from dateutil.parser import parse as parse_date
import pytest
from scitacean import Dataset, DatasetType, ScicatCommError
from scitacean import model
from scitacean.testing.client import FakeClient
from scitacean.testing.transfer import FakeFileTransfer

from .common.files import make_file

# TODO source_folder changed / populated in file after upload


@pytest.fixture
def ownable():
    return model.Ownable(ownerGroup="uu", accessGroups=["group1", "2nd_group"])


@pytest.fixture
def derived_dataset_model(ownable):
    return model.DerivedDataset(
        owner="PonderStibbons",
        investigator="ridcully@uu.am",
        contactEmail="p.stibbons@uu.am",
        sourceFolder="/hex/source123",
        size=0,
        numberOfFiles=0,
        creationTime=parse_date("2011-08-24T12:34:56Z"),
        datasetName="Data A38",
        inputDatasets=[],
        usedSoftware=["EasyScience"],
        scientificMetadata={
            "data_type": "event data",
            "temperature": {"value": "123", "unit": "K"},
            "weight": {"value": "42", "unit": "mg"},
        },
        type=DatasetType.DERIVED,
        **ownable.dict(),
    )


@pytest.fixture
def client(fs):
    return FakeClient.from_token(
        url="", token="", file_transfer=FakeFileTransfer(fs=fs, files={}, reverted={})
    )


@pytest.fixture
def dataset(derived_dataset_model, fs):
    make_file(fs, path="file.nxs", contents=b"contents of file.nxs")
    make_file(fs, path="the_log_file.log", contents=b"this is a log file")
    dset = Dataset.from_models(
        dataset_model=derived_dataset_model, orig_datablock_models=None
    )
    dset.add_local_files("file.nxs", "the_log_file.log")
    return dset


def test_upload_assigns_fixed_fields(client, dataset):
    finalized = client.upload_new_dataset_now(dataset)
    expected = dataset.replace(_read_only={"pid": finalized.pid})

    with client.file_transfer.connect_for_upload(finalized.pid) as con:
        source_dir = con.source_dir
    expected.source_folder = source_dir
    assert finalized == expected


def test_upload_creates_dataset_and_datablock(client, dataset):
    finalized = client.upload_new_dataset_now(dataset)
    assert client.datasets[finalized.pid] == finalized.make_models().dataset
    assert (
        client.orig_datablocks[finalized.pid] == finalized.make_models().orig_datablocks
    )


def test_upload_uploads_files_to_source_folder(client, dataset):
    finalized = client.upload_new_dataset_now(dataset)

    with client.file_transfer.connect_for_upload(finalized.pid) as con:
        source_dir = con.source_dir
    assert (
        client.file_transfer.files[source_dir + "file.nxs"] == b"contents of file.nxs"
    )
    assert (
        client.file_transfer.files[source_dir + "the_log_file.log"]
        == b"this is a log file"
    )


def test_upload_does_not_create_dataset_if_file_upload_fails(dataset, fs):
    class RaisingUpload(FakeFileTransfer):
        source_dir = "/"

        def upload_file(self, *, local, remote):
            raise RuntimeError("Fake upload failure")

        @contextmanager
        def connect_for_upload(self, pid):
            yield self

    client = FakeClient(file_transfer=RaisingUpload(fs=fs))

    with pytest.raises(RuntimeError, match="Fake upload failure"):
        client.upload_new_dataset_now(dataset)

    assert dataset.pid not in client.datasets
    assert dataset.pid not in client.orig_datablocks


def test_upload_cleans_up_files_if_dataset_ingestion_fails(dataset, fs):
    client = FakeClient(
        disable={"create_dataset_model": ScicatCommError("Ingestion failed")},
        file_transfer=FakeFileTransfer(fs=fs),
    )
    with pytest.raises(ScicatCommError):
        client.upload_new_dataset_now(dataset)

    assert not client.file_transfer.files


def test_failed_datablock_upload_does_not_revert(dataset, fs):
    client = FakeClient(
        disable={"create_orig_datablock": ScicatCommError("Ingestion failed")},
        file_transfer=FakeFileTransfer(fs=fs),
    )
    with pytest.raises(RuntimeError):
        client.upload_new_dataset_now(dataset)

    uploaded_dset = next(iter(client.datasets.values()))
    assert uploaded_dset.owner == "PonderStibbons"
    assert uploaded_dset.datasetName == "Data A38"
    assert uploaded_dset.usedSoftware == ["EasyScience"]

    assert client.file_transfer.files
    assert not client.file_transfer.reverted
