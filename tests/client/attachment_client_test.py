# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
# mypy: disable-error-code="arg-type"

from copy import deepcopy

import pytest
from dateutil.parser import parse as parse_date

from scitacean import PID, Client, ScicatCommError, Thumbnail
from scitacean.client import ScicatClient
from scitacean.model import (
    Attachment,
    DatasetType,
    UploadAttachment,
    UploadDerivedDataset,
)
from scitacean.testing.backend.seed import (
    INITIAL_ATTACHMENTS,
    INITIAL_DATASETS,
)


@pytest.fixture()
def scicat_client(client: Client) -> ScicatClient:
    return client.scicat


@pytest.fixture()
def derived_dataset(scicat_access):
    return UploadDerivedDataset(
        contactEmail="black.foess@dom.koelle",
        creationTime=parse_date("1995-11-11T11:11:11.000Z"),
        owner="bfoess",
        investigator="b.foess@dom.koelle",
        sourceFolder="/dom/platt",
        type=DatasetType.DERIVED,
        inputDatasets=[],
        usedSoftware=[],
        ownerGroup=scicat_access.user.group,
        accessGroups=["koelle"],
        numberOfFilesArchived=0,
    )


@pytest.fixture()
def attachment(scicat_access):
    return UploadAttachment(
        caption="An attachment",
        thumbnail=Thumbnail(mime="image/png", data=b"9278c78a904jh"),
        ownerGroup=scicat_access.user.group,
        accessGroups=["group1", "2nd_group"],
    )


def compare_attachment_after_upload(uploaded, downloaded):
    for key, expected in uploaded:
        # The database populates a number of fields that are None in uploaded.
        # But we don't want to test those here as we don't want to test the database.
        if expected is not None:
            assert expected == dict(downloaded)[key], f"key = {key}"


def test_create_attachment_for_dataset(scicat_client, attachment, derived_dataset):
    attachment1 = deepcopy(attachment)
    attachment2 = deepcopy(attachment)
    attachment2.caption = "Another attachment"

    dataset_id = scicat_client.create_dataset_model(derived_dataset).pid

    finalized1 = scicat_client.create_attachment_for_dataset(
        attachment1, dataset_id=dataset_id
    )
    attachment1.datasetId = dataset_id
    compare_attachment_after_upload(attachment1, finalized1)

    finalized2 = scicat_client.create_attachment_for_dataset(
        attachment2, dataset_id=dataset_id
    )
    attachment2.datasetId = dataset_id
    compare_attachment_after_upload(attachment2, finalized2)


def test_create_attachment_for_dataset_with_existing_id(
    real_client, attachment, derived_dataset, require_scicat_backend
):
    scicat_client = real_client.scicat

    dataset_id = scicat_client.create_dataset_model(derived_dataset).pid
    attachment.id = "attachment-id"
    scicat_client.create_attachment_for_dataset(attachment, dataset_id=dataset_id)

    with pytest.raises(ScicatCommError):
        scicat_client.create_attachment_for_dataset(attachment, dataset_id=dataset_id)


def test_cannot_create_attachment_for_dataset_for_nonexistent_dataset(
    scicat_client, attachment
):
    with pytest.raises(ScicatCommError):
        scicat_client.create_attachment_for_dataset(
            attachment, dataset_id=PID(pid="nonexistent-id")
        )


def test_create_attachment_for_dataset_for_dataset_populates_ids(
    scicat_client, attachment, derived_dataset
):
    assert attachment.id is None
    assert attachment.datasetId is None
    assert attachment.sampleId is None
    assert attachment.proposalId is None

    dataset_id = scicat_client.create_dataset_model(derived_dataset).pid

    finalized = scicat_client.create_attachment_for_dataset(
        attachment, dataset_id=dataset_id
    )

    assert finalized.id is not None
    assert finalized.datasetId is not None
    assert finalized.sampleId is None
    assert finalized.proposalId is None


def test_get_attachments_for_dataset(scicat_client):
    dset = INITIAL_DATASETS["derived"]
    attachments = scicat_client.get_attachments_for_dataset(dset.pid)
    assert attachments == INITIAL_ATTACHMENTS["derived"]


def test_get_attachments_for_dataset_no_attachments(scicat_client):
    assert INITIAL_ATTACHMENTS.get("raw") is None
    dset = INITIAL_DATASETS["raw"]
    attachments = scicat_client.get_attachments_for_dataset(dset.pid)
    assert attachments == []


@pytest.mark.parametrize("key", ("raw", "derived"))
def test_get_dataset_does_not_initialise_attachments(client, key):
    dset = INITIAL_DATASETS["derived"]
    downloaded = client.get_dataset(dset.pid)
    assert downloaded.attachments is None


@pytest.mark.parametrize("key", ("raw", "derived"))
def test_download_attachments_for_dataset(client, key):
    dset = INITIAL_DATASETS[key]
    downloaded = client.get_dataset(dset.pid)
    with_attachments = client.download_attachments_for(downloaded)
    expected = [
        Attachment.from_download_model(attachment)
        for attachment in INITIAL_ATTACHMENTS.get(key, ())
    ]
    assert with_attachments.attachments == expected


@pytest.mark.parametrize("key", ("raw", "derived"))
def test_get_dataset_with_attachments(client, key):
    dset = INITIAL_DATASETS[key]
    downloaded = client.get_dataset(dset.pid, attachments=True)
    expected = [
        Attachment.from_download_model(attachment)
        for attachment in INITIAL_ATTACHMENTS.get(key, ())
    ]
    assert downloaded.attachments == expected
