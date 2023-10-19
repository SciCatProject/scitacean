# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)

from contextlib import contextmanager
from typing import cast

import pytest
from dateutil.parser import parse as parse_date

from scitacean import (
    PID,
    Attachment,
    Client,
    Dataset,
    DatasetType,
    File,
    ScicatCommError,
    Thumbnail,
)
from scitacean.testing.client import FakeClient
from scitacean.testing.transfer import FakeFileTransfer

from .common.files import make_file

# TODO source_folder changed / populated in file after upload


def get_file_transfer(client: Client) -> FakeFileTransfer:
    return client.file_transfer  # type: ignore[return-value]


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
def attachments():
    return [
        Attachment(
            caption="Attachment no 1",
            owner_group="uu",
            thumbnail=Thumbnail(mime="png/jpeg", data=b"840109725761"),
        ),
        Attachment(
            caption="Second attachment",
            owner_group="uu",
            thumbnail=Thumbnail(mime=None, data=b"5189762957"),
        ),
    ]


@pytest.fixture
def client(fs, scicat_access):
    return FakeClient.from_credentials(
        url="",
        **scicat_access.user.credentials,
        file_transfer=FakeFileTransfer(fs=fs, files={}, reverted={}),
    )


def test_upload_returns_updated_dataset_no_attachments(client, dataset_with_files):
    finalized = client.upload_new_dataset_now(dataset_with_files)
    expected = client.get_dataset(finalized.pid, attachments=True).replace(
        # The backend may update the dataset after upload
        _read_only={
            "updated_at": finalized.updated_at,
            "updated_by": finalized.updated_by,
        }
    )
    assert finalized == expected


def test_upload_returns_updated_dataset_with_attachments(
    client, dataset_with_files, attachments
):
    dataset_with_files.attachments = attachments
    finalized = client.upload_new_dataset_now(dataset_with_files)
    expected = client.get_dataset(finalized.pid, attachments=True).replace(
        # The backend may update the dataset after upload
        _read_only={
            "updated_at": finalized.updated_at,
            "updated_by": finalized.updated_by,
        }
    )
    assert finalized == expected


def test_upload_without_files_creates_dataset(client, dataset):
    finalized = client.upload_new_dataset_now(dataset)
    expected = client.get_dataset(finalized.pid, attachments=True).replace(
        # The backend may update the dataset after upload
        _read_only={
            "updated_at": finalized.updated_at,
            "updated_by": finalized.updated_by,
        }
    )
    assert finalized == expected
    with pytest.raises(ScicatCommError):
        client.scicat.get_orig_datablocks(finalized.pid)


def test_upload_without_files_does_not_need_file_transfer(dataset):
    client = FakeClient()
    finalized = client.upload_new_dataset_now(dataset)
    pid = cast(PID, finalized.pid)
    expected = client.get_dataset(pid, attachments=True).replace(
        # The backend may update the dataset after upload
        _read_only={
            "updated_at": finalized.updated_at,
            "updated_by": finalized.updated_by,
        }
    )
    assert finalized == expected
    with pytest.raises(ScicatCommError):
        client.scicat.get_orig_datablocks(pid)


def test_upload_without_files_does_not_need_revert_files(dataset):
    client = FakeClient(
        disable={"create_dataset_model": ScicatCommError("Ingestion failed")}
    )
    with pytest.raises(ScicatCommError):
        # Does not raise from attempting to access the file transfer.
        client.upload_new_dataset_now(dataset)


def test_upload_with_only_remote_files_does_not_need_file_transfer(dataset):
    dataset.add_files(
        File.from_remote(
            remote_path="source/file1.h5", size=512, creation_time=dataset.creation_time
        )
    )

    client = FakeClient()
    finalized = client.upload_new_dataset_now(dataset)
    pid = cast(PID, finalized.pid)
    expected = client.get_dataset(pid, attachments=True).replace(
        # The backend may update the dataset after upload
        _read_only={
            "updated_at": finalized.updated_at,
            "updated_by": finalized.updated_by,
        }
    )
    assert finalized == expected


def test_upload_with_both_remote_and_local_files(client, dataset_with_files):
    original_file_names = set(
        dataset_with_files.source_folder / file.remote_path
        for file in dataset_with_files.files
    )
    dataset_with_files.add_files(
        File.from_remote(
            remote_path="file1.h5", size=6123, creation_time="2019-09-09T19:29:39Z"
        )
    )

    finalized = client.upload_new_dataset_now(dataset_with_files)
    expected = client.get_dataset(finalized.pid, attachments=True).replace(
        # The backend may update the dataset after upload
        _read_only={
            "updated_at": finalized.updated_at,
            "updated_by": finalized.updated_by,
        }
    )
    assert finalized == expected
    # Does not include the remote file "file1.h5"
    assert get_file_transfer(client).files.keys() == original_file_names


def test_upload_with_file_with_both_remote_and_local_path(client, dataset_with_files):
    file = File.from_remote(
        remote_path="file1.h5", size=6123, creation_time="2019-09-09T19:29:39Z"
    )
    file = file.downloaded(local_path="/local/file1.h5")
    dataset_with_files.add_files(file)

    # Client w/o file transfer to ensure that the client never attempts to upload.
    client = FakeClient()
    with pytest.raises(ValueError, match="path"):
        client.upload_new_dataset_now(dataset_with_files)


def test_upload_creates_dataset_and_datablock(client, dataset_with_files):
    finalized = client.upload_new_dataset_now(dataset_with_files)
    assert client.datasets[finalized.pid].createdAt == finalized.created_at
    assert client.datasets[finalized.pid].datasetName == finalized.name
    assert client.datasets[finalized.pid].owner == finalized.owner
    assert client.datasets[finalized.pid].size == finalized.size

    assert client.orig_datablocks[finalized.pid][0].createdBy == finalized.created_by
    assert client.orig_datablocks[finalized.pid][0].datasetId == finalized.pid
    assert client.orig_datablocks[finalized.pid][0].size == finalized.size


def test_upload_creates_attachments(client, dataset, attachments):
    dataset.attachments = attachments
    finalized = client.upload_new_dataset_now(dataset)

    uploaded = client.attachments[finalized.pid]
    assert len(uploaded) == len(attachments)
    assert uploaded[0].caption == attachments[0].caption
    assert uploaded[0].ownerGroup == attachments[0].owner_group
    assert uploaded[0].thumbnail == attachments[0].thumbnail
    assert uploaded[1].caption == attachments[1].caption
    assert uploaded[1].ownerGroup == attachments[1].owner_group
    assert uploaded[1].thumbnail == attachments[1].thumbnail


def test_upload_uploads_files_to_source_folder(client, dataset_with_files):
    finalized = client.upload_new_dataset_now(dataset_with_files)
    source_folder = client.file_transfer.source_folder_for(finalized)

    assert (
        get_file_transfer(client).files[source_folder / "file.nxs"]
        == b"contents of file.nxs"
    )
    assert (
        get_file_transfer(client).files[source_folder / "the_log_file.log"]
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
    assert not client.attachments


def test_upload_cleans_up_files_if_dataset_ingestion_fails(dataset_with_files, fs):
    client = FakeClient(
        disable={"create_dataset_model": ScicatCommError("Ingestion failed")},
        file_transfer=FakeFileTransfer(fs=fs),
    )
    with pytest.raises(ScicatCommError):
        client.upload_new_dataset_now(dataset_with_files)

    assert not get_file_transfer(client).files


def test_upload_does_not_create_dataset_if_validation_fails(dataset_with_files, fs):
    client = FakeClient(
        disable={"validate_dataset_model": ValueError("Validation failed")},
        file_transfer=FakeFileTransfer(fs=fs),
    )
    with pytest.raises(ValueError):
        client.upload_new_dataset_now(dataset_with_files)

    assert not client.datasets
    assert not client.orig_datablocks
    assert not client.attachments
    assert not get_file_transfer(client).files


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

    assert get_file_transfer(client).files
    assert not get_file_transfer(client).reverted


def test_upload_does_not_create_attachments_if_dataset_ingestion_fails(
    attachments, dataset
):
    dataset.attachments = attachments
    client = FakeClient(
        disable={"create_dataset_model": ScicatCommError("Ingestion failed")},
        file_transfer=FakeFileTransfer(),
    )
    with pytest.raises(ScicatCommError):
        client.upload_new_dataset_now(dataset)

    assert not client.attachments


def test_upload_does_not_create_attachments_if_datablock_ingestion_fails(
    attachments, dataset_with_files, fs
):
    dataset_with_files.attachments = attachments
    client = FakeClient(
        disable={"create_orig_datablock": ScicatCommError("Ingestion failed")},
        file_transfer=FakeFileTransfer(fs=fs),
    )
    with pytest.raises(RuntimeError):
        client.upload_new_dataset_now(dataset_with_files)

    assert not client.attachments


def test_failed_attachment_upload_does_not_revert(attachments, dataset_with_files, fs):
    dataset_with_files.attachments = attachments
    client = FakeClient(
        disable={"create_attachment_for_dataset": ScicatCommError("Ingestion failed")},
        file_transfer=FakeFileTransfer(fs=fs),
    )
    with pytest.raises(RuntimeError):
        client.upload_new_dataset_now(dataset_with_files)

    uploaded_dset = next(iter(client.datasets.values()))
    assert uploaded_dset.owner == "PonderStibbons"
    assert uploaded_dset.datasetName == "Data A38"
    assert uploaded_dset.usedSoftware == ["EasyScience"]

    (uploaded_dblock,) = next(iter(client.orig_datablocks.values()))
    assert uploaded_dblock.datasetId == uploaded_dset.pid

    assert get_file_transfer(client).files
    assert not get_file_transfer(client).reverted
