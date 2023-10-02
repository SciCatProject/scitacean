##########################################
# This file was automatically generated. #
# Do not modify it directly!             #
##########################################

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
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

from datetime import datetime
from typing import Any, Dict, List, Optional, Type

import pydantic
from pydantic import NonNegativeInt

from ._base_model import (
    BaseModel,
    BaseUserModel,
    DatasetType,
    construct,
    validate_datetime,
    validate_drop,
    validate_emails,
    validate_orcids,
)
from ._internal.dataclass_wrapper import dataclass_optional_args
from ._internal.pydantic_compat import field_validator
from .filesystem import RemotePath
from .pid import PID
from .thumbnail import Thumbnail


class DownloadDataset(
    BaseModel, masked=("attachments", "datablocks", "origdatablocks")
):
    contactEmail: Optional[str] = None
    creationLocation: Optional[str] = None
    creationTime: Optional[datetime] = None
    inputDatasets: Optional[List[PID]] = None
    investigator: Optional[str] = None
    numberOfFilesArchived: Optional[NonNegativeInt] = None
    owner: Optional[str] = None
    ownerGroup: Optional[str] = None
    principalInvestigator: Optional[str] = None
    sourceFolder: Optional[RemotePath] = None
    type: Optional[DatasetType] = None
    usedSoftware: Optional[List[str]] = None
    accessGroups: Optional[List[str]] = None
    version: Optional[str] = None
    classification: Optional[str] = None
    comment: Optional[str] = None
    createdAt: Optional[datetime] = None
    createdBy: Optional[str] = None
    dataFormat: Optional[str] = None
    dataQualityMetrics: Optional[int] = None
    description: Optional[str] = None
    endTime: Optional[datetime] = None
    history: Optional[None] = None
    instrumentGroup: Optional[str] = None
    instrumentId: Optional[str] = None
    isPublished: Optional[bool] = None
    jobLogData: Optional[str] = None
    jobParameters: Optional[Dict[str, Any]] = None
    keywords: Optional[List[str]] = None
    license: Optional[str] = None
    datasetlifecycle: Optional[DownloadLifecycle] = None
    scientificMetadata: Optional[Dict[str, Any]] = None
    datasetName: Optional[str] = None
    numberOfFiles: Optional[NonNegativeInt] = None
    orcidOfOwner: Optional[str] = None
    ownerEmail: Optional[str] = None
    packedSize: Optional[NonNegativeInt] = None
    pid: Optional[PID] = None
    proposalId: Optional[str] = None
    relationships: Optional[List[DownloadRelationship]] = None
    sampleId: Optional[str] = None
    sharedWith: Optional[List[str]] = None
    size: Optional[NonNegativeInt] = None
    sourceFolderHost: Optional[str] = None
    techniques: Optional[List[DownloadTechnique]] = None
    updatedAt: Optional[datetime] = None
    updatedBy: Optional[str] = None
    validationStatus: Optional[str] = None

    @field_validator("creationTime", "createdAt", "endTime", "updatedAt", mode="before")
    def _validate_datetime(cls, value: Any) -> Any:
        return validate_datetime(value)

    @field_validator("history", mode="before")
    def _validate_drop(cls, value: Any) -> Any:
        return validate_drop(value)

    @field_validator("contactEmail", "ownerEmail", mode="before")
    def _validate_emails(cls, value: Any) -> Any:
        return validate_emails(value)

    @field_validator("orcidOfOwner", mode="before")
    def _validate_orcids(cls, value: Any) -> Any:
        return validate_orcids(value)


class UploadDerivedDataset(BaseModel):
    contactEmail: str
    creationTime: datetime
    inputDatasets: List[PID]
    investigator: str
    numberOfFilesArchived: NonNegativeInt
    owner: str
    ownerGroup: str
    sourceFolder: RemotePath
    type: DatasetType
    usedSoftware: List[str]
    accessGroups: Optional[List[str]] = None
    classification: Optional[str] = None
    comment: Optional[str] = None
    dataQualityMetrics: Optional[int] = None
    description: Optional[str] = None
    instrumentGroup: Optional[str] = None
    isPublished: Optional[bool] = None
    jobLogData: Optional[str] = None
    jobParameters: Optional[Dict[str, Any]] = None
    keywords: Optional[List[str]] = None
    license: Optional[str] = None
    scientificMetadata: Optional[Dict[str, Any]] = None
    datasetName: Optional[str] = None
    numberOfFiles: Optional[NonNegativeInt] = None
    orcidOfOwner: Optional[str] = None
    ownerEmail: Optional[str] = None
    packedSize: Optional[NonNegativeInt] = None
    relationships: Optional[List[UploadRelationship]] = None
    sharedWith: Optional[List[str]] = None
    size: Optional[NonNegativeInt] = None
    sourceFolderHost: Optional[str] = None
    techniques: Optional[List[UploadTechnique]] = None
    validationStatus: Optional[str] = None

    @field_validator("creationTime", mode="before")
    def _validate_datetime(cls, value: Any) -> Any:
        return validate_datetime(value)

    @field_validator("contactEmail", "ownerEmail", mode="before")
    def _validate_emails(cls, value: Any) -> Any:
        return validate_emails(value)

    @field_validator("orcidOfOwner", mode="before")
    def _validate_orcids(cls, value: Any) -> Any:
        return validate_orcids(value)


class UploadRawDataset(BaseModel):
    contactEmail: str
    creationLocation: str
    creationTime: datetime
    numberOfFilesArchived: NonNegativeInt
    owner: str
    ownerGroup: str
    principalInvestigator: str
    sourceFolder: RemotePath
    type: DatasetType
    accessGroups: Optional[List[str]] = None
    classification: Optional[str] = None
    comment: Optional[str] = None
    dataFormat: Optional[str] = None
    dataQualityMetrics: Optional[int] = None
    description: Optional[str] = None
    endTime: Optional[datetime] = None
    instrumentGroup: Optional[str] = None
    instrumentId: Optional[str] = None
    isPublished: Optional[bool] = None
    keywords: Optional[List[str]] = None
    license: Optional[str] = None
    scientificMetadata: Optional[Dict[str, Any]] = None
    datasetName: Optional[str] = None
    numberOfFiles: Optional[NonNegativeInt] = None
    orcidOfOwner: Optional[str] = None
    ownerEmail: Optional[str] = None
    packedSize: Optional[NonNegativeInt] = None
    proposalId: Optional[str] = None
    relationships: Optional[List[UploadRelationship]] = None
    sampleId: Optional[str] = None
    sharedWith: Optional[List[str]] = None
    size: Optional[NonNegativeInt] = None
    sourceFolderHost: Optional[str] = None
    techniques: Optional[List[UploadTechnique]] = None
    validationStatus: Optional[str] = None

    @field_validator("creationTime", "endTime", mode="before")
    def _validate_datetime(cls, value: Any) -> Any:
        return validate_datetime(value)

    @field_validator("contactEmail", "ownerEmail", mode="before")
    def _validate_emails(cls, value: Any) -> Any:
        return validate_emails(value)

    @field_validator("orcidOfOwner", mode="before")
    def _validate_orcids(cls, value: Any) -> Any:
        return validate_orcids(value)


class DownloadAttachment(BaseModel):
    caption: Optional[str] = None
    ownerGroup: Optional[str] = None
    accessGroups: Optional[List[str]] = None
    createdAt: Optional[datetime] = None
    createdBy: Optional[str] = None
    datasetId: Optional[PID] = None
    id: Optional[str] = None
    instrumentGroup: Optional[str] = None
    proposalId: Optional[str] = None
    sampleId: Optional[str] = None
    thumbnail: Optional[Thumbnail] = None
    updatedAt: Optional[datetime] = None
    updatedBy: Optional[str] = None

    @field_validator("createdAt", "updatedAt", mode="before")
    def _validate_datetime(cls, value: Any) -> Any:
        return validate_datetime(value)

    @classmethod
    def user_model_type(cls) -> Type[Attachment]:
        return Attachment

    @classmethod
    def upload_model_type(cls) -> Type[UploadAttachment]:
        return UploadAttachment


class UploadAttachment(BaseModel):
    caption: str
    ownerGroup: str
    accessGroups: Optional[List[str]] = None
    datasetId: Optional[PID] = None
    id: Optional[str] = None
    instrumentGroup: Optional[str] = None
    proposalId: Optional[str] = None
    sampleId: Optional[str] = None
    thumbnail: Optional[Thumbnail] = None

    @classmethod
    def user_model_type(cls) -> Type[Attachment]:
        return Attachment

    @classmethod
    def download_model_type(cls) -> Type[DownloadAttachment]:
        return DownloadAttachment


class DownloadOrigDatablock(BaseModel):
    dataFileList: Optional[List[DownloadDataFile]] = None
    datasetId: Optional[PID] = None
    size: Optional[NonNegativeInt] = None
    id: Optional[str] = pydantic.Field(alias="_id", default=None)
    accessGroups: Optional[List[str]] = None
    chkAlg: Optional[str] = None
    createdAt: Optional[datetime] = None
    createdBy: Optional[str] = None
    instrumentGroup: Optional[str] = None
    ownerGroup: Optional[str] = None
    updatedAt: Optional[datetime] = None
    updatedBy: Optional[str] = None

    @field_validator("createdAt", "updatedAt", mode="before")
    def _validate_datetime(cls, value: Any) -> Any:
        return validate_datetime(value)

    @classmethod
    def upload_model_type(cls) -> Type[UploadOrigDatablock]:
        return UploadOrigDatablock


class UploadOrigDatablock(BaseModel):
    dataFileList: List[UploadDataFile]
    datasetId: PID
    size: NonNegativeInt
    accessGroups: Optional[List[str]] = None
    chkAlg: Optional[str] = None
    instrumentGroup: Optional[str] = None
    ownerGroup: Optional[str] = None

    @classmethod
    def download_model_type(cls) -> Type[DownloadOrigDatablock]:
        return DownloadOrigDatablock


class DownloadDatablock(BaseModel):
    archiveId: Optional[str] = None
    dataFileList: Optional[List[DownloadDataFile]] = None
    packedSize: Optional[NonNegativeInt] = None
    size: Optional[NonNegativeInt] = None
    version: Optional[str] = None
    id: Optional[str] = pydantic.Field(alias="_id", default=None)
    accessGroups: Optional[List[str]] = None
    chkAlg: Optional[str] = None
    createdAt: Optional[datetime] = None
    createdBy: Optional[str] = None
    datasetId: Optional[PID] = None
    instrumentGroup: Optional[str] = None
    ownerGroup: Optional[str] = None
    updatedAt: Optional[datetime] = None
    updatedBy: Optional[str] = None

    @field_validator("createdAt", "updatedAt", mode="before")
    def _validate_datetime(cls, value: Any) -> Any:
        return validate_datetime(value)

    @classmethod
    def upload_model_type(cls) -> Type[UploadDatablock]:
        return UploadDatablock


class UploadDatablock(BaseModel):
    archiveId: str
    dataFileList: List[UploadDataFile]
    packedSize: NonNegativeInt
    size: NonNegativeInt
    version: str
    chkAlg: Optional[str] = None

    @classmethod
    def download_model_type(cls) -> Type[DownloadDatablock]:
        return DownloadDatablock


class DownloadLifecycle(BaseModel):
    archivable: Optional[bool] = None
    archiveRetentionTime: Optional[datetime] = None
    archiveReturnMessage: Optional[Dict[str, Any]] = None
    archiveStatusMessage: Optional[str] = None
    dateOfDiskPurging: Optional[datetime] = None
    dateOfPublishing: Optional[datetime] = None
    exportedTo: Optional[str] = None
    isOnCentralDisk: Optional[bool] = None
    publishable: Optional[bool] = None
    publishedOn: Optional[datetime] = None
    retrievable: Optional[bool] = None
    retrieveIntegrityCheck: Optional[bool] = None
    retrieveReturnMessage: Optional[Dict[str, Any]] = None
    retrieveStatusMessage: Optional[str] = None

    @field_validator(
        "archiveRetentionTime",
        "dateOfDiskPurging",
        "dateOfPublishing",
        "publishedOn",
        mode="before",
    )
    def _validate_datetime(cls, value: Any) -> Any:
        return validate_datetime(value)

    @classmethod
    def user_model_type(cls) -> Type[Lifecycle]:
        return Lifecycle


class DownloadTechnique(BaseModel):
    name: Optional[str] = None
    pid: Optional[str] = None

    @classmethod
    def user_model_type(cls) -> Type[Technique]:
        return Technique

    @classmethod
    def upload_model_type(cls) -> Type[UploadTechnique]:
        return UploadTechnique


class UploadTechnique(BaseModel):
    name: str
    pid: str

    @classmethod
    def user_model_type(cls) -> Type[Technique]:
        return Technique

    @classmethod
    def download_model_type(cls) -> Type[DownloadTechnique]:
        return DownloadTechnique


class DownloadRelationship(BaseModel):
    pid: Optional[PID] = None
    relationship: Optional[str] = None

    @classmethod
    def user_model_type(cls) -> Type[Relationship]:
        return Relationship

    @classmethod
    def upload_model_type(cls) -> Type[UploadRelationship]:
        return UploadRelationship


class UploadRelationship(BaseModel):
    pid: PID
    relationship: str

    @classmethod
    def user_model_type(cls) -> Type[Relationship]:
        return Relationship

    @classmethod
    def download_model_type(cls) -> Type[DownloadRelationship]:
        return DownloadRelationship


class DownloadHistory(BaseModel):
    id: Optional[str] = pydantic.Field(alias="_id", default=None)
    updatedAt: Optional[datetime] = None
    updatedBy: Optional[datetime] = None

    @field_validator("updatedAt", mode="before")
    def _validate_datetime(cls, value: Any) -> Any:
        return validate_datetime(value)

    @classmethod
    def user_model_type(cls) -> Type[History]:
        return History


class DownloadDataFile(BaseModel):
    path: Optional[str] = None
    size: Optional[NonNegativeInt] = None
    time: Optional[datetime] = None
    chk: Optional[str] = None
    gid: Optional[str] = None
    perm: Optional[str] = None
    uid: Optional[str] = None

    @field_validator("time", mode="before")
    def _validate_datetime(cls, value: Any) -> Any:
        return validate_datetime(value)

    @classmethod
    def upload_model_type(cls) -> Type[UploadDataFile]:
        return UploadDataFile


class UploadDataFile(BaseModel):
    path: str
    size: NonNegativeInt
    time: datetime
    chk: Optional[str] = None
    gid: Optional[str] = None
    perm: Optional[str] = None
    uid: Optional[str] = None

    @field_validator("time", mode="before")
    def _validate_datetime(cls, value: Any) -> Any:
        return validate_datetime(value)

    @classmethod
    def download_model_type(cls) -> Type[DownloadDataFile]:
        return DownloadDataFile


class DownloadInstrument(BaseModel):
    customMetadata: Optional[Dict[str, Any]] = None
    name: Optional[str] = None
    pid: Optional[str] = None
    uniqueName: Optional[str] = None

    @classmethod
    def user_model_type(cls) -> Type[Instrument]:
        return Instrument


class DownloadSample(BaseModel):
    ownerGroup: Optional[str] = None
    accessGroups: Optional[List[str]] = None
    createdAt: Optional[datetime] = None
    createdBy: Optional[str] = None
    description: Optional[str] = None
    instrumentGroup: Optional[str] = None
    isPublished: Optional[bool] = None
    owner: Optional[str] = None
    sampleCharacteristics: Optional[Dict[str, Any]] = None
    sampleId: Optional[str] = None
    updatedAt: Optional[datetime] = None
    updatedBy: Optional[str] = None

    @field_validator("createdAt", "updatedAt", mode="before")
    def _validate_datetime(cls, value: Any) -> Any:
        return validate_datetime(value)

    @classmethod
    def user_model_type(cls) -> Type[Sample]:
        return Sample

    @classmethod
    def upload_model_type(cls) -> Type[UploadSample]:
        return UploadSample


class UploadSample(BaseModel):
    ownerGroup: str
    accessGroups: Optional[List[str]] = None
    description: Optional[str] = None
    instrumentGroup: Optional[str] = None
    isPublished: Optional[bool] = None
    owner: Optional[str] = None
    sampleCharacteristics: Optional[Dict[str, Any]] = None
    sampleId: Optional[str] = None

    @classmethod
    def user_model_type(cls) -> Type[Sample]:
        return Sample

    @classmethod
    def download_model_type(cls) -> Type[DownloadSample]:
        return DownloadSample


@dataclass_optional_args(kw_only=True, slots=True)
class Attachment(BaseUserModel):
    caption: str
    owner_group: str
    access_groups: Optional[List[str]] = None
    dataset_id: Optional[PID] = None
    id: Optional[str] = None
    instrument_group: Optional[str] = None
    proposal_id: Optional[str] = None
    sample_id: Optional[str] = None
    thumbnail: Optional[Thumbnail] = None
    _created_at: Optional[datetime] = None
    _created_by: Optional[str] = None
    _updated_at: Optional[datetime] = None
    _updated_by: Optional[str] = None

    @property
    def created_at(self) -> Optional[datetime]:
        return self._created_at

    @property
    def created_by(self) -> Optional[str]:
        return self._created_by

    @property
    def updated_at(self) -> Optional[datetime]:
        return self._updated_at

    @property
    def updated_by(self) -> Optional[str]:
        return self._updated_by

    @classmethod
    def from_download_model(cls, download_model: DownloadAttachment) -> Attachment:
        """Construct an instance from an associated SciCat download model."""
        return cls(**cls._download_model_dict(download_model))

    def make_upload_model(self) -> UploadAttachment:
        """Construct a SciCat upload model from self."""
        return UploadAttachment(**self._upload_model_dict())

    @classmethod
    def upload_model_type(cls) -> Type[UploadAttachment]:
        return UploadAttachment

    @classmethod
    def download_model_type(cls) -> Type[DownloadAttachment]:
        return DownloadAttachment


@dataclass_optional_args(kw_only=True, slots=True)
class Lifecycle(BaseUserModel):
    _archivable: Optional[bool] = None
    _archive_retention_time: Optional[datetime] = None
    _archive_return_message: Optional[Dict[str, Any]] = None
    _archive_status_message: Optional[str] = None
    _date_of_disk_purging: Optional[datetime] = None
    _date_of_publishing: Optional[datetime] = None
    _exported_to: Optional[str] = None
    _is_on_central_disk: Optional[bool] = None
    _publishable: Optional[bool] = None
    _published_on: Optional[datetime] = None
    _retrievable: Optional[bool] = None
    _retrieve_integrity_check: Optional[bool] = None
    _retrieve_return_message: Optional[Dict[str, Any]] = None
    _retrieve_status_message: Optional[str] = None

    @property
    def archivable(self) -> Optional[bool]:
        return self._archivable

    @property
    def archive_retention_time(self) -> Optional[datetime]:
        return self._archive_retention_time

    @property
    def archive_return_message(self) -> Optional[Dict[str, Any]]:
        return self._archive_return_message

    @property
    def archive_status_message(self) -> Optional[str]:
        return self._archive_status_message

    @property
    def date_of_disk_purging(self) -> Optional[datetime]:
        return self._date_of_disk_purging

    @property
    def date_of_publishing(self) -> Optional[datetime]:
        return self._date_of_publishing

    @property
    def exported_to(self) -> Optional[str]:
        return self._exported_to

    @property
    def is_on_central_disk(self) -> Optional[bool]:
        return self._is_on_central_disk

    @property
    def publishable(self) -> Optional[bool]:
        return self._publishable

    @property
    def published_on(self) -> Optional[datetime]:
        return self._published_on

    @property
    def retrievable(self) -> Optional[bool]:
        return self._retrievable

    @property
    def retrieve_integrity_check(self) -> Optional[bool]:
        return self._retrieve_integrity_check

    @property
    def retrieve_return_message(self) -> Optional[Dict[str, Any]]:
        return self._retrieve_return_message

    @property
    def retrieve_status_message(self) -> Optional[str]:
        return self._retrieve_status_message

    @classmethod
    def from_download_model(cls, download_model: DownloadLifecycle) -> Lifecycle:
        """Construct an instance from an associated SciCat download model."""
        return cls(**cls._download_model_dict(download_model))

    @classmethod
    def download_model_type(cls) -> Type[DownloadLifecycle]:
        return DownloadLifecycle


@dataclass_optional_args(kw_only=True, slots=True)
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
    def upload_model_type(cls) -> Type[UploadTechnique]:
        return UploadTechnique

    @classmethod
    def download_model_type(cls) -> Type[DownloadTechnique]:
        return DownloadTechnique


@dataclass_optional_args(kw_only=True, slots=True)
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
    def upload_model_type(cls) -> Type[UploadRelationship]:
        return UploadRelationship

    @classmethod
    def download_model_type(cls) -> Type[DownloadRelationship]:
        return DownloadRelationship


@dataclass_optional_args(kw_only=True, slots=True)
class History(BaseUserModel):
    __id: Optional[str] = None
    _updated_at: Optional[datetime] = None
    _updated_by: Optional[datetime] = None

    @property
    def _id(self) -> Optional[str]:
        return self.__id

    @property
    def updated_at(self) -> Optional[datetime]:
        return self._updated_at

    @property
    def updated_by(self) -> Optional[datetime]:
        return self._updated_by

    @classmethod
    def from_download_model(cls, download_model: DownloadHistory) -> History:
        """Construct an instance from an associated SciCat download model."""
        return cls(**cls._download_model_dict(download_model))

    @classmethod
    def download_model_type(cls) -> Type[DownloadHistory]:
        return DownloadHistory


@dataclass_optional_args(kw_only=True, slots=True)
class Instrument(BaseUserModel):
    _custom_metadata: Optional[Dict[str, Any]] = None
    _name: Optional[str] = None
    _pid: Optional[str] = None
    _unique_name: Optional[str] = None

    @property
    def custom_metadata(self) -> Optional[Dict[str, Any]]:
        return self._custom_metadata

    @property
    def name(self) -> Optional[str]:
        return self._name

    @property
    def pid(self) -> Optional[str]:
        return self._pid

    @property
    def unique_name(self) -> Optional[str]:
        return self._unique_name

    @classmethod
    def from_download_model(cls, download_model: DownloadInstrument) -> Instrument:
        """Construct an instance from an associated SciCat download model."""
        return cls(**cls._download_model_dict(download_model))

    @classmethod
    def download_model_type(cls) -> Type[DownloadInstrument]:
        return DownloadInstrument


@dataclass_optional_args(kw_only=True, slots=True)
class Sample(BaseUserModel):
    owner_group: str
    access_groups: Optional[List[str]] = None
    description: Optional[str] = None
    instrument_group: Optional[str] = None
    is_published: Optional[bool] = None
    owner: Optional[str] = None
    sample_characteristics: Optional[Dict[str, Any]] = None
    sample_id: Optional[str] = None
    _created_at: Optional[datetime] = None
    _created_by: Optional[str] = None
    _updated_at: Optional[datetime] = None
    _updated_by: Optional[str] = None

    @property
    def created_at(self) -> Optional[datetime]:
        return self._created_at

    @property
    def created_by(self) -> Optional[str]:
        return self._created_by

    @property
    def updated_at(self) -> Optional[datetime]:
        return self._updated_at

    @property
    def updated_by(self) -> Optional[str]:
        return self._updated_by

    @classmethod
    def from_download_model(cls, download_model: DownloadSample) -> Sample:
        """Construct an instance from an associated SciCat download model."""
        return cls(**cls._download_model_dict(download_model))

    def make_upload_model(self) -> UploadSample:
        """Construct a SciCat upload model from self."""
        return UploadSample(**self._upload_model_dict())

    @classmethod
    def upload_model_type(cls) -> Type[UploadSample]:
        return UploadSample

    @classmethod
    def download_model_type(cls) -> Type[DownloadSample]:
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
