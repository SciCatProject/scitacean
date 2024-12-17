##########################################
# This file was automatically generated. #
# Do not modify it directly!             #
##########################################

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)
# flake8: noqa

"""Base class for Dataset."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal, TypeVar

import dateutil.parser

from ._base_model import DatasetType
from .datablock import OrigDatablock
from .filesystem import RemotePath
from .model import (
    construct,
    Attachment,
    BaseModel,
    BaseUserModel,
    DownloadDataset,
    DownloadLifecycle,
    Lifecycle,
    Relationship,
    Technique,
)
from .pid import PID


M = TypeVar("M", bound=BaseModel)


def _parse_datetime(x: datetime | str | None) -> datetime | None:
    if isinstance(x, datetime) or x is None:
        return x
    if x == "now":
        return datetime.now(tz=timezone.utc)
    return dateutil.parser.parse(x)


def _parse_pid(pid: str | PID | None) -> PID | None:
    if pid is None:
        return pid
    return PID.parse(pid)


def _parse_remote_path(path: str | RemotePath | None) -> RemotePath | None:
    if path is None:
        return path
    return RemotePath(path)


def _validate_checksum_algorithm(algorithm: str | None) -> str | None:
    if algorithm is None:
        return algorithm
    import hashlib

    if algorithm not in hashlib.algorithms_available:
        raise ValueError(f"Checksum algorithm not recognized: {algorithm}")
    return algorithm


class DatasetBase:
    @dataclass(frozen=True, kw_only=True, slots=True)
    class Field:
        name: str
        description: str
        read_only: bool
        required: bool
        scicat_name: str
        type: type
        used_by_derived: bool
        used_by_raw: bool

        def used_by(self, dataset_type: DatasetType) -> bool:
            return (
                self.used_by_raw
                if dataset_type == DatasetType.RAW
                else self.used_by_derived
            )

    _FIELD_SPEC = [
        Field(
            name="type",
            description="Characterize type of dataset, either 'raw' or 'derived'. Autofilled when choosing the proper inherited models.",
            read_only=False,
            required=True,
            scicat_name="type",
            type=DatasetType,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="access_groups",
            description="Optional additional groups which have read access to the data. Users which are members in one of the groups listed here are allowed to access this data. The special group 'public' makes data available to all users.",
            read_only=False,
            required=False,
            scicat_name="accessGroups",
            type=list[str],
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="api_version",
            description="Version of the API used when the dataset was created or last updated. API version is defined in code for each release. Managed by the system.",
            read_only=True,
            required=False,
            scicat_name="version",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="classification",
            description="ACIA information about AUthenticity,COnfidentiality,INtegrity and AVailability requirements of dataset. E.g. AV(ailabilty)=medium could trigger the creation of a two tape copies. Format 'AV=medium,CO=low'. Please check the following post for more info: https://en.wikipedia.org/wiki/Parkerian_Hexad",
            read_only=False,
            required=False,
            scicat_name="classification",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="comment",
            description="Short comment provided by the user about a given dataset. This is additional to the description field.",
            read_only=False,
            required=False,
            scicat_name="comment",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="contact_email",
            description="Email of the contact person for this dataset. The string may contain a list of emails, which should then be separated by semicolons.",
            read_only=False,
            required=True,
            scicat_name="contactEmail",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="created_at",
            description="Date and time when this record was created. This field is managed by mongoose with through the timestamp settings. The field should be a string containing a date in ISO 8601 format (2024-02-27T12:26:57.313Z)",
            read_only=True,
            required=False,
            scicat_name="createdAt",
            type=datetime,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="created_by",
            description="Indicate the user who created this record. This property is added and maintained by the system.",
            read_only=True,
            required=False,
            scicat_name="createdBy",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="creation_location",
            description="Unique location identifier where data was acquired. Usually in the form /Site-name/facility-name/instrumentOrBeamline-name.",
            read_only=False,
            required=True,
            scicat_name="creationLocation",
            type=str,
            used_by_derived=False,
            used_by_raw=True,
        ),
        Field(
            name="creation_time",
            description="Time when dataset became fully available on disk, i.e. all containing files have been written,  or the dataset was created in SciCat.<br>It is expected to be in ISO8601 format according to specifications for internet date/time format in RFC 3339, chapter 5.6 (https://www.rfc-editor.org/rfc/rfc3339#section-5).<br>Local times without timezone/offset info are automatically transformed to UTC using the timezone of the API server.",
            read_only=False,
            required=True,
            scicat_name="creationTime",
            type=datetime,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="data_format",
            description="Defines the format of the data files in this dataset, e.g Nexus Version x.y.",
            read_only=False,
            required=False,
            scicat_name="dataFormat",
            type=str,
            used_by_derived=False,
            used_by_raw=True,
        ),
        Field(
            name="data_quality_metrics",
            description="Data Quality Metrics given by the user to rate the dataset.",
            read_only=False,
            required=False,
            scicat_name="dataQualityMetrics",
            type=int,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="description",
            description="Free text explanation of contents of dataset.",
            read_only=False,
            required=False,
            scicat_name="description",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="end_time",
            description="End time of data acquisition for the current dataset.<br>It is expected to be in ISO8601 format according to specifications for internet date/time format in RFC 3339, chapter 5.6 (https://www.rfc-editor.org/rfc/rfc3339#section-5).<br>Local times without timezone/offset info are automatically transformed to UTC using the timezone of the API server.",
            read_only=False,
            required=False,
            scicat_name="endTime",
            type=datetime,
            used_by_derived=False,
            used_by_raw=True,
        ),
        Field(
            name="input_datasets",
            description="Array of input dataset identifiers used in producing the derived dataset. Ideally these are the global identifier to existing datasets inside this or federated data catalogs.",
            read_only=False,
            required=True,
            scicat_name="inputDatasets",
            type=list[PID],
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="instrument_group",
            description="Optional additional groups which have read and write access to the data. Users which are members in one of the groups listed here are allowed to access this data.",
            read_only=False,
            required=False,
            scicat_name="instrumentGroup",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="instrument_id",
            description="ID of the instrument where the data was created.",
            read_only=False,
            required=False,
            scicat_name="instrumentId",
            type=str,
            used_by_derived=False,
            used_by_raw=True,
        ),
        Field(
            name="instrument_ids",
            description="Id of the instrument or array of IDS of the instruments where the data contained in this dataset was created/acquired.",
            read_only=True,
            required=False,
            scicat_name="instrumentIds",
            type=list[str],
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="investigator",
            description="",
            read_only=False,
            required=True,
            scicat_name="investigator",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="is_published",
            description="Flag is true when data are made publicly available.",
            read_only=False,
            required=False,
            scicat_name="isPublished",
            type=bool,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="job_log_data",
            description="The output job logfile. Keep the size of this log data well below 15 MB.",
            read_only=False,
            required=False,
            scicat_name="jobLogData",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="job_parameters",
            description="The creation process of the derived data will usually depend on input job parameters. The full structure of these input parameters are stored here.",
            read_only=False,
            required=False,
            scicat_name="jobParameters",
            type=dict[str, Any],
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="keywords",
            description="Array of tags associated with the meaning or contents of this dataset. Values should ideally come from defined vocabularies, taxonomies, ontologies or knowledge graphs.",
            read_only=False,
            required=False,
            scicat_name="keywords",
            type=list[str],
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="license",
            description="Name of the license under which the data can be used.",
            read_only=False,
            required=False,
            scicat_name="license",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="lifecycle",
            description="Describes the current status of the dataset during its lifetime with respect to the storage handling systems.",
            read_only=True,
            required=False,
            scicat_name="datasetlifecycle",
            type=Lifecycle,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="name",
            description="A name for the dataset, given by the creator to carry some semantic meaning. Useful for display purposes e.g. instead of displaying the pid.",
            read_only=False,
            required=True,
            scicat_name="datasetName",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="orcid_of_owner",
            description="ORCID of the owner or custodian. The string may contain a list of ORCIDs, which should then be separated by semicolons.",
            read_only=False,
            required=False,
            scicat_name="orcidOfOwner",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="owner",
            description="Owner or custodian of the dataset, usually first name + last name. The string may contain a list of persons, which should then be separated by semicolons.",
            read_only=False,
            required=True,
            scicat_name="owner",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="owner_email",
            description="Email of the owner or custodian of the dataset. The string may contain a list of emails, which should then be separated by semicolons.",
            read_only=False,
            required=False,
            scicat_name="ownerEmail",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="owner_group",
            description="Defines the group which owns the data, and therefore has unrestricted access to this data. Usually a pgroup like p12151",
            read_only=False,
            required=True,
            scicat_name="ownerGroup",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="pid",
            description="Persistent Identifier for datasets derived from UUIDv4 and prepended automatically by site specific PID prefix like 20.500.12345/",
            read_only=True,
            required=False,
            scicat_name="pid",
            type=PID,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="principal_investigator",
            description="First name and last name of principal investigator(s). If multiple PIs are present, use a semicolon separated list. This field is required if the dataset is a Raw dataset.",
            read_only=False,
            required=True,
            scicat_name="principalInvestigator",
            type=str,
            used_by_derived=False,
            used_by_raw=True,
        ),
        Field(
            name="proposal_id",
            description="The ID of the proposal to which the dataset belongs.",
            read_only=False,
            required=False,
            scicat_name="proposalId",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="proposal_ids",
            description="The ID of the proposal to which the dataset belongs to and it has been acquired under.",
            read_only=True,
            required=False,
            scicat_name="proposalIds",
            type=list[str],
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="relationships",
            description="Array of relationships with other datasets. It contains relationship type and destination dataset",
            read_only=False,
            required=False,
            scicat_name="relationships",
            type=list[Relationship],
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="sample_id",
            description="ID of the sample used when collecting the data.",
            read_only=False,
            required=False,
            scicat_name="sampleId",
            type=str,
            used_by_derived=False,
            used_by_raw=True,
        ),
        Field(
            name="sample_ids",
            description="Single ID or array of IDS of the samples used when collecting the data.",
            read_only=True,
            required=False,
            scicat_name="sampleIds",
            type=list[str],
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="shared_with",
            description="List of additional users that the dataset has been shared with.",
            read_only=False,
            required=False,
            scicat_name="sharedWith",
            type=list[str],
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="source_folder",
            description="Absolute file path on file server containing the files of this dataset, e.g. /some/path/to/sourcefolder. In case of a single file dataset, e.g. HDF5 data, it contains the path up to, but excluding the filename. Trailing slashes are removed.",
            read_only=False,
            required=True,
            scicat_name="sourceFolder",
            type=RemotePath,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="source_folder_host",
            description="DNS host name of file server hosting sourceFolder, optionally including a protocol e.g. [protocol://]fileserver1.example.com",
            read_only=False,
            required=False,
            scicat_name="sourceFolderHost",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="start_time",
            description="Start time of data acquisition for the current dataset.<br>It is expected to be in ISO8601 format according to specifications for internet date/time format in RFC 3339, chapter 5.6 (https://www.rfc-editor.org/rfc/rfc3339#section-5).<br>Local times without timezone/offset info are automatically transformed to UTC using the timezone of the API server.",
            read_only=False,
            required=False,
            scicat_name="startTime",
            type=datetime,
            used_by_derived=False,
            used_by_raw=True,
        ),
        Field(
            name="techniques",
            description="Array of techniques information, with technique name and pid.",
            read_only=False,
            required=False,
            scicat_name="techniques",
            type=list[Technique],
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="updated_at",
            description="Date and time when this record was updated last. This field is managed by mongoose with through the timestamp settings. The field should be a string containing a date in ISO 8601 format (2024-02-27T12:26:57.313Z)",
            read_only=True,
            required=False,
            scicat_name="updatedAt",
            type=datetime,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="updated_by",
            description="Indicate the user who updated this record last. This property is added and maintained by the system.",
            read_only=True,
            required=False,
            scicat_name="updatedBy",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="used_software",
            description="A list of links to software repositories which uniquely identifies the pieces of software, including versions, used for yielding the derived data.",
            read_only=False,
            required=True,
            scicat_name="usedSoftware",
            type=list[str],
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="validation_status",
            description="Defines a level of trust, e.g. a measure of how much data was verified or used by other persons.",
            read_only=False,
            required=False,
            scicat_name="validationStatus",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
    ]

    __slots__ = (
        "_access_groups",
        "_api_version",
        "_classification",
        "_comment",
        "_contact_email",
        "_created_at",
        "_created_by",
        "_creation_location",
        "_creation_time",
        "_data_format",
        "_data_quality_metrics",
        "_description",
        "_end_time",
        "_input_datasets",
        "_instrument_group",
        "_instrument_id",
        "_instrument_ids",
        "_investigator",
        "_is_published",
        "_job_log_data",
        "_job_parameters",
        "_keywords",
        "_license",
        "_lifecycle",
        "_name",
        "_orcid_of_owner",
        "_owner",
        "_owner_email",
        "_owner_group",
        "_pid",
        "_principal_investigator",
        "_proposal_id",
        "_proposal_ids",
        "_relationships",
        "_sample_id",
        "_sample_ids",
        "_shared_with",
        "_source_folder",
        "_source_folder_host",
        "_start_time",
        "_techniques",
        "_updated_at",
        "_updated_by",
        "_used_software",
        "_validation_status",
        "_meta",
        "_type",
        "_default_checksum_algorithm",
        "_orig_datablocks",
        "_attachments",
    )

    def __init__(
        self,
        type: DatasetType | Literal["raw", "derived"],
        access_groups: list[str] | None = None,
        classification: str | None = None,
        comment: str | None = None,
        contact_email: str | None = None,
        creation_location: str | None = None,
        creation_time: str | datetime | None = "now",
        data_format: str | None = None,
        data_quality_metrics: int | None = None,
        description: str | None = None,
        end_time: datetime | None = None,
        input_datasets: list[PID] | None = None,
        instrument_group: str | None = None,
        instrument_id: str | None = None,
        investigator: str | None = None,
        is_published: bool | None = None,
        job_log_data: str | None = None,
        job_parameters: dict[str, Any] | None = None,
        keywords: list[str] | None = None,
        license: str | None = None,
        name: str | None = None,
        orcid_of_owner: str | None = None,
        owner: str | None = None,
        owner_email: str | None = None,
        owner_group: str | None = None,
        principal_investigator: str | None = None,
        proposal_id: str | None = None,
        relationships: list[Relationship] | None = None,
        sample_id: str | None = None,
        shared_with: list[str] | None = None,
        source_folder: RemotePath | str | None = None,
        source_folder_host: str | None = None,
        start_time: datetime | None = None,
        techniques: list[Technique] | None = None,
        used_software: list[str] | None = None,
        validation_status: str | None = None,
        meta: dict[str, Any] | None = None,
        checksum_algorithm: str | None = "blake2b",
    ) -> None:
        self._type = DatasetType(type)
        self._access_groups = access_groups
        self._classification = classification
        self._comment = comment
        self._contact_email = contact_email
        self._creation_location = creation_location
        self._creation_time = _parse_datetime(creation_time)
        self._data_format = data_format
        self._data_quality_metrics = data_quality_metrics
        self._description = description
        self._end_time = end_time
        self._input_datasets = input_datasets
        self._instrument_group = instrument_group
        self._instrument_id = instrument_id
        self._investigator = investigator
        self._is_published = is_published
        self._job_log_data = job_log_data
        self._job_parameters = job_parameters
        self._keywords = keywords
        self._license = license
        self._name = name
        self._orcid_of_owner = orcid_of_owner
        self._owner = owner
        self._owner_email = owner_email
        self._owner_group = owner_group
        self._principal_investigator = principal_investigator
        self._proposal_id = proposal_id
        self._relationships = relationships
        self._sample_id = sample_id
        self._shared_with = shared_with
        self._source_folder = _parse_remote_path(source_folder)
        self._source_folder_host = source_folder_host
        self._start_time = start_time
        self._techniques = techniques
        self._used_software = used_software
        self._validation_status = validation_status
        self._api_version = None
        self._created_at = None
        self._created_by = None
        self._instrument_ids = None
        self._lifecycle = None
        self._pid = None
        self._proposal_ids = None
        self._sample_ids = None
        self._updated_at = None
        self._updated_by = None
        self._meta = meta or {}
        self._default_checksum_algorithm = _validate_checksum_algorithm(
            checksum_algorithm
        )
        self._orig_datablocks: list[OrigDatablock] = []
        self._attachments: list[Attachment] | None = []

    @property
    def access_groups(self) -> list[str] | None:
        """Optional additional groups which have read access to the data. Users which are members in one of the groups listed here are allowed to access this data. The special group 'public' makes data available to all users."""
        return self._access_groups

    @access_groups.setter
    def access_groups(self, access_groups: list[str] | None) -> None:
        """Optional additional groups which have read access to the data. Users which are members in one of the groups listed here are allowed to access this data. The special group 'public' makes data available to all users."""
        self._access_groups = access_groups

    @property
    def api_version(self) -> str | None:
        """Version of the API used when the dataset was created or last updated. API version is defined in code for each release. Managed by the system."""
        return self._api_version

    @property
    def classification(self) -> str | None:
        """ACIA information about AUthenticity,COnfidentiality,INtegrity and AVailability requirements of dataset. E.g. AV(ailabilty)=medium could trigger the creation of a two tape copies. Format 'AV=medium,CO=low'. Please check the following post for more info: https://en.wikipedia.org/wiki/Parkerian_Hexad"""
        return self._classification

    @classification.setter
    def classification(self, classification: str | None) -> None:
        """ACIA information about AUthenticity,COnfidentiality,INtegrity and AVailability requirements of dataset. E.g. AV(ailabilty)=medium could trigger the creation of a two tape copies. Format 'AV=medium,CO=low'. Please check the following post for more info: https://en.wikipedia.org/wiki/Parkerian_Hexad"""
        self._classification = classification

    @property
    def comment(self) -> str | None:
        """Short comment provided by the user about a given dataset. This is additional to the description field."""
        return self._comment

    @comment.setter
    def comment(self, comment: str | None) -> None:
        """Short comment provided by the user about a given dataset. This is additional to the description field."""
        self._comment = comment

    @property
    def contact_email(self) -> str | None:
        """Email of the contact person for this dataset. The string may contain a list of emails, which should then be separated by semicolons."""
        return self._contact_email

    @contact_email.setter
    def contact_email(self, contact_email: str | None) -> None:
        """Email of the contact person for this dataset. The string may contain a list of emails, which should then be separated by semicolons."""
        self._contact_email = contact_email

    @property
    def created_at(self) -> datetime | None:
        """Date and time when this record was created. This field is managed by mongoose with through the timestamp settings. The field should be a string containing a date in ISO 8601 format (2024-02-27T12:26:57.313Z)"""
        return self._created_at

    @property
    def created_by(self) -> str | None:
        """Indicate the user who created this record. This property is added and maintained by the system."""
        return self._created_by

    @property
    def creation_location(self) -> str | None:
        """Unique location identifier where data was acquired. Usually in the form /Site-name/facility-name/instrumentOrBeamline-name."""
        return self._creation_location

    @creation_location.setter
    def creation_location(self, creation_location: str | None) -> None:
        """Unique location identifier where data was acquired. Usually in the form /Site-name/facility-name/instrumentOrBeamline-name."""
        self._creation_location = creation_location

    @property
    def creation_time(self) -> datetime | None:
        """Time when dataset became fully available on disk, i.e. all containing files have been written,  or the dataset was created in SciCat.<br>It is expected to be in ISO8601 format according to specifications for internet date/time format in RFC 3339, chapter 5.6 (https://www.rfc-editor.org/rfc/rfc3339#section-5).<br>Local times without timezone/offset info are automatically transformed to UTC using the timezone of the API server."""
        return self._creation_time

    @creation_time.setter
    def creation_time(self, creation_time: str | datetime | None) -> None:
        """Time when dataset became fully available on disk, i.e. all containing files have been written,  or the dataset was created in SciCat.<br>It is expected to be in ISO8601 format according to specifications for internet date/time format in RFC 3339, chapter 5.6 (https://www.rfc-editor.org/rfc/rfc3339#section-5).<br>Local times without timezone/offset info are automatically transformed to UTC using the timezone of the API server."""
        self._creation_time = _parse_datetime(creation_time)

    @property
    def data_format(self) -> str | None:
        """Defines the format of the data files in this dataset, e.g Nexus Version x.y."""
        return self._data_format

    @data_format.setter
    def data_format(self, data_format: str | None) -> None:
        """Defines the format of the data files in this dataset, e.g Nexus Version x.y."""
        self._data_format = data_format

    @property
    def data_quality_metrics(self) -> int | None:
        """Data Quality Metrics given by the user to rate the dataset."""
        return self._data_quality_metrics

    @data_quality_metrics.setter
    def data_quality_metrics(self, data_quality_metrics: int | None) -> None:
        """Data Quality Metrics given by the user to rate the dataset."""
        self._data_quality_metrics = data_quality_metrics

    @property
    def description(self) -> str | None:
        """Free text explanation of contents of dataset."""
        return self._description

    @description.setter
    def description(self, description: str | None) -> None:
        """Free text explanation of contents of dataset."""
        self._description = description

    @property
    def end_time(self) -> datetime | None:
        """End time of data acquisition for the current dataset.<br>It is expected to be in ISO8601 format according to specifications for internet date/time format in RFC 3339, chapter 5.6 (https://www.rfc-editor.org/rfc/rfc3339#section-5).<br>Local times without timezone/offset info are automatically transformed to UTC using the timezone of the API server."""
        return self._end_time

    @end_time.setter
    def end_time(self, end_time: datetime | None) -> None:
        """End time of data acquisition for the current dataset.<br>It is expected to be in ISO8601 format according to specifications for internet date/time format in RFC 3339, chapter 5.6 (https://www.rfc-editor.org/rfc/rfc3339#section-5).<br>Local times without timezone/offset info are automatically transformed to UTC using the timezone of the API server."""
        self._end_time = end_time

    @property
    def input_datasets(self) -> list[PID] | None:
        """Array of input dataset identifiers used in producing the derived dataset. Ideally these are the global identifier to existing datasets inside this or federated data catalogs."""
        return self._input_datasets

    @input_datasets.setter
    def input_datasets(self, input_datasets: list[PID] | None) -> None:
        """Array of input dataset identifiers used in producing the derived dataset. Ideally these are the global identifier to existing datasets inside this or federated data catalogs."""
        self._input_datasets = input_datasets

    @property
    def instrument_group(self) -> str | None:
        """Optional additional groups which have read and write access to the data. Users which are members in one of the groups listed here are allowed to access this data."""
        return self._instrument_group

    @instrument_group.setter
    def instrument_group(self, instrument_group: str | None) -> None:
        """Optional additional groups which have read and write access to the data. Users which are members in one of the groups listed here are allowed to access this data."""
        self._instrument_group = instrument_group

    @property
    def instrument_id(self) -> str | None:
        """ID of the instrument where the data was created."""
        return self._instrument_id

    @instrument_id.setter
    def instrument_id(self, instrument_id: str | None) -> None:
        """ID of the instrument where the data was created."""
        self._instrument_id = instrument_id

    @property
    def instrument_ids(self) -> list[str] | None:
        """Id of the instrument or array of IDS of the instruments where the data contained in this dataset was created/acquired."""
        return self._instrument_ids

    @property
    def investigator(self) -> str | None:
        """"""
        return self._investigator

    @investigator.setter
    def investigator(self, investigator: str | None) -> None:
        """"""
        self._investigator = investigator

    @property
    def is_published(self) -> bool | None:
        """Flag is true when data are made publicly available."""
        return self._is_published

    @is_published.setter
    def is_published(self, is_published: bool | None) -> None:
        """Flag is true when data are made publicly available."""
        self._is_published = is_published

    @property
    def job_log_data(self) -> str | None:
        """The output job logfile. Keep the size of this log data well below 15 MB."""
        return self._job_log_data

    @job_log_data.setter
    def job_log_data(self, job_log_data: str | None) -> None:
        """The output job logfile. Keep the size of this log data well below 15 MB."""
        self._job_log_data = job_log_data

    @property
    def job_parameters(self) -> dict[str, Any] | None:
        """The creation process of the derived data will usually depend on input job parameters. The full structure of these input parameters are stored here."""
        return self._job_parameters

    @job_parameters.setter
    def job_parameters(self, job_parameters: dict[str, Any] | None) -> None:
        """The creation process of the derived data will usually depend on input job parameters. The full structure of these input parameters are stored here."""
        self._job_parameters = job_parameters

    @property
    def keywords(self) -> list[str] | None:
        """Array of tags associated with the meaning or contents of this dataset. Values should ideally come from defined vocabularies, taxonomies, ontologies or knowledge graphs."""
        return self._keywords

    @keywords.setter
    def keywords(self, keywords: list[str] | None) -> None:
        """Array of tags associated with the meaning or contents of this dataset. Values should ideally come from defined vocabularies, taxonomies, ontologies or knowledge graphs."""
        self._keywords = keywords

    @property
    def license(self) -> str | None:
        """Name of the license under which the data can be used."""
        return self._license

    @license.setter
    def license(self, license: str | None) -> None:
        """Name of the license under which the data can be used."""
        self._license = license

    @property
    def lifecycle(self) -> Lifecycle | None:
        """Describes the current status of the dataset during its lifetime with respect to the storage handling systems."""
        return self._lifecycle

    @property
    def name(self) -> str | None:
        """A name for the dataset, given by the creator to carry some semantic meaning. Useful for display purposes e.g. instead of displaying the pid."""
        return self._name

    @name.setter
    def name(self, name: str | None) -> None:
        """A name for the dataset, given by the creator to carry some semantic meaning. Useful for display purposes e.g. instead of displaying the pid."""
        self._name = name

    @property
    def orcid_of_owner(self) -> str | None:
        """ORCID of the owner or custodian. The string may contain a list of ORCIDs, which should then be separated by semicolons."""
        return self._orcid_of_owner

    @orcid_of_owner.setter
    def orcid_of_owner(self, orcid_of_owner: str | None) -> None:
        """ORCID of the owner or custodian. The string may contain a list of ORCIDs, which should then be separated by semicolons."""
        self._orcid_of_owner = orcid_of_owner

    @property
    def owner(self) -> str | None:
        """Owner or custodian of the dataset, usually first name + last name. The string may contain a list of persons, which should then be separated by semicolons."""
        return self._owner

    @owner.setter
    def owner(self, owner: str | None) -> None:
        """Owner or custodian of the dataset, usually first name + last name. The string may contain a list of persons, which should then be separated by semicolons."""
        self._owner = owner

    @property
    def owner_email(self) -> str | None:
        """Email of the owner or custodian of the dataset. The string may contain a list of emails, which should then be separated by semicolons."""
        return self._owner_email

    @owner_email.setter
    def owner_email(self, owner_email: str | None) -> None:
        """Email of the owner or custodian of the dataset. The string may contain a list of emails, which should then be separated by semicolons."""
        self._owner_email = owner_email

    @property
    def owner_group(self) -> str | None:
        """Defines the group which owns the data, and therefore has unrestricted access to this data. Usually a pgroup like p12151"""
        return self._owner_group

    @owner_group.setter
    def owner_group(self, owner_group: str | None) -> None:
        """Defines the group which owns the data, and therefore has unrestricted access to this data. Usually a pgroup like p12151"""
        self._owner_group = owner_group

    @property
    def pid(self) -> PID | None:
        """Persistent Identifier for datasets derived from UUIDv4 and prepended automatically by site specific PID prefix like 20.500.12345/"""
        return self._pid

    @property
    def principal_investigator(self) -> str | None:
        """First name and last name of principal investigator(s). If multiple PIs are present, use a semicolon separated list. This field is required if the dataset is a Raw dataset."""
        return self._principal_investigator

    @principal_investigator.setter
    def principal_investigator(self, principal_investigator: str | None) -> None:
        """First name and last name of principal investigator(s). If multiple PIs are present, use a semicolon separated list. This field is required if the dataset is a Raw dataset."""
        self._principal_investigator = principal_investigator

    @property
    def proposal_id(self) -> str | None:
        """The ID of the proposal to which the dataset belongs."""
        return self._proposal_id

    @proposal_id.setter
    def proposal_id(self, proposal_id: str | None) -> None:
        """The ID of the proposal to which the dataset belongs."""
        self._proposal_id = proposal_id

    @property
    def proposal_ids(self) -> list[str] | None:
        """The ID of the proposal to which the dataset belongs to and it has been acquired under."""
        return self._proposal_ids

    @property
    def relationships(self) -> list[Relationship] | None:
        """Array of relationships with other datasets. It contains relationship type and destination dataset"""
        return self._relationships

    @relationships.setter
    def relationships(self, relationships: list[Relationship] | None) -> None:
        """Array of relationships with other datasets. It contains relationship type and destination dataset"""
        self._relationships = relationships

    @property
    def sample_id(self) -> str | None:
        """ID of the sample used when collecting the data."""
        return self._sample_id

    @sample_id.setter
    def sample_id(self, sample_id: str | None) -> None:
        """ID of the sample used when collecting the data."""
        self._sample_id = sample_id

    @property
    def sample_ids(self) -> list[str] | None:
        """Single ID or array of IDS of the samples used when collecting the data."""
        return self._sample_ids

    @property
    def shared_with(self) -> list[str] | None:
        """List of additional users that the dataset has been shared with."""
        return self._shared_with

    @shared_with.setter
    def shared_with(self, shared_with: list[str] | None) -> None:
        """List of additional users that the dataset has been shared with."""
        self._shared_with = shared_with

    @property
    def source_folder(self) -> RemotePath | None:
        """Absolute file path on file server containing the files of this dataset, e.g. /some/path/to/sourcefolder. In case of a single file dataset, e.g. HDF5 data, it contains the path up to, but excluding the filename. Trailing slashes are removed."""
        return self._source_folder

    @source_folder.setter
    def source_folder(self, source_folder: RemotePath | str | None) -> None:
        """Absolute file path on file server containing the files of this dataset, e.g. /some/path/to/sourcefolder. In case of a single file dataset, e.g. HDF5 data, it contains the path up to, but excluding the filename. Trailing slashes are removed."""
        self._source_folder = _parse_remote_path(source_folder)

    @property
    def source_folder_host(self) -> str | None:
        """DNS host name of file server hosting sourceFolder, optionally including a protocol e.g. [protocol://]fileserver1.example.com"""
        return self._source_folder_host

    @source_folder_host.setter
    def source_folder_host(self, source_folder_host: str | None) -> None:
        """DNS host name of file server hosting sourceFolder, optionally including a protocol e.g. [protocol://]fileserver1.example.com"""
        self._source_folder_host = source_folder_host

    @property
    def start_time(self) -> datetime | None:
        """Start time of data acquisition for the current dataset.<br>It is expected to be in ISO8601 format according to specifications for internet date/time format in RFC 3339, chapter 5.6 (https://www.rfc-editor.org/rfc/rfc3339#section-5).<br>Local times without timezone/offset info are automatically transformed to UTC using the timezone of the API server."""
        return self._start_time

    @start_time.setter
    def start_time(self, start_time: datetime | None) -> None:
        """Start time of data acquisition for the current dataset.<br>It is expected to be in ISO8601 format according to specifications for internet date/time format in RFC 3339, chapter 5.6 (https://www.rfc-editor.org/rfc/rfc3339#section-5).<br>Local times without timezone/offset info are automatically transformed to UTC using the timezone of the API server."""
        self._start_time = start_time

    @property
    def techniques(self) -> list[Technique] | None:
        """Array of techniques information, with technique name and pid."""
        return self._techniques

    @techniques.setter
    def techniques(self, techniques: list[Technique] | None) -> None:
        """Array of techniques information, with technique name and pid."""
        self._techniques = techniques

    @property
    def updated_at(self) -> datetime | None:
        """Date and time when this record was updated last. This field is managed by mongoose with through the timestamp settings. The field should be a string containing a date in ISO 8601 format (2024-02-27T12:26:57.313Z)"""
        return self._updated_at

    @property
    def updated_by(self) -> str | None:
        """Indicate the user who updated this record last. This property is added and maintained by the system."""
        return self._updated_by

    @property
    def used_software(self) -> list[str] | None:
        """A list of links to software repositories which uniquely identifies the pieces of software, including versions, used for yielding the derived data."""
        return self._used_software

    @used_software.setter
    def used_software(self, used_software: list[str] | None) -> None:
        """A list of links to software repositories which uniquely identifies the pieces of software, including versions, used for yielding the derived data."""
        self._used_software = used_software

    @property
    def validation_status(self) -> str | None:
        """Defines a level of trust, e.g. a measure of how much data was verified or used by other persons."""
        return self._validation_status

    @validation_status.setter
    def validation_status(self, validation_status: str | None) -> None:
        """Defines a level of trust, e.g. a measure of how much data was verified or used by other persons."""
        self._validation_status = validation_status

    @property
    def meta(self) -> dict[str, Any]:
        """Dict of scientific metadata."""
        return self._meta

    @meta.setter
    def meta(self, meta: dict[str, Any]) -> None:
        """Dict of scientific metadata."""
        self._meta = meta

    @property
    def type(self) -> DatasetType:
        """Characterize type of dataset, either 'raw' or 'derived'. Autofilled when choosing the proper inherited models."""
        return self._type

    @staticmethod
    def _prepare_fields_from_download(
        download_model: DownloadDataset,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        init_args = {}
        read_only = {}
        for field in DatasetBase._FIELD_SPEC:
            if field.read_only:
                read_only["_" + field.name] = getattr(download_model, field.scicat_name)
            elif hasattr(
                download_model, field.scicat_name
            ):  # TODO remove condition in API v4
                init_args[field.name] = getattr(download_model, field.scicat_name)

        init_args["meta"] = download_model.scientificMetadata
        _convert_download_fields_in_place(init_args, read_only)

        return init_args, read_only

    @staticmethod
    def _convert_readonly_fields_in_place(read_only: dict[str, Any]) -> None:
        if (pid := read_only.get("_pid")) is not None:
            read_only["_pid"] = _parse_pid(pid)


def _convert_download_fields_in_place(
    init_args: dict[str, Any], read_only: dict[str, Any]
) -> None:
    for mod, key in ((Technique, "techniques"), (Relationship, "relationships")):
        init_args[key] = _list_field_from_download(mod, init_args.get(key))

    DatasetBase._convert_readonly_fields_in_place(read_only)
    if (lifecycle := read_only.get("_lifecycle")) is not None:
        read_only["_lifecycle"] = Lifecycle.from_download_model(
            _as_model(DownloadLifecycle, lifecycle)
        )


def _list_field_from_download(
    mod: type[BaseUserModel], value: list[Any] | None
) -> list[BaseUserModel] | None:
    if value is None:
        return None
    return [
        mod.from_download_model(_as_model(mod.download_model_type(), item))
        for item in value
    ]


# If validation fails, sub models are not converted automatically by Pydantic.
def _as_model(mod: type[M], value: M | dict[str, Any]) -> M:
    if isinstance(value, dict):
        return construct(mod, **value, _strict_validation=False)
    return value
