# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)

from contextlib import contextmanager

import pytest
from dateutil.parser import parse as parse_date

from scitacean import Dataset, DatasetType, ScicatCommError
from scitacean.testing.client import FakeClient
from scitacean.testing.transfer import FakeFileTransfer

from .common.files import make_file

# TODO source_folder changed / populated in file after upload


@pytest.fixture
def dataset():
    return Dataset(
        access_groups=["group1", "2nd_group"],
        investigator="ridcully@uu.am",
        contact_email="p.stibbons@uu.am",
        source_folder="/hex/source123",
        creation_time=parse_date("2011-08-24T12:34:56Z"),
        input_datasets=[],
        name="Data A38",
        owner="PonderStibbons",
        owner_group="uu",
        used_software=["EasyScience"],
        meta={
            "data_type": "event data",
            "temperature": {"value": "123", "unit": "K"},
            "weight": {"value": "42", "unit": "mg"},
        },
        type=DatasetType.DERIVED,
    )


@pytest.fixture
def dataset_with_files(dataset, fs):
    make_file(fs, path="file.nxs", contents=b"contents of file.nxs")
    make_file(fs, path="the_log_file.log", contents=b"this is a log file")
    dataset.add_local_files("file.nxs", "the_log_file.log")
    return dataset


@pytest.fixture
def client(fs, scicat_access):
    return FakeClient.from_credentials(
        url="",
        **scicat_access.user.credentials,
        file_transfer=FakeFileTransfer(fs=fs, files={}, reverted={}),
    )


def test_upload_returns_updated_dataset(client, dataset_with_files):
    finalized = client.upload_new_dataset_now(dataset_with_files)
    expected = client.get_dataset(finalized.pid).replace(
        # The backend may update the dataset after upload
        _read_only={
            "updated_at": finalized.updated_at,
            "updated_by": finalized.updated_by,
        }
    )
    assert finalized == expected


def test_upload_without_files_creates_dataset(client, dataset):
    finalized = client.upload_new_dataset_now(dataset)
    expected = client.get_dataset(finalized.pid).replace(
        # The backend may update the dataset after upload
        _read_only={
            "updated_at": finalized.updated_at,
            "updated_by": finalized.updated_by,
        }
    )
    assert finalized == expected
    with pytest.raises(ScicatCommError):
        client.scicat.get_orig_datablocks(finalized.pid)


def test_upload_creates_dataset_and_datablock(client, dataset_with_files):
    finalized = client.upload_new_dataset_now(dataset_with_files)
    assert client.datasets[finalized.pid].createdAt == finalized.created_at
    assert client.datasets[finalized.pid].datasetName == finalized.name
    assert client.datasets[finalized.pid].owner == finalized.owner
    assert client.datasets[finalized.pid].size == finalized.size

    assert client.orig_datablocks[finalized.pid][0].createdBy == finalized.created_by
    assert client.orig_datablocks[finalized.pid][0].datasetId == finalized.pid
    assert client.orig_datablocks[finalized.pid][0].size == finalized.size


def test_upload_uploads_files_to_source_folder(client, dataset_with_files):
    finalized = client.upload_new_dataset_now(dataset_with_files)
    source_folder = client.file_transfer.source_folder_for(finalized)

    assert (
        client.file_transfer.files[source_folder / "file.nxs"]
        == b"contents of file.nxs"
    )
    assert (
        client.file_transfer.files[source_folder / "the_log_file.log"]
        == b"this is a log file"
    )


def test_upload_does_not_create_dataset_if_file_upload_fails(dataset_with_files, fs):
    class RaisingUpload(FakeFileTransfer):
        source_dir = "/"

        def upload_files(self, *files):
            raise RuntimeError("Fake upload failure")

        @contextmanager
        def connect_for_upload(self, pid):
            yield self

    client = FakeClient(file_transfer=RaisingUpload(fs=fs))

    with pytest.raises(RuntimeError, match="Fake upload failure"):
        client.upload_new_dataset_now(dataset_with_files)

    assert not client.datasets
    assert not client.orig_datablocks


def test_upload_cleans_up_files_if_dataset_ingestion_fails(dataset_with_files, fs):
    client = FakeClient(
        disable={"create_dataset_model": ScicatCommError("Ingestion failed")},
        file_transfer=FakeFileTransfer(fs=fs),
    )
    with pytest.raises(ScicatCommError):
        client.upload_new_dataset_now(dataset_with_files)

    assert not client.file_transfer.files


def test_failed_datablock_upload_does_not_revert(dataset_with_files, fs):
    client = FakeClient(
        disable={"create_orig_datablock": ScicatCommError("Ingestion failed")},
        file_transfer=FakeFileTransfer(fs=fs),
    )
    with pytest.raises(RuntimeError):
        client.upload_new_dataset_now(dataset_with_files)

    uploaded_dset = next(iter(client.datasets.values()))
    assert uploaded_dset.owner == "PonderStibbons"
    assert uploaded_dset.datasetName == "Data A38"
    assert uploaded_dset.usedSoftware == ["EasyScience"]

    assert client.file_transfer.files
    assert not client.file_transfer.reverted
