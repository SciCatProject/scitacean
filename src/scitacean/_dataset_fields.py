# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)

"""Base class for Dataset."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, ClassVar, Literal, TypeVar

from ._base_model import DatasetType
from .datablock import OrigDatablock
from .filesystem import RemotePath
from .model import (
    Attachment,
    BaseModel,
    BaseUserModel,
    DownloadDataset,
    DownloadLifecycle,
    Lifecycle,
    Relationship,
    Technique,
    construct,
)
from .ontology import find_technique
from .pid import PID

M = TypeVar("M", bound=BaseModel)


def _parse_datetime(x: datetime | str | None) -> datetime | None:
    if isinstance(x, datetime) or x is None:
        return x
    if x == "now":
        return datetime.now(tz=UTC)
    return datetime.fromisoformat(x)


def _parse_pid(pid: str | PID | None) -> PID | None:
    if pid is None:
        return pid
    return PID.parse(pid)


def _parse_remote_path(path: str | RemotePath | None) -> RemotePath | None:
    if path is None:
        return path
    return RemotePath(path)


def _parse_techniques(arg: Iterable[str | Technique] | None) -> list[Technique] | None:
    if arg is None:
        return None
    return [t if isinstance(t, Technique) else find_technique(t) for t in arg]


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

    _FIELD_SPEC: ClassVar[list[Field]] = [
        Field(
            name="type",
            read_only=False,
            required=True,
            scicat_name="type",
            type=DatasetType,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="access_groups",
            read_only=False,
            required=False,
            scicat_name="accessGroups",
            type=list[str],
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="api_version",
            read_only=True,
            required=False,
            scicat_name="version",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="classification",
            read_only=False,
            required=False,
            scicat_name="classification",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="comment",
            read_only=False,
            required=False,
            scicat_name="comment",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="contact_email",
            read_only=False,
            required=True,
            scicat_name="contactEmail",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="created_at",
            read_only=True,
            required=False,
            scicat_name="createdAt",
            type=datetime,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="created_by",
            read_only=True,
            required=False,
            scicat_name="createdBy",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="creation_location",
            read_only=False,
            required=True,
            scicat_name="creationLocation",
            type=str,
            used_by_derived=False,
            used_by_raw=True,
        ),
        Field(
            name="creation_time",
            read_only=False,
            required=True,
            scicat_name="creationTime",
            type=datetime,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="data_format",
            read_only=False,
            required=False,
            scicat_name="dataFormat",
            type=str,
            used_by_derived=False,
            used_by_raw=True,
        ),
        Field(
            name="data_quality_metrics",
            read_only=False,
            required=False,
            scicat_name="dataQualityMetrics",
            type=int,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="description",
            read_only=False,
            required=False,
            scicat_name="description",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="end_time",
            read_only=False,
            required=False,
            scicat_name="endTime",
            type=datetime,
            used_by_derived=False,
            used_by_raw=True,
        ),
        Field(
            name="input_datasets",
            read_only=False,
            required=True,
            scicat_name="inputDatasets",
            type=list[PID],
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="instrument_group",
            read_only=False,
            required=False,
            scicat_name="instrumentGroup",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="instrument_id",
            read_only=False,
            required=False,
            scicat_name="instrumentId",
            type=str,
            used_by_derived=False,
            used_by_raw=True,
        ),
        Field(
            name="investigator",
            read_only=False,
            required=True,
            scicat_name="investigator",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="is_published",
            read_only=False,
            required=False,
            scicat_name="isPublished",
            type=bool,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="job_log_data",
            read_only=False,
            required=False,
            scicat_name="jobLogData",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="job_parameters",
            read_only=False,
            required=False,
            scicat_name="jobParameters",
            type=dict[str, Any],
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="keywords",
            read_only=False,
            required=False,
            scicat_name="keywords",
            type=list[str],
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="license",
            read_only=False,
            required=False,
            scicat_name="license",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="lifecycle",
            read_only=True,
            required=False,
            scicat_name="datasetlifecycle",
            type=Lifecycle,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="name",
            read_only=False,
            required=True,
            scicat_name="datasetName",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="orcid_of_owner",
            read_only=False,
            required=False,
            scicat_name="orcidOfOwner",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="owner",
            read_only=False,
            required=True,
            scicat_name="owner",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="owner_email",
            read_only=False,
            required=False,
            scicat_name="ownerEmail",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="owner_group",
            read_only=False,
            required=True,
            scicat_name="ownerGroup",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="pid",
            read_only=True,
            required=False,
            scicat_name="pid",
            type=PID,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="principal_investigator",
            read_only=False,
            required=True,
            scicat_name="principalInvestigator",
            type=str,
            used_by_derived=False,
            used_by_raw=True,
        ),
        Field(
            name="proposal_id",
            read_only=False,
            required=False,
            scicat_name="proposalId",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="relationships",
            read_only=False,
            required=False,
            scicat_name="relationships",
            type=list[Relationship],
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="run_number",
            read_only=False,
            required=False,
            scicat_name="runNumber",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="sample_id",
            read_only=False,
            required=False,
            scicat_name="sampleId",
            type=str,
            used_by_derived=False,
            used_by_raw=True,
        ),
        Field(
            name="shared_with",
            read_only=False,
            required=False,
            scicat_name="sharedWith",
            type=list[str],
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="source_folder",
            read_only=False,
            required=True,
            scicat_name="sourceFolder",
            type=RemotePath,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="source_folder_host",
            read_only=False,
            required=False,
            scicat_name="sourceFolderHost",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="start_time",
            read_only=False,
            required=False,
            scicat_name="startTime",
            type=datetime,
            used_by_derived=False,
            used_by_raw=True,
        ),
        Field(
            name="techniques",
            read_only=False,
            required=False,
            scicat_name="techniques",
            type=list[Technique],
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="updated_at",
            read_only=True,
            required=False,
            scicat_name="updatedAt",
            type=datetime,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="updated_by",
            read_only=True,
            required=False,
            scicat_name="updatedBy",
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="used_software",
            read_only=False,
            required=True,
            scicat_name="usedSoftware",
            type=list[str],
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="validation_status",
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
        "_attachments",
        "_attachments",
        "_classification",
        "_comment",
        "_contact_email",
        "_created_at",
        "_created_by",
        "_creation_location",
        "_creation_time",
        "_data_format",
        "_data_quality_metrics",
        "_default_checksum_algorithm",
        "_description",
        "_end_time",
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
        "_meta",
        "_name",
        "_orcid_of_owner",
        "_orig_datablocks",
        "_owner",
        "_owner_email",
        "_owner_group",
        "_pid",
        "_principal_investigator",
        "_proposal_id",
        "_relationships",
        "_run_number",
        "_sample_id",
        "_shared_with",
        "_source_folder",
        "_source_folder_host",
        "_start_time",
        "_techniques",
        "_type",
        "_updated_at",
        "_updated_by",
        "_used_software",
        "_validation_status",
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
        lifecycle: Lifecycle | None = None,
        name: str | None = None,
        orcid_of_owner: str | None = None,
        owner: str | None = None,
        owner_email: str | None = None,
        owner_group: str | None = None,
        principal_investigator: str | None = None,
        proposal_id: str | None = None,
        relationships: list[Relationship] | None = None,
        run_number: str | None = None,
        sample_id: str | None = None,
        shared_with: list[str] | None = None,
        source_folder: RemotePath | str | None = None,
        source_folder_host: str | None = None,
        start_time: datetime | None = None,
        techniques: Iterable[str | Technique] | None = None,
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
        self._lifecycle = lifecycle
        self._name = name
        self._orcid_of_owner = orcid_of_owner
        self._owner = owner
        self._owner_email = owner_email
        self._owner_group = owner_group
        self._principal_investigator = principal_investigator
        self._proposal_id = proposal_id
        self._relationships = relationships
        self._run_number = run_number
        self._sample_id = sample_id
        self._shared_with = shared_with
        self._source_folder = _parse_remote_path(source_folder)
        self._source_folder_host = source_folder_host
        self._start_time = start_time
        self._techniques = _parse_techniques(techniques)
        self._used_software = used_software
        self._validation_status = validation_status
        self._api_version = None
        self._created_at = None
        self._created_by = None
        self._pid = None
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
        """List of groups which have access to this item."""
        return self._access_groups

    @access_groups.setter
    def access_groups(self, access_groups: list[str] | None) -> None:
        self._access_groups = access_groups

    @property
    def api_version(self) -> str | None:
        """Version of the API used to create the dataset."""
        return self._api_version

    @property
    def classification(self) -> str | None:
        """ACIA information about the dataset.

        ACIA stands for AUthenticity,COnfidentiality,INtegrity and AVailability.
        Example: ``'AV=medium,CO=low'``

        SciCat may trigger different operations based on this value.
        """
        return self._classification

    @classification.setter
    def classification(self, classification: str | None) -> None:
        self._classification = classification

    @property
    def comment(self) -> str | None:
        """Comment about the dataset."""
        return self._comment

    @comment.setter
    def comment(self, comment: str | None) -> None:
        self._comment = comment

    @property
    def contact_email(self) -> str | None:
        """Email of the contact person for this dataset.

        The string may contain a list of emails,
        which should then be separated by semicolons.
        """
        return self._contact_email

    @contact_email.setter
    def contact_email(self, contact_email: str | None) -> None:
        self._contact_email = contact_email

    @property
    def created_at(self) -> datetime | None:
        """Date and time when this dataset was created in the database.

        This field is managed by SciCat.
        """
        return self._created_at

    @property
    def created_by(self) -> str | None:
        """Username who created this dataset.

        This field is managed by SciCat.
        """
        return self._created_by

    @property
    def creation_location(self) -> str | None:
        """Unique location identifier where data was taken.

        Usually one of these forms::

            /site-name/facility-name/instrumentOrBeamline-name
            facility-name:instrumentOrBeamline-name
        """
        return self._creation_location

    @creation_location.setter
    def creation_location(self, creation_location: str | None) -> None:
        self._creation_location = creation_location

    @property
    def creation_time(self) -> datetime | None:
        """Time when dataset became fully available.

        This can be the time when all containing files have been written,
        or when the dataset was created in SciCat.
        Local times without timezone/offset info are automatically transformed to
        UTC using the timezone of the API server.

        Inserted automatically by Scitacean on upload.
        """
        return self._creation_time

    @creation_time.setter
    def creation_time(self, creation_time: str | datetime | None) -> None:
        self._creation_time = _parse_datetime(creation_time)

    @property
    def data_format(self) -> str | None:
        """Format of the data files in this dataset.

        Example: ```Nexus Version x.y.```
        """
        return self._data_format

    @data_format.setter
    def data_format(self, data_format: str | None) -> None:
        self._data_format = data_format

    @property
    def data_quality_metrics(self) -> int | None:
        """A number  given by the user to rate the dataset."""
        return self._data_quality_metrics

    @data_quality_metrics.setter
    def data_quality_metrics(self, data_quality_metrics: int | None) -> None:
        self._data_quality_metrics = data_quality_metrics

    @property
    def description(self) -> str | None:
        """Free text explanation of the contents of the dataset."""
        return self._description

    @description.setter
    def description(self, description: str | None) -> None:
        self._description = description

    @property
    def end_time(self) -> datetime | None:
        """End time of data acquisition for the current dataset.

        Local times without timezone/offset info are automatically transformed to
        UTC using the timezone of the API server.
        """
        return self._end_time

    @end_time.setter
    def end_time(self, end_time: datetime | None) -> None:
        self._end_time = end_time

    @property
    def input_datasets(self) -> list[PID] | None:
        """Array of input dataset identifiers used in producing this dataset.

        Can be identifiers in the same or another federated catalogue.
        """
        return self._input_datasets

    @input_datasets.setter
    def input_datasets(self, input_datasets: list[PID] | None) -> None:
        self._input_datasets = input_datasets

    @property
    def instrument_group(self) -> str | None:
        """Group of the instrument which this item was acquired on."""
        return self._instrument_group

    @instrument_group.setter
    def instrument_group(self, instrument_group: str | None) -> None:
        self._instrument_group = instrument_group

    @property
    def instrument_id(self) -> str | None:
        """IDs of the instruments where the data was created."""
        return self._instrument_id

    @instrument_id.setter
    def instrument_id(self, instrument_id: str | None) -> None:
        self._instrument_id = instrument_id

    @property
    def investigator(self) -> str | None:
        """Legacy fallback for principal_investigator."""
        return self._principal_investigator

    @investigator.setter
    def investigator(self, investigator: str | None) -> None:
        self._principal_investigator = investigator

    @property
    def is_published(self) -> bool | None:
        """True if dataset is publicly available."""
        return self._is_published

    @is_published.setter
    def is_published(self, is_published: bool | None) -> None:
        self._is_published = is_published

    @property
    def job_log_data(self) -> str | None:
        """The job log file.

        Keep the size of this log data well below 15 MB.
        """
        return self._job_log_data

    @job_log_data.setter
    def job_log_data(self, job_log_data: str | None) -> None:
        self._job_log_data = job_log_data

    @property
    def job_parameters(self) -> dict[str, Any] | None:
        """Parameters used by the job that created this dataset."""
        return self._job_parameters

    @job_parameters.setter
    def job_parameters(self, job_parameters: dict[str, Any] | None) -> None:
        self._job_parameters = job_parameters

    @property
    def keywords(self) -> list[str] | None:
        """Array of tags associated with the meaning or contents of this dataset.

        Values should ideally come from defined vocabularies, taxonomies,
        ontologies, or knowledge graphs.
        """
        return self._keywords

    @keywords.setter
    def keywords(self, keywords: list[str] | None) -> None:
        self._keywords = keywords

    @property
    def license(self) -> str | None:
        """Name of the license under which the data can be used."""
        return self._license

    @license.setter
    def license(self, license: str | None) -> None:
        self._license = license

    @property
    def lifecycle(self) -> Lifecycle | None:
        """Current status of the dataset during its lifetime w.r.t. storage handling."""
        return self._lifecycle

    @property
    def name(self) -> str | None:
        """The name of the dataset.

        Can be set freely by the creator to help identify the dataset.
        """
        return self._name

    @name.setter
    def name(self, name: str | None) -> None:
        self._name = name

    @property
    def orcid_of_owner(self) -> str | None:
        """ORCID iD of the owner or custodian.

        The string may contain a list of ORCIDs,
        which should then be separated by semicolons.
        """
        return self._orcid_of_owner

    @orcid_of_owner.setter
    def orcid_of_owner(self, orcid_of_owner: str | None) -> None:
        self._orcid_of_owner = orcid_of_owner

    @property
    def owner(self) -> str | None:
        """Full name of the owner or custodian of the dataset.

        The string may contain a list of persons,
        which should then be separated by semicolons.
        """
        return self._owner

    @owner.setter
    def owner(self, owner: str | None) -> None:
        self._owner = owner

    @property
    def owner_email(self) -> str | None:
        """Email of the owner or custodian of the dataset.

        The string may contain a list of emails,
        which should then be separated by semicolons.
        """
        return self._owner_email

    @owner_email.setter
    def owner_email(self, owner_email: str | None) -> None:
        self._owner_email = owner_email

    @property
    def owner_group(self) -> str | None:
        """Name of the group owning this item.

        This group must exist in SciCat and is used to control access to this dataset.
        """
        return self._owner_group

    @owner_group.setter
    def owner_group(self, owner_group: str | None) -> None:
        self._owner_group = owner_group

    @property
    def pid(self) -> PID | None:
        """Persistent identifier of the dataset."""
        return self._pid

    @property
    def principal_investigator(self) -> str | None:
        """Full name of the principal investigator(s).

        If multiple PIs are present, use a semicolon-separated list.
        """
        return self._principal_investigator

    @principal_investigator.setter
    def principal_investigator(self, principal_investigator: str | None) -> None:
        self._principal_investigator = principal_investigator

    @property
    def proposal_id(self) -> str | None:
        """The ID of the proposal to which the dataset belongs."""
        return self._proposal_id

    @proposal_id.setter
    def proposal_id(self, proposal_id: str | None) -> None:
        self._proposal_id = proposal_id

    @property
    def relationships(self) -> list[Relationship] | None:
        """Relationships with other datasets."""
        return self._relationships

    @relationships.setter
    def relationships(self, relationships: list[Relationship] | None) -> None:
        self._relationships = relationships

    @property
    def run_number(self) -> str | None:
        """Run number of the data acquisition."""
        return self._run_number

    @run_number.setter
    def run_number(self, run_number: str | None) -> None:
        self._run_number = run_number

    @property
    def sample_id(self) -> str | None:
        """ID of the sample used when collecting the data."""
        return self._sample_id

    @sample_id.setter
    def sample_id(self, sample_id: str | None) -> None:
        self._sample_id = sample_id

    @property
    def shared_with(self) -> list[str] | None:
        """List of users that the dataset has been shared with."""
        return self._shared_with

    @shared_with.setter
    def shared_with(self, shared_with: list[str] | None) -> None:
        self._shared_with = shared_with

    @property
    def source_folder(self) -> RemotePath | None:
        """Absolute file path on fileserver containing the files of this dataset.

        This is usually a POSIX path, e.g., ``/some/path/to/sourcefolder``.
        All files must be placed within this folder and its subfolders.
        """
        return self._source_folder

    @source_folder.setter
    def source_folder(self, source_folder: RemotePath | str | None) -> None:
        self._source_folder = _parse_remote_path(source_folder)

    @property
    def source_folder_host(self) -> str | None:
        """DNS host name of the fileserver hosting the files."""
        return self._source_folder_host

    @source_folder_host.setter
    def source_folder_host(self, source_folder_host: str | None) -> None:
        self._source_folder_host = source_folder_host

    @property
    def start_time(self) -> datetime | None:
        """Start time of data acquisition for the current dataset.

        Local times without timezone/offset info are automatically transformed to
        UTC using the timezone of the API server.
        """
        return self._start_time

    @start_time.setter
    def start_time(self, start_time: datetime | None) -> None:
        self._start_time = start_time

    @property
    def techniques(self) -> list[Technique] | None:
        """Techniques used to create the data.

        See Also
        --------
        ontology:
            Helper module for defining techniques based on known ontologies.
        """
        return self._techniques

    @techniques.setter
    def techniques(self, techniques: Iterable[str | Technique] | None) -> None:
        self._techniques = _parse_techniques(techniques)

    @property
    def updated_at(self) -> datetime | None:
        """Date and time when this record was updated last.

        This field is managed by SciCat.
        """
        return self._updated_at

    @property
    def updated_by(self) -> str | None:
        """Username who last updated this dataset.

        This field is managed by SciCat.
        """
        return self._updated_by

    @property
    def used_software(self) -> list[str] | None:
        """Software used to create this data.

        Should ideally contain complete and unique identifiers such as links to
        software releases, DOIs, or software name + version combinations.
        """
        return self._used_software

    @used_software.setter
    def used_software(self, used_software: list[str] | None) -> None:
        self._used_software = used_software

    @property
    def validation_status(self) -> str | None:
        """Level of trust.

        For example,  a measure of how much data was verified or used by other persons.
        """
        return self._validation_status

    @validation_status.setter
    def validation_status(self, validation_status: str | None) -> None:
        self._validation_status = validation_status

    @property
    def meta(self) -> dict[str, Any]:
        """Dict of scientific metadata."""
        return self._meta

    @meta.setter
    def meta(self, meta: dict[str, Any]) -> None:
        self._meta = meta

    @property
    def type(self) -> DatasetType:
        """The type of this dataset.

        - ``'raw'``: A dataset without any ancestors, e.g., measured or simulated data.
        - ``'derived'``: A dataset derived from other datasets.
        - _other_: Any other string allowed by the SciCat instance.
        """
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
