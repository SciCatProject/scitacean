# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)
import dataclasses
from typing import TypeVar

import pytest
from dateutil.parser import parse as parse_date
from hypothesis import given, settings
from hypothesis import strategies as st

from scitacean import PID, Client, DatasetType, RemotePath, model
from scitacean.model import (
    DownloadAttachment,
    DownloadDataset,
    DownloadOrigDatablock,
    UploadDerivedDataset,
    UploadRawDataset,
)
from scitacean.testing.backend import config as backend_config

T = TypeVar("T")


def build_user_model_for_upload(cls: type[T]) -> st.SearchStrategy[T]:
    private_fields = {
        field.name: st.none()
        for field in dataclasses.fields(cls)  # type: ignore[arg-type]
        if field.name.startswith("_")
    }
    return st.builds(cls, **private_fields)


@settings(max_examples=10)
@given(data=st.data())
@pytest.mark.parametrize(
    "model_types",
    [
        (model.Attachment, model.UploadAttachment),
        (model.Technique, model.UploadTechnique),
        (model.Relationship, model.UploadRelationship),
    ],
)
# Cannot test (model.Sample, model.UploadSample) because hypothesis
# cannot handle fields with type Any.
def test_can_make_upload_model(
    model_types: tuple[type[model.BaseUserModel], type[model.BaseModel]],
    data: st.DataObject,
) -> None:
    user_model_type, upload_model_type = model_types
    user_model = data.draw(build_user_model_for_upload(user_model_type))
    upload_model = user_model.make_upload_model()
    assert isinstance(upload_model, upload_model_type)


@settings(max_examples=10)
@given(build_user_model_for_upload(model.Attachment))
def test_upload_attachment_fields(attachment: model.Attachment) -> None:
    upload_attachment = attachment.make_upload_model()
    assert upload_attachment.caption == attachment.caption
    assert upload_attachment.accessGroups == attachment.access_groups
    assert upload_attachment.thumbnail == attachment.thumbnail


@settings(max_examples=10)
@given(st.builds(model.Attachment))
def test_upload_model_rejects_non_upload_fields(attachment: model.Attachment) -> None:
    attachment._created_by = "the-creator"
    with pytest.raises(ValueError, match="field.*upload"):
        attachment.make_upload_model()


@settings(max_examples=10)
@given(data=st.data())
@pytest.mark.parametrize(
    "model_types",
    [
        (model.Attachment, model.DownloadAttachment),
        (model.Lifecycle, model.DownloadLifecycle),
        (model.Technique, model.DownloadTechnique),
        (model.History, model.DownloadHistory),
        (model.Instrument, model.DownloadInstrument),
        (model.Relationship, model.DownloadRelationship),
    ],
)
def test_can_make_from_download_model(
    model_types: tuple[type[model.BaseUserModel], type[model.BaseModel]],
    data: st.DataObject,
) -> None:
    user_model_type, download_model_type = model_types
    download_model = data.draw(st.builds(download_model_type))
    # doesn't raise
    user_model_type.from_download_model(download_model)


@settings(max_examples=10)
@given(st.builds(model.DownloadAttachment))
def test_download_attachment_fields(
    download_attachment: model.DownloadAttachment,
) -> None:
    attachment = model.Attachment.from_download_model(download_attachment)
    assert attachment.caption == download_attachment.caption
    assert attachment.dataset_id == download_attachment.datasetId
    assert attachment.thumbnail == download_attachment.thumbnail


def test_derived_dataset_default_values(
    real_client: Client,
    require_scicat_backend: None,
    scicat_access: backend_config.SciCatAccess,
) -> None:
    dset = UploadDerivedDataset(
        accessGroups=["access1"],
        contactEmail="contact@email.com",
        creationTime=parse_date("2000-01-01T01:01:01.000Z"),
        datasetName="Test derived dataset",
        inputDatasets=[PID(prefix="PID.prefix.a0b1", pid="abcd")],
        investigator="inv@esti.gator",
        numberOfFilesArchived=0,
        owner=scicat_access.user.username,
        ownerGroup=scicat_access.user.group,
        sourceFolder=RemotePath("/source/folder"),
        usedSoftware=["software1"],
        type=DatasetType.DERIVED,
    )
    pid = real_client.scicat.create_dataset_model(dset).pid
    assert pid is not None
    finalized = real_client.scicat.get_dataset_model(pid)

    # Inputs
    assert finalized.accessGroups == ["access1"]
    assert finalized.contactEmail == "contact@email.com"
    assert finalized.creationTime == parse_date("2000-01-01T01:01:01.000Z")
    assert finalized.datasetName == "Test derived dataset"
    assert finalized.inputDatasets == [PID(prefix="PID.prefix.a0b1", pid="abcd")]
    assert finalized.principalInvestigator == "inv@esti.gator"
    assert finalized.owner == scicat_access.user.username
    assert finalized.ownerGroup == scicat_access.user.group
    assert finalized.sourceFolder == "/source/folder"
    assert finalized.usedSoftware == ["software1"]

    # Default values
    assert finalized.createdAt  # some non-empty str
    assert finalized.createdBy  # some non-empty str
    assert finalized.classification  # some non-empty str
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
    assert finalized.version == "v3"

    # Left empty
    assert finalized.description is None is None
    assert finalized.jobParameters is None
    assert finalized.jobLogData is None
    assert finalized.license is None
    assert finalized.orcidOfOwner is None
    assert finalized.ownerEmail is None
    assert finalized.sourceFolderHost is None
    assert finalized.validationStatus is None


def test_raw_dataset_default_values(
    real_client: Client,
    require_scicat_backend: None,
    scicat_access: backend_config.SciCatAccess,
) -> None:
    dset = UploadRawDataset(
        accessGroups=["access1"],
        contactEmail="contact@email.com",
        creationTime=parse_date("2000-01-01T01:01:01.000Z"),
        creationLocation="site",
        datasetName="Test raw dataset",
        inputDatasets=[],
        numberOfFilesArchived=0,
        owner=scicat_access.user.username,
        ownerGroup=scicat_access.user.group,
        principalInvestigator="inv@esti.gator",
        sourceFolder=RemotePath("/source/folder"),
        type=DatasetType.RAW,
        usedSoftware=["software1"],
    )
    pid = real_client.scicat.create_dataset_model(dset).pid
    assert pid is not None
    finalized = real_client.scicat.get_dataset_model(pid)

    # Inputs
    assert finalized.datasetName == "Test raw dataset"
    assert finalized.accessGroups == ["access1"]
    assert finalized.contactEmail == "contact@email.com"
    assert finalized.creationLocation == "site"
    assert finalized.creationTime == parse_date("2000-01-01T01:01:01.000Z")
    assert finalized.inputDatasets == []
    assert finalized.owner == scicat_access.user.username
    assert finalized.ownerGroup == scicat_access.user.group
    assert finalized.principalInvestigator == "inv@esti.gator"
    assert finalized.sourceFolder == "/source/folder"
    assert finalized.usedSoftware == ["software1"]

    # Default values
    assert finalized.createdAt  # some non-empty str
    assert finalized.createdBy  # some non-empty str
    assert finalized.classification  # some non-empty str
    assert finalized.instrumentIds == []
    assert finalized.isPublished is False
    assert finalized.keywords == []
    assert finalized.numberOfFiles == 0
    assert finalized.numberOfFilesArchived == 0
    assert finalized.packedSize == 0
    assert finalized.pid  # some non-empty str
    assert finalized.proposalIds == []
    assert finalized.sampleIds == []
    assert finalized.scientificMetadata == {}
    assert finalized.sharedWith == []
    assert finalized.size == 0
    assert finalized.techniques == []
    assert finalized.updatedAt  # some non-empty str
    assert finalized.version == "v3"

    # Left empty
    assert finalized.dataFormat is None
    assert finalized.description is None
    assert finalized.endTime is None
    assert finalized.license is None
    assert finalized.orcidOfOwner is None
    assert finalized.ownerEmail is None
    assert finalized.sourceFolderHost is None
    assert finalized.validationStatus is None


def test_default_masked_fields_are_dropped() -> None:
    mod = DownloadOrigDatablock(  # type: ignore[call-arg]
        id="abc",
        _v="123",
        __v="456",
    )
    # Input id dropped but alias 'id' exists and is not initialized.
    assert mod.id is None

    assert not hasattr(mod, "_v")
    assert not hasattr(mod, "__v")


def test_custom_masked_fields_are_dropped() -> None:
    mod = DownloadDataset(  # type: ignore[call-arg]
        id="abc",
        _id="def",
        _v="123",
        __v="456",
    )
    assert not hasattr(mod, "attachments")
    assert not hasattr(mod, "id")
    assert not hasattr(mod, "_id")
    assert not hasattr(mod, "_v")
    assert not hasattr(mod, "__v")


def test_fields_override_masks() -> None:
    # '_id' is masked but the model has a field 'id' with alias '_id'.
    mod = DownloadOrigDatablock(  # type: ignore[call-arg]
        _id="abc",
        id="def",
    )
    assert mod.id == "abc"
    assert not hasattr(mod, "_id")


def test_fields_override_masks_att() -> None:
    # 'id' is masked but the model has a field 'id' without alias
    mod = DownloadAttachment(  # type: ignore[call-arg]
        _id="abc",
        id="def",
    )
    assert mod.id == "def"
    assert not hasattr(mod, "_id")
