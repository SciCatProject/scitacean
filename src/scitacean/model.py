##########################################
# This file was automatically generated. #
# Do not modify it directly!             #
##########################################

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Models for communication with SciCat and user facing dataclasses.

The high-level :class:`scitacean.Client` and :class:`scitacean.Dataset` return objects
from the SciCat database in the form of 'user models'.
Those are usually all that is required for working with Scitacean.

At a lower level, those models are converted to or from upload or download models,
respectively, by the corresponding methods of the user models.
These upload and download models represent SciCat's schemas more closely and are used
by the lower-level :class:`scitacean.client.ScicatClient`
and :class:`scitacean.testing.client.FakeClient`.

.. rubric:: User models

Dataclasses exposed to users, primarily through :class:`Dataset`.

.. autosummary::
  :toctree: ../classes
  :template: scitacean-class-template.rst

  Attachment
  DatasetType
  History
  Instrument
  Lifecycle
  Relationship
  Sample
  Technique

.. rubric:: Download models

Pydantic models for the data received from SciCat in downloads.

.. autosummary::
  :toctree: ../classes

  DownloadAttachment
  DownloadDatablock
  DownloadDataFile
  DownloadDataset
  DownloadHistory
  DownloadInstrument
  DownloadLifecycle
  DownloadOrigDatablock
  DownloadRelationship
  DownloadSample
  DownloadTechnique

.. rubric:: Upload models

Pydantic models sent to SciCat in uploads.

.. autosummary::
  :toctree: ../classes

  UploadAttachment
  UploadDatablock
  UploadDataFile
  UploadDerivedDataset
  UploadOrigDatablock
  UploadRawDataset
  UploadRelationship
  UploadSample
  UploadTechnique

.. rubric:: Functions

.. autosummary::
   :toctree: ../functions

   construct
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pydantic
from pydantic import NonNegativeInt

from ._base_model import (
    BaseModel,
    BaseUserModel,
    DatasetType,
    construct,
    validate_datetime,
    validate_emails,
    validate_orcids,
)
from .filesystem import RemotePath
from .pid import PID
from .thumbnail import Thumbnail


# TODO remove extra masks after API v4
class DownloadDataset(
    BaseModel, masked=("history", "proposalId", "sampleId", "instrumentId")
):
    contactEmail: str | None = None
    creationLocation: str | None = None
    creationTime: datetime | None = None
    inputDatasets: list[PID] | None = None
    numberOfFilesArchived: NonNegativeInt | None = None
    owner: str | None = None
    ownerGroup: str | None = None
    principalInvestigator: str | None = None
    sourceFolder: RemotePath | None = None
    type: DatasetType | None = None
    usedSoftware: list[str] | None = None
    accessGroups: list[str] | None = None
    version: str | None = None
    classification: str | None = None
    comment: str | None = None
    createdAt: datetime | None = None
    createdBy: str | None = None
    dataFormat: str | None = None
    dataQualityMetrics: int | None = None
    description: str | None = None
    endTime: datetime | None = None
    instrumentGroup: str | None = None
    instrumentIds: list[str] | None = None
    isPublished: bool | None = None
    jobLogData: str | None = None
    jobParameters: dict[str, Any] | None = None
    keywords: list[str] | None = None
    license: str | None = None
    datasetlifecycle: DownloadLifecycle | None = None
    scientificMetadata: dict[str, Any] | None = None
    datasetName: str | None = None
    numberOfFiles: NonNegativeInt | None = None
    orcidOfOwner: str | None = None
    ownerEmail: str | None = None
    packedSize: NonNegativeInt | None = None
    pid: PID | None = None
    proposalIds: list[str] | None = None
    relationships: list[DownloadRelationship] | None = None
    sampleIds: list[str] | None = None
    sharedWith: list[str] | None = None
    size: NonNegativeInt | None = None
    sourceFolderHost: str | None = None
    startTime: datetime | None = None
    techniques: list[DownloadTechnique] | None = None
    updatedAt: datetime | None = None
    updatedBy: str | None = None
    validationStatus: str | None = None

    @pydantic.field_validator(
        "creationTime", "createdAt", "endTime", "updatedAt", mode="before"
    )
    def _validate_datetime(cls, value: Any) -> Any:
        return validate_datetime(value)

    @pydantic.field_validator("contactEmail", "ownerEmail", mode="before")
    def _validate_emails(cls, value: Any) -> Any:
        return validate_emails(value)

    @pydantic.field_validator("orcidOfOwner", mode="before")
    def _validate_orcids(cls, value: Any) -> Any:
        return validate_orcids(value)

    # TODO remove after API v4
    @pydantic.field_validator("sampleIds", mode="before")
    def _validate_sample_ids(cls, value: Any) -> Any:
        if value == [None]:
            return []
        return value

    @pydantic.field_validator("proposalIds", mode="before")
    def _validate_proposal_ids(cls, value: Any) -> Any:
        if value == [None]:
            return []
        return value

    @pydantic.field_validator("instrumentIds", mode="before")
    def _validate_instrument_ids(cls, value: Any) -> Any:
        if value == [None]:
            return []
        return value


class UploadDerivedDataset(BaseModel):
    contactEmail: str
    creationTime: datetime
    inputDatasets: list[PID]
    investigator: str
    numberOfFilesArchived: NonNegativeInt
    owner: str
    ownerGroup: str
    sourceFolder: RemotePath
    type: DatasetType
    usedSoftware: list[str]
    datasetName: str
    accessGroups: list[str] | None = None
    classification: str | None = None
    comment: str | None = None
    dataQualityMetrics: int | None = None
    description: str | None = None
    instrumentGroup: str | None = None
    isPublished: bool | None = None
    jobLogData: str | None = None
    jobParameters: dict[str, Any] | None = None
    keywords: list[str] | None = None
    license: str | None = None
    scientificMetadata: dict[str, Any] | None = None
    numberOfFiles: NonNegativeInt | None = None
    orcidOfOwner: str | None = None
    ownerEmail: str | None = None
    packedSize: NonNegativeInt | None = None
    proposalId: str | None = None
    relationships: list[UploadRelationship] | None = None
    sharedWith: list[str] | None = None
    size: NonNegativeInt | None = None
    sourceFolderHost: str | None = None
    techniques: list[UploadTechnique] | None = None
    validationStatus: str | None = None

    @pydantic.field_validator("creationTime", mode="before")
    def _validate_datetime(cls, value: Any) -> Any:
        return validate_datetime(value)

    @pydantic.field_validator("contactEmail", "ownerEmail", mode="before")
    def _validate_emails(cls, value: Any) -> Any:
        return validate_emails(value)

    @pydantic.field_validator("orcidOfOwner", mode="before")
    def _validate_orcids(cls, value: Any) -> Any:
        return validate_orcids(value)


class UploadRawDataset(BaseModel):
    contactEmail: str
    creationLocation: str
    creationTime: datetime
    inputDatasets: list[PID]
    numberOfFilesArchived: NonNegativeInt
    owner: str
    ownerGroup: str
    principalInvestigator: str
    sourceFolder: RemotePath
    type: DatasetType
    usedSoftware: list[str]
    datasetName: str
    investigator: str | None = None
    accessGroups: list[str] | None = None
    classification: str | None = None
    comment: str | None = None
    dataFormat: str | None = None
    dataQualityMetrics: int | None = None
    description: str | None = None
    endTime: datetime | None = None
    instrumentGroup: str | None = None
    instrumentId: str | None = None
    isPublished: bool | None = None
    jobLogData: str | None = None
    jobParameters: dict[str, Any] | None = None
    keywords: list[str] | None = None
    license: str | None = None
    scientificMetadata: dict[str, Any] | None = None
    numberOfFiles: NonNegativeInt | None = None
    orcidOfOwner: str | None = None
    ownerEmail: str | None = None
    packedSize: NonNegativeInt | None = None
    proposalId: str | None = None
    relationships: list[UploadRelationship] | None = None
    sampleId: str | None = None
    sharedWith: list[str] | None = None
    size: NonNegativeInt | None = None
    sourceFolderHost: str | None = None
    startTime: datetime | None = None
    techniques: list[UploadTechnique] | None = None
    validationStatus: str | None = None

    @pydantic.model_validator(mode="before")
    @classmethod
    def _set_investigator(cls, data: Any) -> Any:
        # The model currently has both `investigator` and `principalInvestigator`
        # and both are mandatory. Eventually, `investigator` will be removed.
        # So make sure we can construct the model if only one is given.
        if isinstance(data, dict):
            if (inv := data.get("investigator")) is not None:
                data.setdefault("principalInvestigator", inv)
            elif (pi := data.get("principalInvestigator")) is not None:
                data["investigator"] = pi
        return data

    @pydantic.field_validator("creationTime", "endTime", mode="before")
    def _validate_datetime(cls, value: Any) -> Any:
        return validate_datetime(value)

    @pydantic.field_validator("contactEmail", "ownerEmail", mode="before")
    def _validate_emails(cls, value: Any) -> Any:
        return validate_emails(value)

    @pydantic.field_validator("orcidOfOwner", mode="before")
    def _validate_orcids(cls, value: Any) -> Any:
        return validate_orcids(value)


class DownloadAttachment(BaseModel):
    caption: str | None = None
    ownerGroup: str | None = None
    accessGroups: list[str] | None = None
    createdAt: datetime | None = None
    createdBy: str | None = None
    datasetId: PID | None = None
    id: str | None = None
    instrumentGroup: str | None = None
    isPublished: bool | None = None
    proposalId: str | None = None
    sampleId: str | None = None
    thumbnail: Thumbnail | None = None
    updatedAt: datetime | None = None
    updatedBy: str | None = None

    @pydantic.field_validator("createdAt", "updatedAt", mode="before")
    def _validate_datetime(cls, value: Any) -> Any:
        return validate_datetime(value)

    @classmethod
    def user_model_type(cls) -> type[Attachment]:
        return Attachment

    @classmethod
    def upload_model_type(cls) -> type[UploadAttachment]:
        return UploadAttachment


class UploadAttachment(BaseModel):
    caption: str
    ownerGroup: str
    accessGroups: list[str] | None = None
    datasetId: PID | None = None
    id: str | None = None
    instrumentGroup: str | None = None
    proposalId: str | None = None
    sampleId: str | None = None
    thumbnail: Thumbnail | None = None

    @classmethod
    def user_model_type(cls) -> type[Attachment]:
        return Attachment

    @classmethod
    def download_model_type(cls) -> type[DownloadAttachment]:
        return DownloadAttachment


class DownloadOrigDatablock(BaseModel):
    dataFileList: list[DownloadDataFile] | None = None
    size: NonNegativeInt | None = None
    id: str | None = pydantic.Field(alias="_id", default=None)
    accessGroups: list[str] | None = None
    chkAlg: str | None = None
    createdAt: datetime | None = None
    createdBy: str | None = None
    datasetId: PID | None = None
    instrumentGroup: str | None = None
    isPublished: bool | None = None
    ownerGroup: str | None = None
    updatedAt: datetime | None = None
    updatedBy: str | None = None

    @pydantic.field_validator("createdAt", "updatedAt", mode="before")
    def _validate_datetime(cls, value: Any) -> Any:
        return validate_datetime(value)

    @classmethod
    def upload_model_type(cls) -> type[UploadOrigDatablock]:
        return UploadOrigDatablock


class UploadOrigDatablock(BaseModel):
    dataFileList: list[UploadDataFile]
    size: NonNegativeInt
    chkAlg: str | None = None

    @classmethod
    def download_model_type(cls) -> type[DownloadOrigDatablock]:
        return DownloadOrigDatablock


class DownloadDatablock(BaseModel):
    archiveId: str | None = None
    dataFileList: list[DownloadDataFile] | None = None
    packedSize: NonNegativeInt | None = None
    size: NonNegativeInt | None = None
    version: str | None = None
    id: str | None = pydantic.Field(alias="_id", default=None)
    accessGroups: list[str] | None = None
    chkAlg: str | None = None
    createdAt: datetime | None = None
    createdBy: str | None = None
    datasetId: PID | None = None
    instrumentGroup: str | None = None
    isPublished: bool | None = None
    ownerGroup: str | None = None
    updatedAt: datetime | None = None
    updatedBy: str | None = None

    @pydantic.field_validator("createdAt", "updatedAt", mode="before")
    def _validate_datetime(cls, value: Any) -> Any:
        return validate_datetime(value)

    @classmethod
    def upload_model_type(cls) -> type[UploadDatablock]:
        return UploadDatablock


class UploadDatablock(BaseModel):
    archiveId: str
    dataFileList: list[UploadDataFile]
    packedSize: NonNegativeInt
    size: NonNegativeInt
    version: str
    chkAlg: str | None = None

    @classmethod
    def download_model_type(cls) -> type[DownloadDatablock]:
        return DownloadDatablock


class DownloadLifecycle(BaseModel):
    archivable: bool | None = None
    archiveRetentionTime: datetime | None = None
    archiveReturnMessage: dict[str, Any] | None = None
    archiveStatusMessage: str | None = None
    dateOfDiskPurging: datetime | None = None
    dateOfPublishing: datetime | None = None
    exportedTo: str | None = None
    isOnCentralDisk: bool | None = None
    publishable: bool | None = None
    publishedOn: datetime | None = None
    retrievable: bool | None = None
    retrieveIntegrityCheck: bool | None = None
    retrieveReturnMessage: dict[str, Any] | None = None
    retrieveStatusMessage: str | None = None

    @pydantic.field_validator(
        "archiveRetentionTime",
        "dateOfDiskPurging",
        "dateOfPublishing",
        "publishedOn",
        mode="before",
    )
    def _validate_datetime(cls, value: Any) -> Any:
        return validate_datetime(value)

    @classmethod
    def user_model_type(cls) -> type[Lifecycle]:
        return Lifecycle


class DownloadTechnique(BaseModel):
    name: str | None = None
    pid: str | None = None

    @classmethod
    def user_model_type(cls) -> type[Technique]:
        return Technique

    @classmethod
    def upload_model_type(cls) -> type[UploadTechnique]:
        return UploadTechnique


class UploadTechnique(BaseModel):
    name: str
    pid: str

    @classmethod
    def user_model_type(cls) -> type[Technique]:
        return Technique

    @classmethod
    def download_model_type(cls) -> type[DownloadTechnique]:
        return DownloadTechnique


class DownloadRelationship(BaseModel):
    pid: PID | None = None
    relationship: str | None = None

    @classmethod
    def user_model_type(cls) -> type[Relationship]:
        return Relationship

    @classmethod
    def upload_model_type(cls) -> type[UploadRelationship]:
        return UploadRelationship


class UploadRelationship(BaseModel):
    pid: PID
    relationship: str

    @classmethod
    def user_model_type(cls) -> type[Relationship]:
        return Relationship

    @classmethod
    def download_model_type(cls) -> type[DownloadRelationship]:
        return DownloadRelationship


class DownloadHistory(BaseModel):
    id: str | None = None
    updatedAt: datetime | None = None
    updatedBy: str | None = None

    @pydantic.field_validator("updatedAt", mode="before")
    def _validate_datetime(cls, value: Any) -> Any:
        return validate_datetime(value)

    @classmethod
    def user_model_type(cls) -> type[History]:
        return History


class DownloadDataFile(BaseModel):
    path: str | None = None
    size: NonNegativeInt | None = None
    time: datetime | None = None
    chk: str | None = None
    gid: str | None = None
    perm: str | None = None
    uid: str | None = None

    @pydantic.field_validator("time", mode="before")
    def _validate_datetime(cls, value: Any) -> Any:
        return validate_datetime(value)

    @classmethod
    def upload_model_type(cls) -> type[UploadDataFile]:
        return UploadDataFile


class UploadDataFile(BaseModel):
    path: str
    size: NonNegativeInt
    time: datetime
    chk: str | None = None
    gid: str | None = None
    perm: str | None = None
    uid: str | None = None

    @pydantic.field_validator("time", mode="before")
    def _validate_datetime(cls, value: Any) -> Any:
        return validate_datetime(value)

    @classmethod
    def download_model_type(cls) -> type[DownloadDataFile]:
        return DownloadDataFile


class DownloadInstrument(BaseModel):
    customMetadata: dict[str, Any] | None = None
    name: str | None = None
    pid: str | None = None
    uniqueName: str | None = None

    @classmethod
    def user_model_type(cls) -> type[Instrument]:
        return Instrument


class DownloadSample(BaseModel):
    ownerGroup: str | None = None
    accessGroups: list[str] | None = None
    createdAt: datetime | None = None
    createdBy: str | None = None
    description: str | None = None
    instrumentGroup: str | None = None
    isPublished: bool | None = None
    owner: str | None = None
    sampleCharacteristics: dict[str, Any] | None = None
    sampleId: str | None = None
    updatedAt: datetime | None = None
    updatedBy: str | None = None

    @pydantic.field_validator("createdAt", "updatedAt", mode="before")
    def _validate_datetime(cls, value: Any) -> Any:
        return validate_datetime(value)

    @classmethod
    def user_model_type(cls) -> type[Sample]:
        return Sample

    @classmethod
    def upload_model_type(cls) -> type[UploadSample]:
        return UploadSample


class UploadSample(BaseModel):
    ownerGroup: str
    accessGroups: list[str] | None = None
    description: str | None = None
    instrumentGroup: str | None = None
    isPublished: bool | None = None
    owner: str | None = None
    sampleCharacteristics: dict[str, Any] | None = None
    sampleId: str | None = None

    @classmethod
    def user_model_type(cls) -> type[Sample]:
        return Sample

    @classmethod
    def download_model_type(cls) -> type[DownloadSample]:
        return DownloadSample


@dataclass(kw_only=True, slots=True)
class Attachment(BaseUserModel):
    caption: str
    owner_group: str
    access_groups: list[str] | None = None
    dataset_id: PID | None = None
    id: str | None = None
    instrument_group: str | None = None
    proposal_id: str | None = None
    sample_id: str | None = None
    thumbnail: Thumbnail | None = None
    _created_at: datetime | None = None
    _created_by: str | None = None
    _is_published: bool | None = None
    _updated_at: datetime | None = None
    _updated_by: str | None = None

    @property
    def created_at(self) -> datetime | None:
        return self._created_at

    @property
    def created_by(self) -> str | None:
        return self._created_by

    @property
    def is_published(self) -> bool | None:
        return self._is_published

    @property
    def updated_at(self) -> datetime | None:
        return self._updated_at

    @property
    def updated_by(self) -> str | None:
        return self._updated_by

    @classmethod
    def from_download_model(cls, download_model: DownloadAttachment) -> Attachment:
        """Construct an instance from an associated SciCat download model."""
        return cls(**cls._download_model_dict(download_model))

    def make_upload_model(self) -> UploadAttachment:
        """Construct a SciCat upload model from self."""
        return UploadAttachment(**self._upload_model_dict())

    @classmethod
    def upload_model_type(cls) -> type[UploadAttachment]:
        return UploadAttachment

    @classmethod
    def download_model_type(cls) -> type[DownloadAttachment]:
        return DownloadAttachment


@dataclass(kw_only=True, slots=True)
class Lifecycle(BaseUserModel):
    _archivable: bool | None = None
    _archive_retention_time: datetime | None = None
    _archive_return_message: dict[str, Any] | None = None
    _archive_status_message: str | None = None
    _date_of_disk_purging: datetime | None = None
    _date_of_publishing: datetime | None = None
    _exported_to: str | None = None
    _is_on_central_disk: bool | None = None
    _publishable: bool | None = None
    _published_on: datetime | None = None
    _retrievable: bool | None = None
    _retrieve_integrity_check: bool | None = None
    _retrieve_return_message: dict[str, Any] | None = None
    _retrieve_status_message: str | None = None

    @property
    def archivable(self) -> bool | None:
        return self._archivable

    @property
    def archive_retention_time(self) -> datetime | None:
        return self._archive_retention_time

    @property
    def archive_return_message(self) -> dict[str, Any] | None:
        return self._archive_return_message

    @property
    def archive_status_message(self) -> str | None:
        return self._archive_status_message

    @property
    def date_of_disk_purging(self) -> datetime | None:
        return self._date_of_disk_purging

    @property
    def date_of_publishing(self) -> datetime | None:
        return self._date_of_publishing

    @property
    def exported_to(self) -> str | None:
        return self._exported_to

    @property
    def is_on_central_disk(self) -> bool | None:
        return self._is_on_central_disk

    @property
    def publishable(self) -> bool | None:
        return self._publishable

    @property
    def published_on(self) -> datetime | None:
        return self._published_on

    @property
    def retrievable(self) -> bool | None:
        return self._retrievable

    @property
    def retrieve_integrity_check(self) -> bool | None:
        return self._retrieve_integrity_check

    @property
    def retrieve_return_message(self) -> dict[str, Any] | None:
        return self._retrieve_return_message

    @property
    def retrieve_status_message(self) -> str | None:
        return self._retrieve_status_message

    @classmethod
    def from_download_model(cls, download_model: DownloadLifecycle) -> Lifecycle:
        """Construct an instance from an associated SciCat download model."""
        return cls(**cls._download_model_dict(download_model))

    @classmethod
    def download_model_type(cls) -> type[DownloadLifecycle]:
        return DownloadLifecycle


@dataclass(kw_only=True, slots=True)
class Technique(BaseUserModel):
    name: str
    pid: str

    @classmethod
    def from_download_model(cls, download_model: DownloadTechnique) -> Technique:
        """Construct an instance from an associated SciCat download model."""
        return cls(**cls._download_model_dict(download_model))

    def make_upload_model(self) -> UploadTechnique:
        """Construct a SciCat upload model from self."""
        return UploadTechnique(**self._upload_model_dict())

    @classmethod
    def upload_model_type(cls) -> type[UploadTechnique]:
        return UploadTechnique

    @classmethod
    def download_model_type(cls) -> type[DownloadTechnique]:
        return DownloadTechnique


@dataclass(kw_only=True, slots=True)
class Relationship(BaseUserModel):
    pid: PID
    relationship: str

    @classmethod
    def from_download_model(cls, download_model: DownloadRelationship) -> Relationship:
        """Construct an instance from an associated SciCat download model."""
        return cls(**cls._download_model_dict(download_model))

    def make_upload_model(self) -> UploadRelationship:
        """Construct a SciCat upload model from self."""
        return UploadRelationship(**self._upload_model_dict())

    @classmethod
    def upload_model_type(cls) -> type[UploadRelationship]:
        return UploadRelationship

    @classmethod
    def download_model_type(cls) -> type[DownloadRelationship]:
        return DownloadRelationship


@dataclass(kw_only=True, slots=True)
class History(BaseUserModel):
    _id: str | None = None
    _updated_at: datetime | None = None
    _updated_by: str | None = None

    @property
    def id(self) -> str | None:
        return self._id

    @property
    def updated_at(self) -> datetime | None:
        return self._updated_at

    @property
    def updated_by(self) -> str | None:
        return self._updated_by

    @classmethod
    def from_download_model(cls, download_model: DownloadHistory) -> History:
        """Construct an instance from an associated SciCat download model."""
        return cls(**cls._download_model_dict(download_model))

    @classmethod
    def download_model_type(cls) -> type[DownloadHistory]:
        return DownloadHistory


@dataclass(kw_only=True, slots=True)
class Instrument(BaseUserModel):
    _custom_metadata: dict[str, Any] | None = None
    _name: str | None = None
    _pid: str | None = None
    _unique_name: str | None = None

    @property
    def custom_metadata(self) -> dict[str, Any] | None:
        return self._custom_metadata

    @property
    def name(self) -> str | None:
        return self._name

    @property
    def pid(self) -> str | None:
        return self._pid

    @property
    def unique_name(self) -> str | None:
        return self._unique_name

    @classmethod
    def from_download_model(cls, download_model: DownloadInstrument) -> Instrument:
        """Construct an instance from an associated SciCat download model."""
        return cls(**cls._download_model_dict(download_model))

    @classmethod
    def download_model_type(cls) -> type[DownloadInstrument]:
        return DownloadInstrument


@dataclass(kw_only=True, slots=True)
class Sample(BaseUserModel):
    owner_group: str
    access_groups: list[str] | None = None
    description: str | None = None
    instrument_group: str | None = None
    is_published: bool | None = None
    owner: str | None = None
    sample_characteristics: dict[str, Any] | None = None
    sample_id: str | None = None
    _created_at: datetime | None = None
    _created_by: str | None = None
    _updated_at: datetime | None = None
    _updated_by: str | None = None

    @property
    def created_at(self) -> datetime | None:
        return self._created_at

    @property
    def created_by(self) -> str | None:
        return self._created_by

    @property
    def updated_at(self) -> datetime | None:
        return self._updated_at

    @property
    def updated_by(self) -> str | None:
        return self._updated_by

    @classmethod
    def from_download_model(cls, download_model: DownloadSample) -> Sample:
        """Construct an instance from an associated SciCat download model."""
        return cls(**cls._download_model_dict(download_model))

    def make_upload_model(self) -> UploadSample:
        """Construct a SciCat upload model from self."""
        return UploadSample(**self._upload_model_dict())

    @classmethod
    def upload_model_type(cls) -> type[UploadSample]:
        return UploadSample

    @classmethod
    def download_model_type(cls) -> type[DownloadSample]:
        return DownloadSample


# Some models contain fields that are other models which are defined
# further down in the file.
# Instead of ordering models according to their dependencies, resolve
# references once all classes have been defined.
DownloadAttachment.model_rebuild()
UploadAttachment.model_rebuild()
DownloadOrigDatablock.model_rebuild()
UploadOrigDatablock.model_rebuild()
DownloadDatablock.model_rebuild()
UploadDatablock.model_rebuild()
DownloadLifecycle.model_rebuild()
DownloadTechnique.model_rebuild()
UploadTechnique.model_rebuild()
DownloadRelationship.model_rebuild()
UploadRelationship.model_rebuild()
DownloadHistory.model_rebuild()
DownloadDataFile.model_rebuild()
UploadDataFile.model_rebuild()
DownloadInstrument.model_rebuild()
DownloadSample.model_rebuild()
UploadSample.model_rebuild()
DownloadDataset.model_rebuild()
UploadDerivedDataset.model_rebuild()
UploadRawDataset.model_rebuild()

__all__ = (
    "BaseModel",
    "BaseUserModel",
    "DatasetType",
    "construct",
    "DownloadDataset",
    "UploadDerivedDataset",
    "UploadRawDataset",
    "DownloadAttachment",
    "UploadAttachment",
    "DownloadOrigDatablock",
    "UploadOrigDatablock",
    "DownloadDatablock",
    "UploadDatablock",
    "DownloadLifecycle",
    "DownloadTechnique",
    "UploadTechnique",
    "DownloadRelationship",
    "UploadRelationship",
    "DownloadHistory",
    "DownloadDataFile",
    "UploadDataFile",
    "DownloadInstrument",
    "DownloadSample",
    "UploadSample",
    "Attachment",
    "Lifecycle",
    "Technique",
    "Relationship",
    "History",
    "Instrument",
    "Sample",
)
