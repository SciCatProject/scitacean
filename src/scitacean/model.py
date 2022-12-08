##########################################
# This file was automatically generated. #
# Do not modify it directly!             #
##########################################
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen
# flake8: noqa

"""Pydantic models to encode data for communication with SciCat."""

import enum
from datetime import datetime
from typing import Dict, List, Optional

import pydantic

from ._internal.orcid import is_valid_orcid
from .pid import PID


# This can be replaced by StrEnum in Python 3.11+
class DatasetType(str, enum.Enum):
    """Type of Dataset"""

    RAW = "raw"
    DERIVED = "derived"


class BaseModel(pydantic.BaseModel):
    class Config:
        extra = pydantic.Extra.forbid
        json_encoders = {PID: lambda v: str(v)}


class Technique(BaseModel):
    name: str
    pid: str


class MongoQueryable(BaseModel):
    createdAt: Optional[datetime]
    createdBy: Optional[str]
    updatedAt: Optional[datetime]
    updatedBy: Optional[str]


class DatasetLifecycle(BaseModel):
    archivable: Optional[bool]
    archiveRetentionTime: Optional[datetime]
    archiveReturnMessage: Optional[str]
    archiveStatusMessage: Optional[str]
    dateOfDiskPurging: Optional[datetime]
    dateOfPublishing: Optional[datetime]
    exportedTo: Optional[str]
    isOnCentralDisk: Optional[bool]
    publishable: Optional[bool]
    publishedOn: Optional[datetime]
    retrievable: Optional[bool]
    retrieveIntegrityCheck: Optional[bool]
    retrieveReturnMessage: Optional[str]
    retrieveStatusMessage: Optional[str]


class DataFile(MongoQueryable):
    path: str
    size: int
    chk: Optional[str]
    gid: Optional[str]
    perm: Optional[str]
    time: Optional[datetime]
    uid: Optional[str]

    @pydantic.validator("size")
    def _validate_size(cls, value):
        return _validate_size(value)


class Ownable(MongoQueryable):
    ownerGroup: str
    accessGroups: Optional[List[str]]
    instrumentGroup: Optional[str]


class Datablock(Ownable):
    archiveId: str
    dataFileList: List[DataFile]
    size: int
    version: str
    chkAlg: Optional[str]
    datasetId: Optional[str]
    packedSize: Optional[int]
    id: Optional[str]

    @pydantic.validator("size", "packedSize")
    def _validate_size(cls, value):
        return _validate_size(value)


class OrigDatablock(Ownable):
    dataFileList: List[DataFile]
    size: int
    datasetId: Optional[PID]
    id: Optional[PID]

    @pydantic.validator("size")
    def _validate_size(cls, value):
        return _validate_size(value)


class DerivedDataset(Ownable):
    contactEmail: str
    creationTime: datetime
    inputDatasets: List[PID]
    investigator: str
    owner: str
    sourceFolder: str
    type: DatasetType
    usedSoftware: List[str]
    classification: Optional[str]
    description: Optional[str]
    history: Optional[List[dict]]
    instrumentId: Optional[str]
    isPublished: Optional[bool]
    jobLogData: Optional[str]
    jobParameters: Optional[dict]
    keywords: Optional[List[str]]
    license: Optional[str]
    datasetlifecycle: Optional[DatasetLifecycle]
    scientificMetadata: Optional[Dict]
    datasetName: Optional[str]
    numberOfFiles: Optional[int]
    numberOfFilesArchived: Optional[int]
    orcidOfOwner: Optional[str]
    ownerEmail: Optional[str]
    packedSize: Optional[int]
    pid: Optional[PID]
    sharedWith: Optional[List[str]]
    size: Optional[int]
    sourceFolderHost: Optional[str]
    techniques: Optional[List[Technique]]
    validationStatus: Optional[str]
    version: Optional[str]

    @pydantic.validator("contactEmail", "investigator", "ownerEmail")
    def _validate_emails(cls, value):
        return _validate_emails(value)

    @pydantic.validator("numberOfFiles", "numberOfFilesArchived", "packedSize", "size")
    def _validate_size(cls, value):
        return _validate_size(value)

    @pydantic.validator("orcidOfOwner")
    def _validate_orcid(cls, value):
        return _validate_orcid(value)


class RawDataset(Ownable):
    contactEmail: str
    creationTime: datetime
    principalInvestigator: str
    owner: str
    sourceFolder: str
    type: DatasetType
    classification: Optional[str]
    creationLocation: Optional[str]
    dataFormat: Optional[str]
    description: Optional[str]
    endTime: Optional[datetime]
    history: Optional[List[dict]]
    instrumentId: Optional[str]
    isPublished: Optional[bool]
    keywords: Optional[List[str]]
    license: Optional[str]
    datasetlifecycle: Optional[DatasetLifecycle]
    scientificMetadata: Optional[Dict]
    datasetName: Optional[str]
    numberOfFiles: Optional[int]
    numberOfFilesArchived: Optional[int]
    orcidOfOwner: Optional[str]
    ownerEmail: Optional[str]
    packedSize: Optional[int]
    pid: Optional[PID]
    proposalId: Optional[str]
    sampleId: Optional[str]
    sharedWith: Optional[List[str]]
    size: Optional[int]
    sourceFolderHost: Optional[str]
    techniques: Optional[List[Technique]]
    validationStatus: Optional[str]
    version: Optional[str]

    @pydantic.validator("contactEmail", "principalInvestigator", "ownerEmail")
    def _validate_emails(cls, value):
        return _validate_emails(value)

    @pydantic.validator("numberOfFiles", "numberOfFilesArchived", "packedSize", "size")
    def _validate_size(cls, value):
        return _validate_size(value)

    @pydantic.validator("orcidOfOwner")
    def _validate_orcid(cls, value):
        return _validate_orcid(value)


def _validate_emails(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    return ";".join(pydantic.EmailStr.validate(item) for item in value.split(";"))


def _validate_size(value: Optional[int]) -> Optional[int]:
    if value is None:
        return value
    if value < 0:
        raise ValueError("Must be > 0")
    return value


def _validate_orcid(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    try:
        if is_valid_orcid(value):
            return value
    except (RuntimeError, ValueError, TypeError):
        pass
    raise ValueError(
        "value is not a valid ORCID, "
        "note that ORCIDs must be prefixed with 'https://orcid.org'."
    )
