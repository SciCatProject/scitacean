##########################################
# This file was automatically generated. #
# Do not modify it directly!             #
##########################################
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen
# flake8: noqa

"""Pydantic models to encode data for communication with SciCat."""

from datetime import datetime
import enum
from typing import Dict, List, Optional

import pydantic

from ._internal.orcid import is_valid_orcid


# This can be replaced by StrEnum in Python 3.11+
class DatasetType(str, enum.Enum):
    """Type of Dataset"""

    RAW = "raw"
    DERIVED = "derived"


class BaseModel(pydantic.BaseModel):
    class Config:
        extra = pydantic.Extra.forbid


class DerivedDataset(BaseModel):
    accessGroups: Optional[List[str]]
    classification: Optional[str]
    contactEmail: str
    createdAt: Optional[datetime]
    createdBy: Optional[str]
    creationTime: datetime
    datasetName: Optional[str]
    description: Optional[str]
    history: Optional[List[dict]]
    inputDatasets: List[str]
    instrumentGroup: Optional[str]
    instrumentId: Optional[str]
    investigator: str
    isPublished: Optional[bool]
    jobLogData: Optional[str]
    jobParameters: Optional[dict]
    keywords: Optional[List[str]]
    license: Optional[str]
    numberOfFiles: Optional[int]
    numberOfFilesArchived: Optional[int]
    orcidOfOwner: Optional[str]
    owner: str
    ownerEmail: Optional[str]
    ownerGroup: str
    packedSize: Optional[int]
    pid: Optional[str]
    scientificMetadata: Optional[Dict]
    sharedWith: Optional[List[str]]
    size: Optional[int]
    sourceFolder: str
    sourceFolderHost: Optional[str]
    techniques: Optional[List[dict]]
    type: DatasetType
    updatedAt: Optional[datetime]
    updatedBy: Optional[str]
    usedSoftware: List[str]
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


class RawDataset(BaseModel):
    accessGroups: Optional[List[str]]
    classification: Optional[str]
    contactEmail: str
    createdAt: Optional[datetime]
    createdBy: Optional[str]
    creationLocation: Optional[str]
    creationTime: datetime
    dataFormat: Optional[str]
    datasetName: Optional[str]
    description: Optional[str]
    endTime: Optional[datetime]
    history: Optional[List[dict]]
    instrumentGroup: Optional[str]
    instrumentId: Optional[str]
    isPublished: Optional[bool]
    keywords: Optional[List[str]]
    license: Optional[str]
    numberOfFiles: Optional[int]
    numberOfFilesArchived: Optional[int]
    orcidOfOwner: Optional[str]
    owner: str
    ownerEmail: Optional[str]
    ownerGroup: str
    packedSize: Optional[int]
    pid: Optional[str]
    principalInvestigator: str
    proposalID: Optional[str]
    sampleID: Optional[str]
    scientificMetadata: Optional[Dict]
    sharedWith: Optional[List[str]]
    size: Optional[int]
    sourceFolder: str
    sourceFolderHost: Optional[str]
    techniques: Optional[List[dict]]
    type: DatasetType
    updatedAt: Optional[datetime]
    updatedBy: Optional[str]
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
