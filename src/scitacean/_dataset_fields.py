##########################################
# This file was automatically generated. #
# Do not modify it directly!             #
##########################################

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
# flake8: noqa

"""Base class for Dataset."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

import dateutil.parser

from ._internal.dataclass_wrapper import dataclass_optional_args
from .datablock import OrigDatablock
from .filesystem import RemotePath
from .model import (
    DatasetType,
    DownloadDataset,
    Lifecycle,
    History,
    Relationship,
    Technique,
)
from .pid import PID


def _parse_datetime(x: Optional[Union[datetime, str]]) -> Optional[datetime]:
    if isinstance(x, datetime) or x is None:
        return x
    if x == "now":
        return datetime.now(tz=timezone.utc)
    return dateutil.parser.parse(x)


def _parse_pid(pid: Optional[Union[str, PID]]) -> Optional[PID]:
    if pid is None:
        return pid
    return PID.parse(pid)


def _parse_remote_path(path: Optional[Union[str, RemotePath]]) -> Optional[RemotePath]:
    if path is None:
        return path
    return RemotePath(path)


def _validate_checksum_algorithm(algorithm: Optional[str]) -> Optional[str]:
    if algorithm is None:
        return algorithm
    import hashlib

    if algorithm not in hashlib.algorithms_available:
        raise ValueError(f"Checksum algorithm not recognized: {algorithm}")
    return algorithm


class DatasetBase:
    @dataclass_optional_args(frozen=True, kw_only=True, slots=True)
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
            name="access_groups",
            description="Optional additional groups which have read access to the data. Users which are members in one of the groups listed here are allowed to access this data. The special group 'public' makes data available to all users.",
            read_only=False,
            required=False,
            scicat_name="accessGroups",
            type=List[str],
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="api_version",
            description="Version of the API used in creation of the dataset.",
            read_only=True,
            required=False,
            scicat_name="version",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="classification",
            description="ACIA information about AUthenticity,COnfidentiality,INtegrity and AVailability requirements of dataset. E.g. AV(ailabilty)=medium could trigger the creation of a two tape copies. Format 'AV=medium,CO=low'",
            read_only=False,
            required=False,
            scicat_name="classification",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="comment",
            description="Comment the user has about a given dataset.",
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
            description="Date and time when this record was created. This property is added and maintained by mongoose.",
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
            description="Unique location identifier where data was taken, usually in the form /Site-name/facility-name/instrumentOrBeamline-name. This field is required if the dataset is a Raw dataset.",
            read_only=False,
            required=True,
            scicat_name="creationLocation",
            type=str,
            used_by_derived=False,
            used_by_raw=True,
        ),
        Field(
            name="creation_time",
            description="Time when dataset became fully available on disk, i.e. all containing files have been written. Format according to chapter 5.6 internet date/time format in RFC 3339. Local times without timezone/offset info are automatically transformed to UTC using the timezone of the API server.",
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
            description="End time of data acquisition for this dataset, format according to chapter 5.6 internet date/time format in RFC 3339. Local times without timezone/offset info are automatically transformed to UTC using the timezone of the API server.",
            read_only=False,
            required=False,
            scicat_name="endTime",
            type=datetime,
            used_by_derived=False,
            used_by_raw=True,
        ),
        Field(
            name="history",
            description="List of objects containing old and new values.",
            read_only=True,
            required=False,
            scicat_name="history",
            type=None,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="input_datasets",
            description="Array of input dataset identifiers used in producing the derived dataset. Ideally these are the global identifier to existing datasets inside this or federated data catalogs. This field is required if the dataset is a Derived dataset.",
            read_only=False,
            required=True,
            scicat_name="inputDatasets",
            type=List[PID],
            used_by_derived=True,
            used_by_raw=False,
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
            name="investigator",
            description="First name and last name of the person or people pursuing the data analysis. The string may contain a list of names, which should then be separated by semicolons.",
            read_only=False,
            required=True,
            scicat_name="investigator",
            type=str,
            used_by_derived=True,
            used_by_raw=False,
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
            used_by_raw=False,
        ),
        Field(
            name="job_parameters",
            description="The creation process of the derived data will usually depend on input job parameters. The full structure of these input parameters are stored here.",
            read_only=False,
            required=False,
            scicat_name="jobParameters",
            type=Dict[str, Any],
            used_by_derived=True,
            used_by_raw=False,
        ),
        Field(
            name="keywords",
            description="Array of tags associated with the meaning or contents of this dataset. Values should ideally come from defined vocabularies, taxonomies, ontologies or knowledge graphs.",
            read_only=False,
            required=False,
            scicat_name="keywords",
            type=List[str],
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
            description="A name for the dataset, given by the creator to carry some semantic meaning. Useful for display purposes e.g. instead of displaying the pid. Will be autofilled if missing using info from sourceFolder.",
            read_only=False,
            required=False,
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
            used_by_derived=False,
            used_by_raw=True,
        ),
        Field(
            name="relationships",
            description="Stores the relationships with other datasets.",
            read_only=False,
            required=False,
            scicat_name="relationships",
            type=List[Relationship],
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
            name="shared_with",
            description="List of users that the dataset has been shared with.",
            read_only=False,
            required=False,
            scicat_name="sharedWith",
            type=List[str],
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
            name="techniques",
            description="Stores the metadata information for techniques.",
            read_only=False,
            required=False,
            scicat_name="techniques",
            type=List[Technique],
            used_by_derived=True,
            used_by_raw=True,
        ),
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
            name="updated_at",
            description="Date and time when this record was updated last. This property is added and maintained by mongoose.",
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
            description="A list of links to software repositories which uniquely identifies the pieces of software, including versions, used for yielding the derived data. This field is required if the dataset is a Derived dataset.",
            read_only=False,
            required=True,
            scicat_name="usedSoftware",
            type=List[str],
            used_by_derived=True,
            used_by_raw=False,
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
        "_history",
        "_input_datasets",
        "_instrument_group",
        "_instrument_id",
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
        "_relationships",
        "_sample_id",
        "_shared_with",
        "_source_folder",
        "_source_folder_host",
        "_techniques",
        "_type",
        "_updated_at",
        "_updated_by",
        "_used_software",
        "_validation_status",
        "_meta",
        "_default_checksum_algorithm",
        "_orig_datablocks",
    )

    def __init__(
        self,
        type: Union[DatasetType, Literal["raw", "derived"]],
        access_groups: Optional[List[str]] = None,
        classification: Optional[str] = None,
        comment: Optional[str] = None,
        contact_email: Optional[str] = None,
        creation_location: Optional[str] = None,
        creation_time: Optional[Union[str, datetime]] = "now",
        data_format: Optional[str] = None,
        data_quality_metrics: Optional[int] = None,
        description: Optional[str] = None,
        end_time: Optional[datetime] = None,
        input_datasets: Optional[List[PID]] = None,
        instrument_group: Optional[str] = None,
        instrument_id: Optional[str] = None,
        investigator: Optional[str] = None,
        is_published: Optional[bool] = None,
        job_log_data: Optional[str] = None,
        job_parameters: Optional[Dict[str, Any]] = None,
        keywords: Optional[List[str]] = None,
        license: Optional[str] = None,
        name: Optional[str] = None,
        orcid_of_owner: Optional[str] = None,
        owner: Optional[str] = None,
        owner_email: Optional[str] = None,
        owner_group: Optional[str] = None,
        principal_investigator: Optional[str] = None,
        proposal_id: Optional[str] = None,
        relationships: Optional[List[Relationship]] = None,
        sample_id: Optional[str] = None,
        shared_with: Optional[List[str]] = None,
        source_folder: Optional[Union[RemotePath, str]] = None,
        source_folder_host: Optional[str] = None,
        techniques: Optional[List[Technique]] = None,
        used_software: Optional[List[str]] = None,
        validation_status: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
        checksum_algorithm: Optional[str] = "blake2b",
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
        self._techniques = techniques
        self._used_software = used_software
        self._validation_status = validation_status
        self._api_version = None
        self._created_at = None
        self._created_by = None
        self._history = None
        self._lifecycle = None
        self._pid = None
        self._updated_at = None
        self._updated_by = None
        self._meta = meta or {}
        self._default_checksum_algorithm = _validate_checksum_algorithm(
            checksum_algorithm
        )
        self._orig_datablocks: List[OrigDatablock] = []

    @property
    def access_groups(self) -> Optional[List[str]]:
        """Optional additional groups which have read access to the data. Users which are members in one of the groups listed here are allowed to access this data. The special group 'public' makes data available to all users."""
        return self._access_groups

    @access_groups.setter
    def access_groups(self, access_groups: Optional[List[str]]) -> None:
        """Optional additional groups which have read access to the data. Users which are members in one of the groups listed here are allowed to access this data. The special group 'public' makes data available to all users."""
        self._access_groups = access_groups

    @property
    def api_version(self) -> Optional[str]:
        """Version of the API used in creation of the dataset."""
        return self._api_version

    @property
    def classification(self) -> Optional[str]:
        """ACIA information about AUthenticity,COnfidentiality,INtegrity and AVailability requirements of dataset. E.g. AV(ailabilty)=medium could trigger the creation of a two tape copies. Format 'AV=medium,CO=low'"""
        return self._classification

    @classification.setter
    def classification(self, classification: Optional[str]) -> None:
        """ACIA information about AUthenticity,COnfidentiality,INtegrity and AVailability requirements of dataset. E.g. AV(ailabilty)=medium could trigger the creation of a two tape copies. Format 'AV=medium,CO=low'"""
        self._classification = classification

    @property
    def comment(self) -> Optional[str]:
        """Comment the user has about a given dataset."""
        return self._comment

    @comment.setter
    def comment(self, comment: Optional[str]) -> None:
        """Comment the user has about a given dataset."""
        self._comment = comment

    @property
    def contact_email(self) -> Optional[str]:
        """Email of the contact person for this dataset. The string may contain a list of emails, which should then be separated by semicolons."""
        return self._contact_email

    @contact_email.setter
    def contact_email(self, contact_email: Optional[str]) -> None:
        """Email of the contact person for this dataset. The string may contain a list of emails, which should then be separated by semicolons."""
        self._contact_email = contact_email

    @property
    def created_at(self) -> Optional[datetime]:
        """Date and time when this record was created. This property is added and maintained by mongoose."""
        return self._created_at

    @property
    def created_by(self) -> Optional[str]:
        """Indicate the user who created this record. This property is added and maintained by the system."""
        return self._created_by

    @property
    def creation_location(self) -> Optional[str]:
        """Unique location identifier where data was taken, usually in the form /Site-name/facility-name/instrumentOrBeamline-name. This field is required if the dataset is a Raw dataset."""
        return self._creation_location

    @creation_location.setter
    def creation_location(self, creation_location: Optional[str]) -> None:
        """Unique location identifier where data was taken, usually in the form /Site-name/facility-name/instrumentOrBeamline-name. This field is required if the dataset is a Raw dataset."""
        self._creation_location = creation_location

    @property
    def creation_time(self) -> Optional[datetime]:
        """Time when dataset became fully available on disk, i.e. all containing files have been written. Format according to chapter 5.6 internet date/time format in RFC 3339. Local times without timezone/offset info are automatically transformed to UTC using the timezone of the API server."""
        return self._creation_time

    @creation_time.setter
    def creation_time(self, creation_time: Optional[Union[str, datetime]]) -> None:
        """Time when dataset became fully available on disk, i.e. all containing files have been written. Format according to chapter 5.6 internet date/time format in RFC 3339. Local times without timezone/offset info are automatically transformed to UTC using the timezone of the API server."""
        self._creation_time = _parse_datetime(creation_time)

    @property
    def data_format(self) -> Optional[str]:
        """Defines the format of the data files in this dataset, e.g Nexus Version x.y."""
        return self._data_format

    @data_format.setter
    def data_format(self, data_format: Optional[str]) -> None:
        """Defines the format of the data files in this dataset, e.g Nexus Version x.y."""
        self._data_format = data_format

    @property
    def data_quality_metrics(self) -> Optional[int]:
        """Data Quality Metrics given by the user to rate the dataset."""
        return self._data_quality_metrics

    @data_quality_metrics.setter
    def data_quality_metrics(self, data_quality_metrics: Optional[int]) -> None:
        """Data Quality Metrics given by the user to rate the dataset."""
        self._data_quality_metrics = data_quality_metrics

    @property
    def description(self) -> Optional[str]:
        """Free text explanation of contents of dataset."""
        return self._description

    @description.setter
    def description(self, description: Optional[str]) -> None:
        """Free text explanation of contents of dataset."""
        self._description = description

    @property
    def end_time(self) -> Optional[datetime]:
        """End time of data acquisition for this dataset, format according to chapter 5.6 internet date/time format in RFC 3339. Local times without timezone/offset info are automatically transformed to UTC using the timezone of the API server."""
        return self._end_time

    @end_time.setter
    def end_time(self, end_time: Optional[datetime]) -> None:
        """End time of data acquisition for this dataset, format according to chapter 5.6 internet date/time format in RFC 3339. Local times without timezone/offset info are automatically transformed to UTC using the timezone of the API server."""
        self._end_time = end_time

    @property
    def history(self) -> Optional[None]:
        """List of objects containing old and new values."""
        return self._history

    @property
    def input_datasets(self) -> Optional[List[PID]]:
        """Array of input dataset identifiers used in producing the derived dataset. Ideally these are the global identifier to existing datasets inside this or federated data catalogs. This field is required if the dataset is a Derived dataset."""
        return self._input_datasets

    @input_datasets.setter
    def input_datasets(self, input_datasets: Optional[List[PID]]) -> None:
        """Array of input dataset identifiers used in producing the derived dataset. Ideally these are the global identifier to existing datasets inside this or federated data catalogs. This field is required if the dataset is a Derived dataset."""
        self._input_datasets = input_datasets

    @property
    def instrument_group(self) -> Optional[str]:
        """Optional additional groups which have read and write access to the data. Users which are members in one of the groups listed here are allowed to access this data."""
        return self._instrument_group

    @instrument_group.setter
    def instrument_group(self, instrument_group: Optional[str]) -> None:
        """Optional additional groups which have read and write access to the data. Users which are members in one of the groups listed here are allowed to access this data."""
        self._instrument_group = instrument_group

    @property
    def instrument_id(self) -> Optional[str]:
        """ID of the instrument where the data was created."""
        return self._instrument_id

    @instrument_id.setter
    def instrument_id(self, instrument_id: Optional[str]) -> None:
        """ID of the instrument where the data was created."""
        self._instrument_id = instrument_id

    @property
    def investigator(self) -> Optional[str]:
        """First name and last name of the person or people pursuing the data analysis. The string may contain a list of names, which should then be separated by semicolons."""
        return self._investigator

    @investigator.setter
    def investigator(self, investigator: Optional[str]) -> None:
        """First name and last name of the person or people pursuing the data analysis. The string may contain a list of names, which should then be separated by semicolons."""
        self._investigator = investigator

    @property
    def is_published(self) -> Optional[bool]:
        """Flag is true when data are made publicly available."""
        return self._is_published

    @is_published.setter
    def is_published(self, is_published: Optional[bool]) -> None:
        """Flag is true when data are made publicly available."""
        self._is_published = is_published

    @property
    def job_log_data(self) -> Optional[str]:
        """The output job logfile. Keep the size of this log data well below 15 MB."""
        return self._job_log_data

    @job_log_data.setter
    def job_log_data(self, job_log_data: Optional[str]) -> None:
        """The output job logfile. Keep the size of this log data well below 15 MB."""
        self._job_log_data = job_log_data

    @property
    def job_parameters(self) -> Optional[Dict[str, Any]]:
        """The creation process of the derived data will usually depend on input job parameters. The full structure of these input parameters are stored here."""
        return self._job_parameters

    @job_parameters.setter
    def job_parameters(self, job_parameters: Optional[Dict[str, Any]]) -> None:
        """The creation process of the derived data will usually depend on input job parameters. The full structure of these input parameters are stored here."""
        self._job_parameters = job_parameters

    @property
    def keywords(self) -> Optional[List[str]]:
        """Array of tags associated with the meaning or contents of this dataset. Values should ideally come from defined vocabularies, taxonomies, ontologies or knowledge graphs."""
        return self._keywords

    @keywords.setter
    def keywords(self, keywords: Optional[List[str]]) -> None:
        """Array of tags associated with the meaning or contents of this dataset. Values should ideally come from defined vocabularies, taxonomies, ontologies or knowledge graphs."""
        self._keywords = keywords

    @property
    def license(self) -> Optional[str]:
        """Name of the license under which the data can be used."""
        return self._license

    @license.setter
    def license(self, license: Optional[str]) -> None:
        """Name of the license under which the data can be used."""
        self._license = license

    @property
    def lifecycle(self) -> Optional[Lifecycle]:
        """Describes the current status of the dataset during its lifetime with respect to the storage handling systems."""
        return self._lifecycle

    @property
    def name(self) -> Optional[str]:
        """A name for the dataset, given by the creator to carry some semantic meaning. Useful for display purposes e.g. instead of displaying the pid. Will be autofilled if missing using info from sourceFolder."""
        return self._name

    @name.setter
    def name(self, name: Optional[str]) -> None:
        """A name for the dataset, given by the creator to carry some semantic meaning. Useful for display purposes e.g. instead of displaying the pid. Will be autofilled if missing using info from sourceFolder."""
        self._name = name

    @property
    def orcid_of_owner(self) -> Optional[str]:
        """ORCID of the owner or custodian. The string may contain a list of ORCIDs, which should then be separated by semicolons."""
        return self._orcid_of_owner

    @orcid_of_owner.setter
    def orcid_of_owner(self, orcid_of_owner: Optional[str]) -> None:
        """ORCID of the owner or custodian. The string may contain a list of ORCIDs, which should then be separated by semicolons."""
        self._orcid_of_owner = orcid_of_owner

    @property
    def owner(self) -> Optional[str]:
        """Owner or custodian of the dataset, usually first name + last name. The string may contain a list of persons, which should then be separated by semicolons."""
        return self._owner

    @owner.setter
    def owner(self, owner: Optional[str]) -> None:
        """Owner or custodian of the dataset, usually first name + last name. The string may contain a list of persons, which should then be separated by semicolons."""
        self._owner = owner

    @property
    def owner_email(self) -> Optional[str]:
        """Email of the owner or custodian of the dataset. The string may contain a list of emails, which should then be separated by semicolons."""
        return self._owner_email

    @owner_email.setter
    def owner_email(self, owner_email: Optional[str]) -> None:
        """Email of the owner or custodian of the dataset. The string may contain a list of emails, which should then be separated by semicolons."""
        self._owner_email = owner_email

    @property
    def owner_group(self) -> Optional[str]:
        """Defines the group which owns the data, and therefore has unrestricted access to this data. Usually a pgroup like p12151"""
        return self._owner_group

    @owner_group.setter
    def owner_group(self, owner_group: Optional[str]) -> None:
        """Defines the group which owns the data, and therefore has unrestricted access to this data. Usually a pgroup like p12151"""
        self._owner_group = owner_group

    @property
    def pid(self) -> Optional[PID]:
        """Persistent Identifier for datasets derived from UUIDv4 and prepended automatically by site specific PID prefix like 20.500.12345/"""
        return self._pid

    @property
    def principal_investigator(self) -> Optional[str]:
        """First name and last name of principal investigator(s). If multiple PIs are present, use a semicolon separated list. This field is required if the dataset is a Raw dataset."""
        return self._principal_investigator

    @principal_investigator.setter
    def principal_investigator(self, principal_investigator: Optional[str]) -> None:
        """First name and last name of principal investigator(s). If multiple PIs are present, use a semicolon separated list. This field is required if the dataset is a Raw dataset."""
        self._principal_investigator = principal_investigator

    @property
    def proposal_id(self) -> Optional[str]:
        """The ID of the proposal to which the dataset belongs."""
        return self._proposal_id

    @proposal_id.setter
    def proposal_id(self, proposal_id: Optional[str]) -> None:
        """The ID of the proposal to which the dataset belongs."""
        self._proposal_id = proposal_id

    @property
    def relationships(self) -> Optional[List[Relationship]]:
        """Stores the relationships with other datasets."""
        return self._relationships

    @relationships.setter
    def relationships(self, relationships: Optional[List[Relationship]]) -> None:
        """Stores the relationships with other datasets."""
        self._relationships = relationships

    @property
    def sample_id(self) -> Optional[str]:
        """ID of the sample used when collecting the data."""
        return self._sample_id

    @sample_id.setter
    def sample_id(self, sample_id: Optional[str]) -> None:
        """ID of the sample used when collecting the data."""
        self._sample_id = sample_id

    @property
    def shared_with(self) -> Optional[List[str]]:
        """List of users that the dataset has been shared with."""
        return self._shared_with

    @shared_with.setter
    def shared_with(self, shared_with: Optional[List[str]]) -> None:
        """List of users that the dataset has been shared with."""
        self._shared_with = shared_with

    @property
    def source_folder(self) -> Optional[RemotePath]:
        """Absolute file path on file server containing the files of this dataset, e.g. /some/path/to/sourcefolder. In case of a single file dataset, e.g. HDF5 data, it contains the path up to, but excluding the filename. Trailing slashes are removed."""
        return self._source_folder

    @source_folder.setter
    def source_folder(self, source_folder: Optional[Union[RemotePath, str]]) -> None:
        """Absolute file path on file server containing the files of this dataset, e.g. /some/path/to/sourcefolder. In case of a single file dataset, e.g. HDF5 data, it contains the path up to, but excluding the filename. Trailing slashes are removed."""
        self._source_folder = _parse_remote_path(source_folder)

    @property
    def source_folder_host(self) -> Optional[str]:
        """DNS host name of file server hosting sourceFolder, optionally including a protocol e.g. [protocol://]fileserver1.example.com"""
        return self._source_folder_host

    @source_folder_host.setter
    def source_folder_host(self, source_folder_host: Optional[str]) -> None:
        """DNS host name of file server hosting sourceFolder, optionally including a protocol e.g. [protocol://]fileserver1.example.com"""
        self._source_folder_host = source_folder_host

    @property
    def techniques(self) -> Optional[List[Technique]]:
        """Stores the metadata information for techniques."""
        return self._techniques

    @techniques.setter
    def techniques(self, techniques: Optional[List[Technique]]) -> None:
        """Stores the metadata information for techniques."""
        self._techniques = techniques

    @property
    def type(self) -> Optional[DatasetType]:
        """Characterize type of dataset, either 'raw' or 'derived'. Autofilled when choosing the proper inherited models."""
        return self._type

    @type.setter
    def type(self, type: Optional[DatasetType]) -> None:
        """Characterize type of dataset, either 'raw' or 'derived'. Autofilled when choosing the proper inherited models."""
        self._type = type

    @property
    def updated_at(self) -> Optional[datetime]:
        """Date and time when this record was updated last. This property is added and maintained by mongoose."""
        return self._updated_at

    @property
    def updated_by(self) -> Optional[str]:
        """Indicate the user who updated this record last. This property is added and maintained by the system."""
        return self._updated_by

    @property
    def used_software(self) -> Optional[List[str]]:
        """A list of links to software repositories which uniquely identifies the pieces of software, including versions, used for yielding the derived data. This field is required if the dataset is a Derived dataset."""
        return self._used_software

    @used_software.setter
    def used_software(self, used_software: Optional[List[str]]) -> None:
        """A list of links to software repositories which uniquely identifies the pieces of software, including versions, used for yielding the derived data. This field is required if the dataset is a Derived dataset."""
        self._used_software = used_software

    @property
    def validation_status(self) -> Optional[str]:
        """Defines a level of trust, e.g. a measure of how much data was verified or used by other persons."""
        return self._validation_status

    @validation_status.setter
    def validation_status(self, validation_status: Optional[str]) -> None:
        """Defines a level of trust, e.g. a measure of how much data was verified or used by other persons."""
        self._validation_status = validation_status

    @property
    def meta(self) -> Dict[str, Any]:
        """Dict of scientific metadata."""
        return self._meta

    @meta.setter
    def meta(self, meta: Dict[str, Any]) -> None:
        """Dict of scientific metadata."""
        self._meta = meta

    @staticmethod
    def _prepare_fields_from_download(
        download_model: DownloadDataset,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        init_args = {}
        read_only = {}
        for field in DatasetBase._FIELD_SPEC:
            if field.read_only:
                read_only["_" + field.name] = getattr(download_model, field.scicat_name)
            else:
                init_args[field.name] = getattr(download_model, field.scicat_name)

        init_args["meta"] = download_model.scientificMetadata
        DatasetBase._convert_readonly_fields_in_place(read_only)

        return init_args, read_only

    @staticmethod
    def _convert_readonly_fields_in_place(read_only: Dict[str, Any]) -> Dict[str, Any]:
        if "_pid" in read_only:
            read_only["_pid"] = _parse_pid(read_only["_pid"])
        return read_only
