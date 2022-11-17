##########################################
# This file was automatically generated. #
# Do not modify it directly!             #
##########################################
# flake8: noqa

"""Pydantic models to encode data for communication with SciCat."""

from datetime import datetime
import enum
from typing import Dict, List, Optional

import pydantic

from .pid import PID


# This can be replaced by StrEnum in Python 3.11+
class DatasetType(str, enum.Enum):
    """Type of Dataset"""

    RAW = "raw"
    DERIVED = "derived"


class DerivedDataset(pydantic.BaseModel):
    access_groups: Optional[List[str]]
    classification: Optional[str]
    contact_email: str
    created_at: Optional[str]
    created_by: Optional[str]
    creation_location: Optional[str]
    creation_time: datetime
    data_format: str
    description: Optional[str]
    end_time: Optional[datetime]
    history: Optional[List[dict]]
    input_datasets: List[str]
    instrument_group: Optional[str]
    instrument_id: Optional[str]
    investigator: str
    is_published: Optional[bool]
    job_log_data: Optional[str]
    job_parameters: Optional[dict]
    keywords: Optional[List[str]]
    license: Optional[str]
    meta: Optional[Dict]
    name: Optional[str]
    number_of_files: Optional[int]
    number_of_files_archived: Optional[int]
    orcid_of_owner: Optional[str]
    owner: str
    owner_email: Optional[str]
    owner_group: str
    packed_size: Optional[int]
    pid: Optional[str]
    proposal_id: Optional[str]
    sample_id: Optional[str]
    shared_with: Optional[List[str]]
    size: Optional[int]
    source_folder: str
    source_folder_host: Optional[str]
    techniques: Optional[List[dict]]
    type: DatasetType
    updated_at: Optional[str]
    updated_by: Optional[str]
    used_software: List[str]
    validation_status: Optional[str]
    version: Optional[str]


class RawDataset(pydantic.BaseModel):
    access_groups: Optional[List[str]]
    classification: Optional[str]
    contact_email: str
    created_at: Optional[str]
    created_by: Optional[str]
    creation_location: Optional[str]
    creation_time: datetime
    data_format: str
    description: Optional[str]
    end_time: Optional[datetime]
    history: Optional[List[dict]]
    input_datasets: List[str]
    instrument_group: Optional[str]
    instrument_id: Optional[str]
    investigator: str
    is_published: Optional[bool]
    job_log_data: Optional[str]
    job_parameters: Optional[dict]
    keywords: Optional[List[str]]
    license: Optional[str]
    meta: Optional[Dict]
    name: Optional[str]
    number_of_files: Optional[int]
    number_of_files_archived: Optional[int]
    orcid_of_owner: Optional[str]
    owner: str
    owner_email: Optional[str]
    owner_group: str
    packed_size: Optional[int]
    pid: Optional[str]
    proposal_id: Optional[str]
    sample_id: Optional[str]
    shared_with: Optional[List[str]]
    size: Optional[int]
    source_folder: str
    source_folder_host: Optional[str]
    techniques: Optional[List[dict]]
    type: DatasetType
    updated_at: Optional[str]
    updated_by: Optional[str]
    used_software: List[str]
    validation_status: Optional[str]
    version: Optional[str]
