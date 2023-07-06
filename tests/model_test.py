# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
import dataclasses
from typing import Type, TypeVar

import pytest
from dateutil.parser import parse as parse_date
from hypothesis import given, settings
from hypothesis import strategies as st

from scitacean import PID, DatasetType, model
from scitacean.model import UploadDerivedDataset, UploadRawDataset

T = TypeVar("T")


def build_user_model_for_upload(cls: Type[T]) -> st.SearchStrategy[T]:
    private_fields = {
        field.name: st.none()
        for field in dataclasses.fields(cls)
        if field.name.startswith("_")
    }
    return st.builds(cls, **private_fields)


@settings(max_examples=10)
@given(data=st.data())
@pytest.mark.parametrize(
    "model_types",
    (
        (model.Attachment, model.UploadAttachment),
        (model.Technique, model.UploadTechnique),
        (model.Relationship, model.UploadRelationship),
    ),
)
# Cannot test (model.Sample, model.UploadSample) because hypothesis
# cannot handle fields with type Any.
def test_can_make_upload_model(model_types, data):
    user_model_type, upload_model_type = model_types
    user_model = data.draw(build_user_model_for_upload(user_model_type))
    upload_model = user_model.make_upload_model()
    assert isinstance(upload_model, upload_model_type)


@settings(max_examples=10)
@given(build_user_model_for_upload(model.Attachment))
def test_upload_attachment_fields(attachment):
    upload_attachment = attachment.make_upload_model()
    assert upload_attachment.caption == attachment.caption
    assert upload_attachment.accessGroups == attachment.access_groups
    assert upload_attachment.thumbnail == attachment.thumbnail


@settings(max_examples=10)
@given(st.builds(model.Attachment))
def test_upload_model_rejects_non_upload_fields(attachment):
    attachment._created_by = "the-creator"
    with pytest.raises(ValueError):
        attachment.make_upload_model()


@settings(max_examples=10)
@given(data=st.data())
@pytest.mark.parametrize(
    "model_types",
    (
        (model.Attachment, model.DownloadAttachment),
        (model.Lifecycle, model.DownloadLifecycle),
        (model.Technique, model.DownloadTechnique),
        (model.History, model.DownloadHistory),
        (model.Instrument, model.DownloadInstrument),
        (model.Relationship, model.DownloadRelationship),
    ),
)
def test_can_make_from_download_model(model_types, data):
    user_model_type, download_model_type = model_types
    download_model = data.draw(st.builds(download_model_type))
    # doesn't raise
    user_model_type.from_download_model(download_model)


@settings(max_examples=10)
@given(st.builds(model.DownloadAttachment))
def test_download_attachment_fields(download_attachment):
    attachment = model.Attachment.from_download_model(download_attachment)
    assert attachment.caption == download_attachment.caption
    assert attachment.dataset_id == download_attachment.datasetId
    assert attachment.thumbnail == download_attachment.thumbnail


def test_derived_dataset_default_values(
    real_client, require_scicat_backend, scicat_access
):
    dset = UploadDerivedDataset(
        accessGroups=["access1"],
        contactEmail="contact@email.com",
        creationTime=parse_date("2000-01-01T01:01:01.000Z"),
        inputDatasets=[PID(prefix="PID.prefix.a0b1", pid="abcd")],
        investigator="inv@esti.gator",
        numberOfFilesArchived=0,
        owner=scicat_access.user.username,
        ownerGroup=scicat_access.user.group,
        sourceFolder="/source/folder",
        usedSoftware=["software1"],
        type=DatasetType.DERIVED,
    )
    pid = real_client.scicat.create_dataset_model(dset).pid
    finalized = real_client.scicat.get_dataset_model(pid)

    # Inputs
    assert finalized.accessGroups == ["access1"]
    assert finalized.contactEmail == "contact@email.com"
    assert finalized.creationTime == parse_date("2000-01-01T01:01:01.000Z")
    assert finalized.inputDatasets == [PID(prefix="PID.prefix.a0b1", pid="abcd")]
    assert finalized.investigator == "inv@esti.gator"
    assert finalized.owner == scicat_access.user.username
    assert finalized.ownerGroup == scicat_access.user.group
    assert finalized.sourceFolder == "/source/folder"
    assert finalized.usedSoftware == ["software1"]

    # Default values
    assert finalized.createdAt  # some non-empty str
    assert finalized.createdBy  # some non-empty str
    assert finalized.classification  # some non-empty str
    assert finalized.datasetName  # some non-empty str
    assert finalized.history is None
    assert finalized.isPublished is False
    assert finalized.keywords == []
    assert finalized.numberOfFiles == 0
    assert finalized.numberOfFilesArchived == 0
    assert finalized.packedSize == 0
    assert finalized.pid  # some non-empty str
    assert finalized.scientificMetadata == {}
    assert finalized.sharedWith == []
    assert finalized.size == 0
    assert finalized.techniques == []
    assert finalized.updatedAt  # some non-empty str

    # Left empty
    assert finalized.description is None is None
    assert finalized.jobParameters is None
    assert finalized.jobLogData is None
    assert finalized.license is None
    assert finalized.orcidOfOwner is None
    assert finalized.ownerEmail is None
    assert finalized.sourceFolderHost is None
    assert finalized.validationStatus is None
    assert finalized.version is None


def test_raw_dataset_default_values(real_client, require_scicat_backend, scicat_access):
    dset = UploadRawDataset(
        accessGroups=["access1"],
        contactEmail="contact@email.com",
        creationTime=parse_date("2000-01-01T01:01:01.000Z"),
        creationLocation="site",
        numberOfFilesArchived=0,
        owner=scicat_access.user.username,
        ownerGroup=scicat_access.user.group,
        principalInvestigator="inv@esti.gator",
        sourceFolder="/source/folder",
        type=DatasetType.RAW,
    )
    pid = real_client.scicat.create_dataset_model(dset).pid
    finalized = real_client.scicat.get_dataset_model(pid)

    # Inputs
    assert finalized.accessGroups == ["access1"]
    assert finalized.contactEmail == "contact@email.com"
    assert finalized.creationLocation == "site"
    assert finalized.creationTime == parse_date("2000-01-01T01:01:01.000Z")
    assert finalized.owner == scicat_access.user.username
    assert finalized.ownerGroup == scicat_access.user.group
    assert finalized.principalInvestigator == "inv@esti.gator"
    assert finalized.sourceFolder == "/source/folder"

    # Default values
    assert finalized.createdAt  # some non-empty str
    assert finalized.createdBy  # some non-empty str
    assert finalized.classification  # some non-empty str
    assert finalized.datasetName  # some non-empty str
    assert finalized.history is None
    assert finalized.isPublished is False
    assert finalized.keywords == []
    assert finalized.numberOfFiles == 0
    assert finalized.numberOfFilesArchived == 0
    assert finalized.packedSize == 0
    assert finalized.pid  # some non-empty str
    assert finalized.scientificMetadata == {}
    assert finalized.sharedWith == []
    assert finalized.size == 0
    assert finalized.techniques == []
    assert finalized.updatedAt  # some non-empty str

    # Left empty
    assert finalized.dataFormat is None
    assert finalized.description is None
    assert finalized.endTime is None
    assert finalized.instrumentId is None
    assert finalized.license is None
    assert finalized.orcidOfOwner is None
    assert finalized.ownerEmail is None
    assert finalized.proposalId is None
    assert finalized.sampleId is None
    assert finalized.sourceFolderHost is None
    assert finalized.validationStatus is None
    assert finalized.version is None
