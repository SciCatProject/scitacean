##########################################
# This file was automatically generated. #
# Do not modify it directly!             #
##########################################

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Models for communication with SciCat and user facing dataclasses."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

import pydantic
from pydantic import NonNegativeInt

from ._base_model import (
    BaseModel,
    BaseUserModel,
    DatasetType,
    validate_emails,
    validate_orcids,
)
from ._internal.dataclass_wrapper import dataclass_optional_args
from .filesystem import RemotePath
from .pid import PID


class DownloadDataset(
    BaseModel, masked=("attachments", "datablocks", "origdatablocks")
):
    contactEmail: str
    creationTime: datetime
    numberOfFilesArchived: NonNegativeInt
    owner: str
    ownerGroup: str
    sourceFolder: RemotePath
    type: DatasetType
    accessGroups: Optional[List[str]]
    version: Optional[str]
    classification: Optional[str]
    comment: Optional[str]
    createdAt: Optional[datetime]
    createdBy: Optional[str]
    creationLocation: Optional[str]
    dataFormat: Optional[str]
    dataQualityMetrics: Optional[int]
    description: Optional[str]
    endTime: Optional[datetime]
    history: Optional[DownloadHistory]
    inputDatasets: Optional[List[PID]]
    instrumentGroup: Optional[str]
    instrumentId: Optional[str]
    investigator: Optional[str]
    isPublished: Optional[bool]
    jobLogData: Optional[str]
    jobParameters: Optional[Dict[str, Any]]
    keywords: Optional[List[str]]
    license: Optional[str]
    datasetlifecycle: Optional[DownloadLifecycle]
    scientificMetadata: Optional[Dict[str, Any]]
    datasetName: Optional[str]
    numberOfFiles: Optional[NonNegativeInt]
    orcidOfOwner: Optional[str]
    ownerEmail: Optional[str]
    packedSize: Optional[NonNegativeInt]
    pid: Optional[PID]
    principalInvestigator: Optional[str]
    proposalId: Optional[str]
    relationships: Optional[List[DownloadRelationship]]
    sampleId: Optional[str]
    sharedWith: Optional[List[str]]
    size: Optional[NonNegativeInt]
    sourceFolderHost: Optional[str]
    techniques: Optional[List[DownloadTechnique]]
    updatedAt: Optional[datetime]
    updatedBy: Optional[str]
    usedSoftware: Optional[List[str]]
    validationStatus: Optional[str]

    @pydantic.validator("contactEmail", "ownerEmail")
    def _validate_emails(cls, value: Any) -> Any:
        return validate_emails(value)

    @pydantic.validator("orcidOfOwner")
    def _validate_orcids(cls, value: Any) -> Any:
        return validate_orcids(value)


class UploadDerivedDataset(BaseModel):
    contactEmail: str
    creationTime: datetime
    numberOfFilesArchived: NonNegativeInt
    owner: str
    ownerGroup: str
    sourceFolder: RemotePath
    type: DatasetType
    accessGroups: Optional[List[str]]
    classification: Optional[str]
    comment: Optional[str]
    dataQualityMetrics: Optional[int]
    description: Optional[str]
    inputDatasets: Optional[List[PID]]
    instrumentGroup: Optional[str]
    investigator: Optional[str]
    isPublished: Optional[bool]
    jobLogData: Optional[str]
    jobParameters: Optional[Dict[str, Any]]
    keywords: Optional[List[str]]
    license: Optional[str]
    scientificMetadata: Optional[Dict[str, Any]]
    datasetName: Optional[str]
    numberOfFiles: Optional[NonNegativeInt]
    orcidOfOwner: Optional[str]
    ownerEmail: Optional[str]
    packedSize: Optional[NonNegativeInt]
    relationships: Optional[List[UploadRelationship]]
    sharedWith: Optional[List[str]]
    size: Optional[NonNegativeInt]
    sourceFolderHost: Optional[str]
    techniques: Optional[List[UploadTechnique]]
    usedSoftware: Optional[List[str]]
    validationStatus: Optional[str]

    @pydantic.validator("contactEmail", "ownerEmail")
    def _validate_emails(cls, value: Any) -> Any:
        return validate_emails(value)

    @pydantic.validator("orcidOfOwner")
    def _validate_orcids(cls, value: Any) -> Any:
        return validate_orcids(value)


class UploadRawDataset(BaseModel):
    contactEmail: str
    creationTime: datetime
    numberOfFilesArchived: NonNegativeInt
    owner: str
    ownerGroup: str
    sourceFolder: RemotePath
    type: DatasetType
    accessGroups: Optional[List[str]]
    classification: Optional[str]
    comment: Optional[str]
    creationLocation: Optional[str]
    dataFormat: Optional[str]
    dataQualityMetrics: Optional[int]
    description: Optional[str]
    endTime: Optional[datetime]
    instrumentGroup: Optional[str]
    instrumentId: Optional[str]
    isPublished: Optional[bool]
    keywords: Optional[List[str]]
    license: Optional[str]
    scientificMetadata: Optional[Dict[str, Any]]
    datasetName: Optional[str]
    numberOfFiles: Optional[NonNegativeInt]
    orcidOfOwner: Optional[str]
    ownerEmail: Optional[str]
    packedSize: Optional[NonNegativeInt]
    principalInvestigator: Optional[str]
    proposalId: Optional[str]
    relationships: Optional[List[UploadRelationship]]
    sampleId: Optional[str]
    sharedWith: Optional[List[str]]
    size: Optional[NonNegativeInt]
    sourceFolderHost: Optional[str]
    techniques: Optional[List[UploadTechnique]]
    validationStatus: Optional[str]

    @pydantic.validator("contactEmail", "ownerEmail")
    def _validate_emails(cls, value: Any) -> Any:
        return validate_emails(value)

    @pydantic.validator("orcidOfOwner")
    def _validate_orcids(cls, value: Any) -> Any:
        return validate_orcids(value)


class DownloadAttachment(BaseModel):
    caption: str
    ownerGroup: str
    accessGroups: Optional[List[str]]
    createdAt: Optional[datetime]
    createdBy: Optional[str]
    datasetId: Optional[str]
    id: Optional[str]
    instrumentGroup: Optional[str]
    proposalId: Optional[str]
    sampleId: Optional[str]
    thumbnail: Optional[str]
    updatedAt: Optional[datetime]
    updatedBy: Optional[str]


class UploadAttachment(BaseModel):
    caption: str
    ownerGroup: str
    accessGroups: Optional[List[str]]
    datasetId: Optional[str]
    id: Optional[str]
    instrumentGroup: Optional[str]
    proposalId: Optional[str]
    sampleId: Optional[str]
    thumbnail: Optional[str]


class DownloadOrigDatablock(BaseModel):
    chkAlg: str
    dataFileList: List[DownloadDataFile]
    datasetId: PID
    ownerGroup: str
    size: NonNegativeInt
    _id: Optional[str]
    accessGroups: Optional[List[str]]
    createdAt: Optional[datetime]
    createdBy: Optional[str]
    instrumentGroup: Optional[str]
    updatedAt: Optional[datetime]
    updatedBy: Optional[str]


class UploadOrigDatablock(BaseModel):
    chkAlg: str
    dataFileList: List[UploadDataFile]
    datasetId: PID
    ownerGroup: str
    size: NonNegativeInt
    accessGroups: Optional[List[str]]
    instrumentGroup: Optional[str]


class DownloadDatablock(BaseModel):
    archiveId: str
    chkAlg: str
    dataFileList: List[DownloadDataFile]
    packedSize: NonNegativeInt
    size: NonNegativeInt
    version: str
    _id: Optional[str]
    accessGroups: Optional[List[str]]
    createdAt: Optional[datetime]
    createdBy: Optional[str]
    datasetId: Optional[PID]
    instrumentGroup: Optional[str]
    ownerGroup: Optional[str]
    updatedAt: Optional[datetime]
    updatedBy: Optional[str]


class UploadDatablock(BaseModel):
    archiveId: str
    chkAlg: str
    dataFileList: List[UploadDataFile]
    packedSize: NonNegativeInt
    size: NonNegativeInt
    version: str


class DownloadLifecycle(BaseModel):
    archivable: Optional[bool]
    archiveRetentionTime: Optional[datetime]
    archiveReturnMessage: Optional[Dict[str, Any]]
    archiveStatusMessage: Optional[str]
    dateOfDiskPurging: Optional[datetime]
    dateOfPublishing: Optional[datetime]
    exportedTo: Optional[str]
    isOnCentralDisk: Optional[bool]
    publishable: Optional[bool]
    publishedOn: Optional[datetime]
    retrievable: Optional[bool]
    retrieveIntegrityCheck: Optional[bool]
    retrieveReturnMessage: Optional[Dict[str, Any]]
    retrieveStatusMessage: Optional[str]


class DownloadTechnique(BaseModel):
    name: str
    pid: str


class UploadTechnique(BaseModel):
    name: str
    pid: str


class DownloadRelationship(BaseModel):
    pid: PID
    relationship: str


class UploadRelationship(BaseModel):
    pid: PID
    relationship: str


class DownloadHistory(BaseModel):
    _id: Optional[str]
    updatedAt: Optional[datetime]
    updatedBy: Optional[datetime]


class DownloadDataFile(BaseModel):
    path: str
    size: NonNegativeInt
    time: datetime
    chk: Optional[str]
    gid: Optional[str]
    perm: Optional[str]
    uid: Optional[str]


class UploadDataFile(BaseModel):
    path: str
    size: NonNegativeInt
    time: datetime
    chk: Optional[str]
    gid: Optional[str]
    perm: Optional[str]
    uid: Optional[str]


class DownloadInstrument(BaseModel):
    customMetadata: Optional[Dict[str, Any]]
    name: Optional[str]
    pid: Optional[str]
    uniqueName: Optional[str]


class DownloadSample(BaseModel):
    ownerGroup: str
    accessGroups: Optional[List[str]]
    createdAt: Optional[datetime]
    createdBy: Optional[str]
    description: Optional[str]
    instrumentGroup: Optional[str]
    isPublished: Optional[bool]
    owner: Optional[str]
    sampleCharacteristics: Optional[Dict[str, Any]]
    sampleId: Optional[str]
    updatedAt: Optional[datetime]
    updatedBy: Optional[str]


class UploadSample(BaseModel):
    ownerGroup: str
    accessGroups: Optional[List[str]]
    description: Optional[str]
    instrumentGroup: Optional[str]
    isPublished: Optional[bool]
    owner: Optional[str]
    sampleCharacteristics: Optional[Dict[str, Any]]
    sampleId: Optional[str]


@dataclass_optional_args(kw_only=True, slots=True)
class Attachment(BaseUserModel):
    caption: str
    owner_group: str
    access_groups: Optional[List[str]] = None
    dataset_id: Optional[str] = None
    id: Optional[str] = None
    instrument_group: Optional[str] = None
    proposal_id: Optional[str] = None
    sample_id: Optional[str] = None
    thumbnail: Optional[str] = None
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


# Some models contain fields that are other models which are defined
# further down in the file.
# Instead of ordering models according to their dependencies, resolve
# references once all classes have been defined.
DownloadAttachment.update_forward_refs()
UploadAttachment.update_forward_refs()
DownloadOrigDatablock.update_forward_refs()
UploadOrigDatablock.update_forward_refs()
DownloadDatablock.update_forward_refs()
UploadDatablock.update_forward_refs()
DownloadLifecycle.update_forward_refs()
DownloadTechnique.update_forward_refs()
UploadTechnique.update_forward_refs()
DownloadRelationship.update_forward_refs()
UploadRelationship.update_forward_refs()
DownloadHistory.update_forward_refs()
DownloadDataFile.update_forward_refs()
UploadDataFile.update_forward_refs()
DownloadInstrument.update_forward_refs()
DownloadSample.update_forward_refs()
UploadSample.update_forward_refs()
DownloadDataset.update_forward_refs()
UploadDerivedDataset.update_forward_refs()
UploadRawDataset.update_forward_refs()
