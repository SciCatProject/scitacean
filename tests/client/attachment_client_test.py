# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 SciCat Project (https://github.com/SciCatProject/scitacean)
# mypy: disable-error-code="arg-type"

from copy import deepcopy
from datetime import datetime

import pytest

from scitacean import PID, Client, RemotePath, ScicatCommError, Thumbnail
from scitacean.client import ScicatClient
from scitacean.model import (
    Attachment,
    AttachmentRelationship,
    DownloadAttachment,
    UploadAttachment,
    UploadDataset,
)
from scitacean.testing.backend import config as backend_config
from scitacean.testing.backend.seed import (
    INITIAL_ATTACHMENTS,
    INITIAL_DATASETS,
)


@pytest.fixture
def scicat_client(client: Client) -> ScicatClient:
    return client.scicat


@pytest.fixture
def derived_dataset(scicat_access: backend_config.SciCatAccess) -> UploadDataset:
    return UploadDataset(
        datasetName="Koelsche Lieder",
        contactEmail="black.foess@dom.koelle",
        creationTime=datetime.fromisoformat("1995-11-11T11:11:11.000Z"),
        owner="bfoess",
        principalInvestigators=["b.foess@dom.koelle"],
        sourceFolder=RemotePath("/dom/platt"),
        type="derived",
        inputDatasets=[],
        usedSoftware=[],
        ownerGroup=scicat_access.user.group,
        accessGroups=["koelle"],
        numberOfFilesArchived=0,
    )


@pytest.fixture
def attachment(scicat_access: backend_config.SciCatAccess) -> UploadAttachment:
    return UploadAttachment(
        caption="An attachment",
        thumbnail=Thumbnail(mime="image/png", data=b"9278c78a904jh"),
        ownerGroup=scicat_access.user.group,
        accessGroups=["group1", "second_group"],
        relationships=[],
    )


def compare_attachment_after_upload(
    uploaded: UploadAttachment, downloaded: DownloadAttachment
) -> None:
    for key, expected in uploaded:
        # The database populates a number of fields that are None in uploaded.
        # But we don't want to test those here as we don't want to test the database.
        if expected is not None:
            assert expected == dict(downloaded)[key], f"key = {key}"


def sorted_attachments(
    attachments: list[DownloadAttachment] | list[Attachment] | None,
) -> list[DownloadAttachment | Attachment]:
    if attachments is None:
        raise ValueError("Missing attachments")
    return sorted(attachments, key=lambda a: str(a.aid))


def test_create_attachment(
    scicat_client: ScicatClient,
    attachment: UploadAttachment,
    derived_dataset: UploadDataset,
) -> None:
    attachment1 = deepcopy(attachment)
    attachment2 = deepcopy(attachment)
    attachment2.caption = "Another attachment"

    dataset_id = scicat_client.create_dataset_model(derived_dataset).pid
    assert dataset_id is not None
    attachment1.relationships = [
        AttachmentRelationship(targetType="dataset", targetId=dataset_id)
    ]
    attachment2.relationships = [
        AttachmentRelationship(targetType="dataset", targetId=dataset_id)
    ]

    finalized1 = scicat_client.create_attachment(attachment1)
    compare_attachment_after_upload(attachment1, finalized1)

    finalized2 = scicat_client.create_attachment(attachment2)
    compare_attachment_after_upload(attachment2, finalized2)


@pytest.mark.skip("https://github.com/SciCatProject/scicat-backend-next/issues/2254")
def test_create_attachment_with_existing_id(
    real_client: Client,
    attachment: UploadAttachment,
    derived_dataset: UploadDataset,
    require_scicat_backend: None,
) -> None:
    scicat_client = real_client.scicat

    dataset_id = scicat_client.create_dataset_model(derived_dataset).pid
    assert dataset_id is not None
    attachment.relationships = [
        AttachmentRelationship(targetType="dataset", targetId=dataset_id)
    ]
    attachment.aid = "attachment-id"
    scicat_client.create_attachment(attachment)

    with pytest.raises(ScicatCommError):
        scicat_client.create_attachment(attachment)


def test_cannot_create_attachment_without_relationships(
    scicat_client: ScicatClient, attachment: UploadAttachment
) -> None:
    with pytest.raises(ScicatCommError):
        scicat_client.create_attachment(attachment)


def test_cannot_create_attachment_for_nonexistent_dataset(
    scicat_client: ScicatClient, attachment: UploadAttachment
) -> None:
    attachment.relationships = [
        AttachmentRelationship(
            targetType="dataset",
            targetId=PID(pid="nonexistent-id"),
        )
    ]
    with pytest.raises(ScicatCommError):
        scicat_client.create_attachment(attachment)


@pytest.mark.parametrize("key", ["raw", "derived"])
def test_get_dataset_does_not_initialise_attachments(client: Client, key: str) -> None:
    dset = INITIAL_DATASETS["derived"]
    assert dset.pid is not None
    downloaded = client.get_dataset(dset.pid)
    assert downloaded.attachments is None


@pytest.mark.parametrize("key", ["raw", "derived"])
def test_get_dataset_with_attachments(client: Client, key: str) -> None:
    dset = INITIAL_DATASETS[key]
    assert dset.pid is not None
    downloaded = client.get_dataset(dset.pid, attachments=True)
    expected = [
        Attachment.from_download_model(attachment)
        for attachment in INITIAL_ATTACHMENTS.get(key, ())
    ]
    assert sorted_attachments(downloaded.attachments) == sorted_attachments(expected)
