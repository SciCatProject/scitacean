##########################################
# This file was automatically generated. #
# Do not modify it directly!             #
##########################################
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen
# flake8: noqa

"""Base dataclass for Dataset."""

import dataclasses
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Generator, Literal, List, Optional, Union

import dateutil.parser

from .file import File
from .model import (
    DatasetLifecycle,
    DatasetType,
    DerivedDataset,
    OrigDatablock,
    RawDataset,
    Technique,
)
from .pid import PID


def _apply_default(
    value: Any, default: Any, default_factory: Optional[Callable]
) -> Any:
    if value is not None:
        return value
    if default_factory is not None:
        return default_factory()
    return default


def _parse_datetime(x: Optional[Union[datetime, str]]) -> datetime:
    if isinstance(x, datetime):
        return x
    if isinstance(x, str):
        if x != "now":
            return dateutil.parser.parse(x)
    return datetime.now(tz=timezone.utc)


class DatasetFields:
    @dataclasses.dataclass(frozen=True)
    class Field:
        name: str
        description: str
        read_only: bool
        required_by_derived: bool
        required_by_raw: bool
        type: type
        used_by_derived: bool
        used_by_raw: bool

        def required(self, dataset_type: DatasetType) -> bool:
            return (
                self.required_by_raw
                if dataset_type == DatasetType.RAW
                else self.required_by_derived
            )

    _FIELD_SPEC = [
        Field(
            name="access_groups",
            description="Groups which have read access to the data. The special group 'public' makes data available to all users.",
            read_only=False,
            required_by_derived=False,
            required_by_raw=False,
            type=List[str],
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="classification",
            description="ACIA information about AUthenticity,COnfidentiality,INtegrity and AVailability requirements of dataset. E.g. AV(ailabilty)=medium could trigger the creation of two tape copies. Format 'AV=medium,CO=low'",
            read_only=False,
            required_by_derived=False,
            required_by_raw=False,
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="contact_email",
            description="Email of contact person for this dataset. May contain a list of emails, which should then be seperated by semicolons.",
            read_only=False,
            required_by_derived=True,
            required_by_raw=True,
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="created_at",
            description="Time when the object was created in the database.",
            read_only=True,
            required_by_derived=False,
            required_by_raw=False,
            type=datetime,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="created_by",
            description="Account name who created the object in the database.",
            read_only=True,
            required_by_derived=False,
            required_by_raw=False,
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="creation_location",
            description="Unique location identifier where data was taken, usually in the form /Site-name/facility-name/instrumentOrBeamline-name",
            read_only=False,
            required_by_derived=False,
            required_by_raw=False,
            type=str,
            used_by_derived=False,
            used_by_raw=True,
        ),
        Field(
            name="creation_time",
            description="Time when dataset became fully available on disk, i.e. all containing files have been written.",
            read_only=False,
            required_by_derived=True,
            required_by_raw=True,
            type=datetime,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="data_format",
            description="Defines format of subsequent scientific meta data, e.g Nexus Version x.y",
            read_only=False,
            required_by_derived=False,
            required_by_raw=False,
            type=str,
            used_by_derived=False,
            used_by_raw=True,
        ),
        Field(
            name="description",
            description="Free text explanation of the contents of the dataset.",
            read_only=False,
            required_by_derived=False,
            required_by_raw=False,
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="end_time",
            description="Time of end of data taking for this dataset.",
            read_only=False,
            required_by_derived=False,
            required_by_raw=False,
            type=datetime,
            used_by_derived=False,
            used_by_raw=True,
        ),
        Field(
            name="history",
            description="List of previous versions of the dataset. Populated automatically by SciCat.",
            read_only=True,
            required_by_derived=False,
            required_by_raw=False,
            type=List[dict],
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="input_datasets",
            description="Array of input dataset identifiers used in producing the derived dataset. Ideally these are the global identifier to existing datasets inside this or federated data catalogs.",
            read_only=False,
            required_by_derived=True,
            required_by_raw=True,
            type=List[PID],
            used_by_derived=True,
            used_by_raw=False,
        ),
        Field(
            name="instrument_group",
            description="Groups which have read and write access to the data.",
            read_only=False,
            required_by_derived=False,
            required_by_raw=False,
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="instrument_id",
            description="SciCat ID of the instrument used to measure the data.",
            read_only=False,
            required_by_derived=False,
            required_by_raw=False,
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="investigator",
            description="Email of the (principal) investigator. The string may contain a list of emails, which should then be separated by semicolons.",
            read_only=False,
            required_by_derived=True,
            required_by_raw=True,
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="is_published",
            description="Indicate whether the dataset is publicly available.",
            read_only=False,
            required_by_derived=False,
            required_by_raw=False,
            type=bool,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="job_log_data",
            description="The output job logfile. Keep the size of this log data well below 15 MB.",
            read_only=False,
            required_by_derived=False,
            required_by_raw=False,
            type=str,
            used_by_derived=True,
            used_by_raw=False,
        ),
        Field(
            name="job_parameters",
            description="Input parameters to the job that produced the derived data.",
            read_only=False,
            required_by_derived=False,
            required_by_raw=False,
            type=dict,
            used_by_derived=True,
            used_by_raw=False,
        ),
        Field(
            name="keywords",
            description="Array of tags associated with the meaning or contents of this dataset. Values should ideally come from defined vocabularies, taxonomies, ontologies or knowledge graphs.",
            read_only=False,
            required_by_derived=False,
            required_by_raw=False,
            type=List[str],
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="license",
            description="Name of license under which data can be used.",
            read_only=False,
            required_by_derived=False,
            required_by_raw=False,
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="lifecycle",
            description="Parameters for storage and publishing of dataset.",
            read_only=False,
            required_by_derived=False,
            required_by_raw=False,
            type=DatasetLifecycle,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="meta",
            description="Free form meta data.",
            read_only=False,
            required_by_derived=False,
            required_by_raw=False,
            type=Dict,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="name",
            description="A name for the dataset.",
            read_only=False,
            required_by_derived=False,
            required_by_raw=False,
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="number_of_files",
            description="Total number of files in directly accessible storage associated with the dataset. (Corresponds to OrigDatablocks.)",
            read_only=True,
            required_by_derived=False,
            required_by_raw=False,
            type=int,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="number_of_files_archived",
            description="Total number of archived files associated with the dataset. (Corresponds to Datablocks.)",
            read_only=True,
            required_by_derived=False,
            required_by_raw=False,
            type=int,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="orcid_of_owner",
            description="ORCID of owner/custodian. The string may contain a list of ORCID, which should then be separated by semicolons. ORCIDs must include the prefix https://orcid.org/",
            read_only=False,
            required_by_derived=False,
            required_by_raw=False,
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="owner",
            description="Owner or custodian of the dataset, usually first name + lastname. The string may contain a list of persons, which should then be seperated by semicolons.",
            read_only=False,
            required_by_derived=True,
            required_by_raw=True,
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="owner_email",
            description="Email of owner or of custodian of the dataset. The string may contain a list of emails, which should then be seperated by semicolons.",
            read_only=False,
            required_by_derived=False,
            required_by_raw=False,
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="owner_group",
            description="Defines the group which owns the data, and therefore has unrestricted access to this data. Usually a pgroup like p12151.",
            read_only=False,
            required_by_derived=True,
            required_by_raw=True,
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="packed_size",
            description="Total size of all datablock package files created for this dataset.",
            read_only=True,
            required_by_derived=False,
            required_by_raw=False,
            type=int,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="pid",
            description="Persistent identifier for datasets.",
            read_only=True,
            required_by_derived=False,
            required_by_raw=False,
            type=PID,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="proposal_id",
            description="Identifier for the proposal that the dataset was produced for.",
            read_only=False,
            required_by_derived=False,
            required_by_raw=False,
            type=str,
            used_by_derived=False,
            used_by_raw=True,
        ),
        Field(
            name="sample_id",
            description="Identifier for the sample that the dataset contains a measurement of.",
            read_only=False,
            required_by_derived=False,
            required_by_raw=False,
            type=str,
            used_by_derived=False,
            used_by_raw=True,
        ),
        Field(
            name="shared_with",
            description="List of users that the dataset has been shared with.",
            read_only=False,
            required_by_derived=False,
            required_by_raw=False,
            type=List[str],
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="size",
            description="Total size of all files contained in source folder on disk when unpacked.",
            read_only=True,
            required_by_derived=False,
            required_by_raw=False,
            type=int,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="source_folder",
            description="Absolute file path on file server containing the files of this dataset, e.g. /some/path/to/sourcefolder. In case of a single file dataset, e.g. HDF5 data, it contains the path up to, but excluding the filename.",
            read_only=False,
            required_by_derived=True,
            required_by_raw=True,
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="source_folder_host",
            description="DNS host name of file server hosting source_folder, optionally including protocol e.g. [protocol://]fileserver1.example.com",
            read_only=False,
            required_by_derived=False,
            required_by_raw=False,
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="techniques",
            description="List of techniques used to produce the data.",
            read_only=False,
            required_by_derived=False,
            required_by_raw=False,
            type=List[Technique],
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="type",
            description="Dataset type. 'Derived' or 'Raw'",
            read_only=False,
            required_by_derived=True,
            required_by_raw=True,
            type=DatasetType,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="updated_at",
            description="Time when the object was last updated in the database.",
            read_only=True,
            required_by_derived=False,
            required_by_raw=False,
            type=datetime,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="updated_by",
            description="Account name who last updated the object in the database.",
            read_only=True,
            required_by_derived=False,
            required_by_raw=False,
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="used_software",
            description="A list of links to software repositories which uniquely identifies the software used and the version for producing the derived data.",
            read_only=False,
            required_by_derived=True,
            required_by_raw=True,
            type=List[str],
            used_by_derived=True,
            used_by_raw=False,
        ),
        Field(
            name="validation_status",
            description="Defines a level of trust, e.g. a measure of how much data was verified or used by other persons.",
            read_only=False,
            required_by_derived=False,
            required_by_raw=False,
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
        Field(
            name="version",
            description="Version of SciCat API used in creation of dataset.",
            read_only=True,
            required_by_derived=False,
            required_by_raw=False,
            type=str,
            used_by_derived=True,
            used_by_raw=True,
        ),
    ]

    def __init__(
        self,
        *,
        type: Union[DatasetType, Literal["derived", "raw"]],
        creation_time: Optional[Union[datetime, str]] = None,
        access_groups: Optional[List[str]] = None,
        classification: Optional[str] = None,
        contact_email: Optional[str] = None,
        creation_location: Optional[str] = None,
        data_format: Optional[str] = None,
        description: Optional[str] = None,
        end_time: Optional[datetime] = None,
        input_datasets: Optional[List[PID]] = None,
        instrument_group: Optional[str] = None,
        instrument_id: Optional[str] = None,
        investigator: Optional[str] = None,
        is_published: Optional[bool] = None,
        job_log_data: Optional[str] = None,
        job_parameters: Optional[dict] = None,
        keywords: Optional[List[str]] = None,
        license: Optional[str] = None,
        lifecycle: Optional[DatasetLifecycle] = None,
        meta: Optional[Dict] = None,
        name: Optional[str] = None,
        orcid_of_owner: Optional[str] = None,
        owner: Optional[str] = None,
        owner_email: Optional[str] = None,
        owner_group: Optional[str] = None,
        proposal_id: Optional[str] = None,
        sample_id: Optional[str] = None,
        shared_with: Optional[List[str]] = None,
        source_folder: Optional[str] = None,
        source_folder_host: Optional[str] = None,
        techniques: Optional[List[Technique]] = None,
        used_software: Optional[List[str]] = None,
        validation_status: Optional[str] = None,
        _files: Optional[List[File]] = None,
        _pid: Optional[Union[str, PID]] = None,
        _read_only: Optional[Dict[str, Any]] = None,
    ):
        _read_only = _read_only or {}
        self._fields = {
            "creation_time": _parse_datetime(creation_time),
            "history": _apply_default(_read_only.get("history"), None, list),
            "pid": PID.parse(_pid) if isinstance(_pid, str) else _pid,
            "type": DatasetType(type),
            "access_groups": _apply_default(access_groups, None, None),
            "classification": _apply_default(classification, None, None),
            "contact_email": _apply_default(contact_email, None, None),
            "created_at": _apply_default(_read_only.get("created_at"), None, None),
            "created_by": _apply_default(_read_only.get("created_by"), None, None),
            "creation_location": _apply_default(creation_location, None, None),
            "data_format": _apply_default(data_format, None, None),
            "description": _apply_default(description, None, None),
            "end_time": _apply_default(end_time, None, None),
            "input_datasets": _apply_default(input_datasets, None, None),
            "instrument_group": _apply_default(instrument_group, None, None),
            "instrument_id": _apply_default(instrument_id, None, None),
            "investigator": _apply_default(investigator, None, None),
            "is_published": _apply_default(is_published, False, None),
            "job_log_data": _apply_default(job_log_data, None, None),
            "job_parameters": _apply_default(job_parameters, None, None),
            "keywords": _apply_default(keywords, None, None),
            "license": _apply_default(license, None, None),
            "lifecycle": _apply_default(lifecycle, None, None),
            "meta": _apply_default(meta, None, dict),
            "name": _apply_default(name, None, None),
            "orcid_of_owner": _apply_default(orcid_of_owner, None, None),
            "owner": _apply_default(owner, None, None),
            "owner_email": _apply_default(owner_email, None, None),
            "owner_group": _apply_default(owner_group, None, None),
            "proposal_id": _apply_default(proposal_id, None, None),
            "sample_id": _apply_default(sample_id, None, None),
            "shared_with": _apply_default(shared_with, None, None),
            "source_folder": _apply_default(source_folder, None, None),
            "source_folder_host": _apply_default(source_folder_host, None, None),
            "techniques": _apply_default(techniques, None, None),
            "updated_at": _apply_default(_read_only.get("updated_at"), None, None),
            "updated_by": _apply_default(_read_only.get("updated_by"), None, None),
            "used_software": _apply_default(used_software, None, None),
            "validation_status": _apply_default(validation_status, None, None),
            "version": _apply_default(_read_only.get("version"), None, None),
        }
        self._files = [] if _files is None else list(_files)

    @property
    def pid(self) -> Optional[PID]:
        """Persistent identifier for datasets."""
        return self._fields["pid"]

    @property
    def creation_time(self) -> datetime:
        return self._fields["creation_time"]

    @creation_time.setter
    def creation_time(self, value: Union[datetime, str]):
        if value is None:
            raise TypeError("Cannot set creation_time to None")
        self._fields["creation_time"] = _parse_datetime(value)

    @property
    def access_groups(self) -> Optional[List[str]]:
        """Groups which have read access to the data. The special group 'public' makes data available to all users."""
        return self._fields["access_groups"]

    @access_groups.setter
    def access_groups(self, val: Optional[List[str]]):
        self._fields["access_groups"] = val

    @property
    def classification(self) -> Optional[str]:
        """ACIA information about AUthenticity,COnfidentiality,INtegrity and AVailability requirements of dataset. E.g. AV(ailabilty)=medium could trigger the creation of two tape copies. Format 'AV=medium,CO=low'"""
        return self._fields["classification"]

    @classification.setter
    def classification(self, val: Optional[str]):
        self._fields["classification"] = val

    @property
    def contact_email(self) -> Optional[str]:
        """Email of contact person for this dataset. May contain a list of emails, which should then be seperated by semicolons."""
        return self._fields["contact_email"]

    @contact_email.setter
    def contact_email(self, val: Optional[str]):
        self._fields["contact_email"] = val

    @property
    def created_at(self) -> Optional[datetime]:
        """Time when the object was created in the database."""
        return self._fields["created_at"]

    @property
    def created_by(self) -> Optional[str]:
        """Account name who created the object in the database."""
        return self._fields["created_by"]

    @property
    def creation_location(self) -> Optional[str]:
        """Unique location identifier where data was taken, usually in the form /Site-name/facility-name/instrumentOrBeamline-name"""
        return self._fields["creation_location"]

    @creation_location.setter
    def creation_location(self, val: Optional[str]):
        self._fields["creation_location"] = val

    @property
    def data_format(self) -> Optional[str]:
        """Defines format of subsequent scientific meta data, e.g Nexus Version x.y"""
        return self._fields["data_format"]

    @data_format.setter
    def data_format(self, val: Optional[str]):
        self._fields["data_format"] = val

    @property
    def description(self) -> Optional[str]:
        """Free text explanation of the contents of the dataset."""
        return self._fields["description"]

    @description.setter
    def description(self, val: Optional[str]):
        self._fields["description"] = val

    @property
    def end_time(self) -> Optional[datetime]:
        """Time of end of data taking for this dataset."""
        return self._fields["end_time"]

    @end_time.setter
    def end_time(self, val: Optional[datetime]):
        self._fields["end_time"] = val

    @property
    def input_datasets(self) -> Optional[List[PID]]:
        """Array of input dataset identifiers used in producing the derived dataset. Ideally these are the global identifier to existing datasets inside this or federated data catalogs."""
        return self._fields["input_datasets"]

    @input_datasets.setter
    def input_datasets(self, val: Optional[List[PID]]):
        self._fields["input_datasets"] = val

    @property
    def instrument_group(self) -> Optional[str]:
        """Groups which have read and write access to the data."""
        return self._fields["instrument_group"]

    @instrument_group.setter
    def instrument_group(self, val: Optional[str]):
        self._fields["instrument_group"] = val

    @property
    def instrument_id(self) -> Optional[str]:
        """SciCat ID of the instrument used to measure the data."""
        return self._fields["instrument_id"]

    @instrument_id.setter
    def instrument_id(self, val: Optional[str]):
        self._fields["instrument_id"] = val

    @property
    def investigator(self) -> Optional[str]:
        """Email of the (principal) investigator. The string may contain a list of emails, which should then be separated by semicolons."""
        return self._fields["investigator"]

    @investigator.setter
    def investigator(self, val: Optional[str]):
        self._fields["investigator"] = val

    @property
    def is_published(self) -> Optional[bool]:
        """Indicate whether the dataset is publicly available."""
        return self._fields["is_published"]

    @is_published.setter
    def is_published(self, val: Optional[bool]):
        self._fields["is_published"] = val

    @property
    def job_log_data(self) -> Optional[str]:
        """The output job logfile. Keep the size of this log data well below 15 MB."""
        return self._fields["job_log_data"]

    @job_log_data.setter
    def job_log_data(self, val: Optional[str]):
        self._fields["job_log_data"] = val

    @property
    def job_parameters(self) -> Optional[dict]:
        """Input parameters to the job that produced the derived data."""
        return self._fields["job_parameters"]

    @job_parameters.setter
    def job_parameters(self, val: Optional[dict]):
        self._fields["job_parameters"] = val

    @property
    def keywords(self) -> Optional[List[str]]:
        """Array of tags associated with the meaning or contents of this dataset. Values should ideally come from defined vocabularies, taxonomies, ontologies or knowledge graphs."""
        return self._fields["keywords"]

    @keywords.setter
    def keywords(self, val: Optional[List[str]]):
        self._fields["keywords"] = val

    @property
    def license(self) -> Optional[str]:
        """Name of license under which data can be used."""
        return self._fields["license"]

    @license.setter
    def license(self, val: Optional[str]):
        self._fields["license"] = val

    @property
    def lifecycle(self) -> Optional[DatasetLifecycle]:
        """Parameters for storage and publishing of dataset."""
        return self._fields["lifecycle"]

    @lifecycle.setter
    def lifecycle(self, val: Optional[DatasetLifecycle]):
        self._fields["lifecycle"] = val

    @property
    def meta(self) -> Optional[Dict]:
        """Free form meta data."""
        return self._fields["meta"]

    @meta.setter
    def meta(self, val: Optional[Dict]):
        self._fields["meta"] = val

    @property
    def name(self) -> Optional[str]:
        """A name for the dataset."""
        return self._fields["name"]

    @name.setter
    def name(self, val: Optional[str]):
        self._fields["name"] = val

    @property
    def orcid_of_owner(self) -> Optional[str]:
        """ORCID of owner/custodian. The string may contain a list of ORCID, which should then be separated by semicolons. ORCIDs must include the prefix https://orcid.org/"""
        return self._fields["orcid_of_owner"]

    @orcid_of_owner.setter
    def orcid_of_owner(self, val: Optional[str]):
        self._fields["orcid_of_owner"] = val

    @property
    def owner(self) -> Optional[str]:
        """Owner or custodian of the dataset, usually first name + lastname. The string may contain a list of persons, which should then be seperated by semicolons."""
        return self._fields["owner"]

    @owner.setter
    def owner(self, val: Optional[str]):
        self._fields["owner"] = val

    @property
    def owner_email(self) -> Optional[str]:
        """Email of owner or of custodian of the dataset. The string may contain a list of emails, which should then be seperated by semicolons."""
        return self._fields["owner_email"]

    @owner_email.setter
    def owner_email(self, val: Optional[str]):
        self._fields["owner_email"] = val

    @property
    def owner_group(self) -> Optional[str]:
        """Defines the group which owns the data, and therefore has unrestricted access to this data. Usually a pgroup like p12151."""
        return self._fields["owner_group"]

    @owner_group.setter
    def owner_group(self, val: Optional[str]):
        self._fields["owner_group"] = val

    @property
    def proposal_id(self) -> Optional[str]:
        """Identifier for the proposal that the dataset was produced for."""
        return self._fields["proposal_id"]

    @proposal_id.setter
    def proposal_id(self, val: Optional[str]):
        self._fields["proposal_id"] = val

    @property
    def sample_id(self) -> Optional[str]:
        """Identifier for the sample that the dataset contains a measurement of."""
        return self._fields["sample_id"]

    @sample_id.setter
    def sample_id(self, val: Optional[str]):
        self._fields["sample_id"] = val

    @property
    def shared_with(self) -> Optional[List[str]]:
        """List of users that the dataset has been shared with."""
        return self._fields["shared_with"]

    @shared_with.setter
    def shared_with(self, val: Optional[List[str]]):
        self._fields["shared_with"] = val

    @property
    def source_folder(self) -> Optional[str]:
        """Absolute file path on file server containing the files of this dataset, e.g. /some/path/to/sourcefolder. In case of a single file dataset, e.g. HDF5 data, it contains the path up to, but excluding the filename."""
        return self._fields["source_folder"]

    @source_folder.setter
    def source_folder(self, val: Optional[str]):
        self._fields["source_folder"] = val

    @property
    def source_folder_host(self) -> Optional[str]:
        """DNS host name of file server hosting source_folder, optionally including protocol e.g. [protocol://]fileserver1.example.com"""
        return self._fields["source_folder_host"]

    @source_folder_host.setter
    def source_folder_host(self, val: Optional[str]):
        self._fields["source_folder_host"] = val

    @property
    def techniques(self) -> Optional[List[Technique]]:
        """List of techniques used to produce the data."""
        return self._fields["techniques"]

    @techniques.setter
    def techniques(self, val: Optional[List[Technique]]):
        self._fields["techniques"] = val

    @property
    def type(self) -> Optional[DatasetType]:
        """Dataset type. 'Derived' or 'Raw'"""
        return self._fields["type"]

    @type.setter
    def type(self, val: Optional[DatasetType]):
        self._fields["type"] = val

    @property
    def updated_at(self) -> Optional[datetime]:
        """Time when the object was last updated in the database."""
        return self._fields["updated_at"]

    @property
    def updated_by(self) -> Optional[str]:
        """Account name who last updated the object in the database."""
        return self._fields["updated_by"]

    @property
    def used_software(self) -> Optional[List[str]]:
        """A list of links to software repositories which uniquely identifies the software used and the version for producing the derived data."""
        return self._fields["used_software"]

    @used_software.setter
    def used_software(self, val: Optional[List[str]]):
        self._fields["used_software"] = val

    @property
    def validation_status(self) -> Optional[str]:
        """Defines a level of trust, e.g. a measure of how much data was verified or used by other persons."""
        return self._fields["validation_status"]

    @validation_status.setter
    def validation_status(self, val: Optional[str]):
        self._fields["validation_status"] = val

    @property
    def version(self) -> Optional[str]:
        """Version of SciCat API used in creation of dataset."""
        return self._fields["version"]

    @classmethod
    def fields(
        cls,
        dataset_type: Optional[Union[DatasetType, Literal["derived", "raw"]]] = None,
        read_only: Optional[bool] = None,
    ) -> Generator[Field, None, None]:
        """Iterator over dataset fields."""
        it = DatasetFields._FIELD_SPEC
        if dataset_type is not None:
            attr = (
                "used_by_derived"
                if dataset_type == DatasetType.DERIVED
                else "used_by_raw"
            )
            it = filter(lambda field: getattr(field, attr), it)
        if read_only is not None:
            it = filter(lambda field: field.read_only == read_only, it)
        yield from it

    def __str__(self) -> str:
        args = ", ".join(
            f"{name}={value}"
            for name, value in (
                (field.name, getattr(self, field.name)) for field in self.fields()
            )
            if value is not None
        )
        return f"Dataset({args})"

    def make_dataset_model(self) -> Union[DerivedDataset, RawDataset]:
        if self.type == DatasetType.DERIVED:
            return self._make_derived_model()
        return self._make_raw_model()

    def _make_derived_model(self):
        if self.creation_location is not None:
            raise ValueError("'creation_location' must not be set in derived datasets")
        if self.data_format is not None:
            raise ValueError("'data_format' must not be set in derived datasets")
        if self.end_time is not None:
            raise ValueError("'end_time' must not be set in derived datasets")
        if self.proposal_id is not None:
            raise ValueError("'proposal_id' must not be set in derived datasets")
        if self.sample_id is not None:
            raise ValueError("'sample_id' must not be set in derived datasets")
        return DerivedDataset(
            accessGroups=self.access_groups,
            classification=self.classification,
            contactEmail=self.contact_email,
            createdAt=self.created_at,
            createdBy=self.created_by,
            creationTime=self.creation_time,
            description=self.description,
            history=self.history,
            inputDatasets=self.input_datasets,
            instrumentGroup=self.instrument_group,
            instrumentId=self.instrument_id,
            investigator=self.investigator,
            isPublished=self.is_published,
            jobLogData=self.job_log_data,
            jobParameters=self.job_parameters,
            keywords=self.keywords,
            license=self.license,
            datasetlifecycle=self.lifecycle,
            scientificMetadata=self.meta,
            datasetName=self.name,
            numberOfFiles=self.number_of_files,
            numberOfFilesArchived=self.number_of_files_archived,
            orcidOfOwner=self.orcid_of_owner,
            owner=self.owner,
            ownerEmail=self.owner_email,
            ownerGroup=self.owner_group,
            packedSize=self.packed_size,
            pid=self.pid,
            sharedWith=self.shared_with,
            size=self.size,
            sourceFolder=self.source_folder,
            sourceFolderHost=self.source_folder_host,
            techniques=self.techniques,
            type=self.type,
            updatedAt=self.updated_at,
            updatedBy=self.updated_by,
            usedSoftware=self.used_software,
            validationStatus=self.validation_status,
            version=self.version,
        )

    def _make_raw_model(self):
        if self.input_datasets is not None:
            raise ValueError("'input_datasets' must not be set in raw datasets")
        if self.job_log_data is not None:
            raise ValueError("'job_log_data' must not be set in raw datasets")
        if self.job_parameters is not None:
            raise ValueError("'job_parameters' must not be set in raw datasets")
        if self.used_software is not None:
            raise ValueError("'used_software' must not be set in raw datasets")
        return RawDataset(
            accessGroups=self.access_groups,
            classification=self.classification,
            contactEmail=self.contact_email,
            createdAt=self.created_at,
            createdBy=self.created_by,
            creationLocation=self.creation_location,
            creationTime=self.creation_time,
            dataFormat=self.data_format,
            description=self.description,
            endTime=self.end_time,
            history=self.history,
            instrumentGroup=self.instrument_group,
            instrumentId=self.instrument_id,
            principalInvestigator=self.investigator,
            isPublished=self.is_published,
            keywords=self.keywords,
            license=self.license,
            datasetlifecycle=self.lifecycle,
            scientificMetadata=self.meta,
            datasetName=self.name,
            numberOfFiles=self.number_of_files,
            numberOfFilesArchived=self.number_of_files_archived,
            orcidOfOwner=self.orcid_of_owner,
            owner=self.owner,
            ownerEmail=self.owner_email,
            ownerGroup=self.owner_group,
            packedSize=self.packed_size,
            pid=self.pid,
            proposalID=self.proposal_id,
            sampleID=self.sample_id,
            sharedWith=self.shared_with,
            size=self.size,
            sourceFolder=self.source_folder,
            sourceFolderHost=self.source_folder_host,
            techniques=self.techniques,
            type=self.type,
            updatedAt=self.updated_at,
            updatedBy=self.updated_by,
            validationStatus=self.validation_status,
            version=self.version,
        )

    @classmethod
    def from_models(
        cls,
        *,
        dataset_model: Union[DerivedDataset, RawDataset],
        orig_datablock_models: Optional[List[OrigDatablock]],
    ):
        """Create a new dataset from fully filled in models.

        Parameters
        ----------
        dataset_model:
            Fields, including scientific metadata are filled from this model.
        orig_datablock_models:
            File links are populated from this model.

        Returns
        -------
        :
            A new dataset.
        """
        args = _fields_from_model(dataset_model)
        read_only_args = args.pop("_read_only")
        read_only_args["history"] = dataset_model.history
        return cls(
            creation_time=dataset_model.creationTime,
            _pid=dataset_model.pid,
            _files=_files_from_datablocks(dataset_model, orig_datablock_models),
            _read_only=read_only_args,
            **args,
        )


def _fields_from_model(model: Union[DerivedDataset, RawDataset]) -> dict:
    return (
        _fields_from_derived_model(model)
        if isinstance(model, DerivedDataset)
        else _fields_from_raw_model(model)
    )


def _files_from_datablocks(
    dataset_model: Union[DerivedDataset, RawDataset],
    orig_datablock_models: Optional[List[OrigDatablock]],
) -> List[File]:
    if orig_datablock_models is None:
        return []

    if len(orig_datablock_models) != 1:
        raise NotImplementedError(
            f"Got {len(orig_datablock_models)} original datablocks for "
            f"dataset {dataset_model.pid} but only support for one is implemented."
        )
    dblock = orig_datablock_models[0]
    return [
        File.from_scicat(file, source_folder=dataset_model.sourceFolder)
        for file in dblock.dataFileList
    ]


def _fields_from_derived_model(model) -> dict:
    return dict(
        _read_only=dict(
            created_at=model.createdAt,
            created_by=model.createdBy,
            updated_at=model.updatedAt,
            updated_by=model.updatedBy,
            version=model.version,
        ),
        access_groups=model.accessGroups,
        classification=model.classification,
        contact_email=model.contactEmail,
        description=model.description,
        input_datasets=model.inputDatasets,
        instrument_group=model.instrumentGroup,
        instrument_id=model.instrumentId,
        investigator=model.investigator,
        is_published=model.isPublished,
        job_log_data=model.jobLogData,
        job_parameters=model.jobParameters,
        keywords=model.keywords,
        license=model.license,
        lifecycle=model.datasetlifecycle,
        meta=model.scientificMetadata,
        name=model.datasetName,
        orcid_of_owner=model.orcidOfOwner,
        owner=model.owner,
        owner_email=model.ownerEmail,
        owner_group=model.ownerGroup,
        shared_with=model.sharedWith,
        source_folder=model.sourceFolder,
        source_folder_host=model.sourceFolderHost,
        techniques=model.techniques,
        type=model.type,
        used_software=model.usedSoftware,
        validation_status=model.validationStatus,
    )


def _fields_from_raw_model(model) -> dict:
    return dict(
        _read_only=dict(
            created_at=model.createdAt,
            created_by=model.createdBy,
            updated_at=model.updatedAt,
            updated_by=model.updatedBy,
            version=model.version,
        ),
        access_groups=model.accessGroups,
        classification=model.classification,
        contact_email=model.contactEmail,
        creation_location=model.creationLocation,
        data_format=model.dataFormat,
        description=model.description,
        end_time=model.endTime,
        instrument_group=model.instrumentGroup,
        instrument_id=model.instrumentId,
        investigator=model.principalInvestigator,
        is_published=model.isPublished,
        keywords=model.keywords,
        license=model.license,
        lifecycle=model.datasetlifecycle,
        meta=model.scientificMetadata,
        name=model.datasetName,
        orcid_of_owner=model.orcidOfOwner,
        owner=model.owner,
        owner_email=model.ownerEmail,
        owner_group=model.ownerGroup,
        proposal_id=model.proposalID,
        sample_id=model.sampleID,
        shared_with=model.sharedWith,
        source_folder=model.sourceFolder,
        source_folder_host=model.sourceFolderHost,
        techniques=model.techniques,
        type=model.type,
        validation_status=model.validationStatus,
    )
