##########################################
# This file was automatically generated. #
# Do not modify it directly!             #
##########################################
# flake8: noqa

"""Base dataclass for Dataset."""

import dataclasses
from datetime import datetime
from typing import Any, Dict, List, Optional

from .pid import PID
from .model import DatasetType


def _get_value_or_default(d: dict, key: str, default: Any, default_factory: Any) -> Any:
    try:
        return d[key]
    except KeyError:
        if default_factory is not None:
            return default_factory()
        return default


class DatasetFields:
    @dataclasses.dataclass(frozen=True)
    class Field:
        name: str
        description: str
        read_only: bool
        required_by_derived: bool
        required_by_raw: bool
        typ: type
        used_by_derived: bool
        used_by_raw: bool
        value: Any

    def __init__(self, _read_only: Dict[str, Any], **kwargs: Any):
        self._fields = {
            "access_groups": DatasetFields.Field(
                name="access_groups",
                description="Groups which have read access to the data. The special group 'public' makes data available to all users.",
                read_only=False,
                required_by_derived=False,
                required_by_raw=False,
                typ=List[str],
                used_by_derived=True,
                used_by_raw=True,
                value=_get_value_or_default(kwargs, "access_groups", None, None),
            ),
            "classification": DatasetFields.Field(
                name="classification",
                description="ACIA information about AUthenticity,COnfidentiality,INtegrity and AVailability requirements of dataset. E.g. AV(ailabilty)=medium could trigger the creation of a two tape copies. Format 'AV=medium,CO=low'",
                read_only=False,
                required_by_derived=False,
                required_by_raw=False,
                typ=str,
                used_by_derived=True,
                used_by_raw=True,
                value=_get_value_or_default(kwargs, "classification", None, None),
            ),
            "contact_email": DatasetFields.Field(
                name="contact_email",
                description="Email of contact person for this dataset. May contain a list of emails, which should then be seperated by semicolons.",
                read_only=False,
                required_by_derived=True,
                required_by_raw=True,
                typ=str,
                used_by_derived=True,
                used_by_raw=True,
                value=_get_value_or_default(kwargs, "contact_email", None, None),
            ),
            "created_at": DatasetFields.Field(
                name="created_at",
                description="Time when the object was created in the database.",
                read_only=True,
                required_by_derived=False,
                required_by_raw=False,
                typ=str,
                used_by_derived=True,
                used_by_raw=True,
                value=_get_value_or_default(_read_only, "created_at", None, None),
            ),
            "created_by": DatasetFields.Field(
                name="created_by",
                description="Account name who created the object in the database.",
                read_only=True,
                required_by_derived=False,
                required_by_raw=False,
                typ=str,
                used_by_derived=True,
                used_by_raw=True,
                value=_get_value_or_default(_read_only, "created_by", None, None),
            ),
            "creation_location": DatasetFields.Field(
                name="creation_location",
                description="Unique location identifier where data was taken, usually in the form /Site-name/facility-name/instrumentOrBeamline-name",
                read_only=False,
                required_by_derived=False,
                required_by_raw=False,
                typ=str,
                used_by_derived=False,
                used_by_raw=True,
                value=_get_value_or_default(kwargs, "creation_location", None, None),
            ),
            "creation_time": DatasetFields.Field(
                name="creation_time",
                description="Time when dataset became fully available on disk, i.e. all containing files have been written.",
                read_only=False,
                required_by_derived=True,
                required_by_raw=True,
                typ=datetime,
                used_by_derived=True,
                used_by_raw=True,
                value=_get_value_or_default(
                    kwargs, "creation_time", None, datetime.now
                ),
            ),
            "data_format": DatasetFields.Field(
                name="data_format",
                description="Defines format of subsequent scientific meta data, e.g Nexus Version x.y",
                read_only=False,
                required_by_derived=True,
                required_by_raw=True,
                typ=str,
                used_by_derived=False,
                used_by_raw=True,
                value=_get_value_or_default(kwargs, "data_format", None, None),
            ),
            "description": DatasetFields.Field(
                name="description",
                description="Free text explanation of the contents of the dataset.",
                read_only=False,
                required_by_derived=False,
                required_by_raw=False,
                typ=str,
                used_by_derived=True,
                used_by_raw=True,
                value=_get_value_or_default(kwargs, "description", None, None),
            ),
            "end_time": DatasetFields.Field(
                name="end_time",
                description="Time of end of data taking for this dataset.",
                read_only=False,
                required_by_derived=False,
                required_by_raw=False,
                typ=datetime,
                used_by_derived=False,
                used_by_raw=True,
                value=_get_value_or_default(kwargs, "end_time", None, None),
            ),
            "input_datasets": DatasetFields.Field(
                name="input_datasets",
                description="Array of input dataset identifiers used in producing the derived dataset. Ideally these are the global identifier to existing datasets inside this or federated data catalogs.",
                read_only=False,
                required_by_derived=True,
                required_by_raw=True,
                typ=List[str],
                used_by_derived=True,
                used_by_raw=False,
                value=_get_value_or_default(kwargs, "input_datasets", None, list),
            ),
            "instrument_group": DatasetFields.Field(
                name="instrument_group",
                description="Groups which have read and write access to the data.",
                read_only=False,
                required_by_derived=False,
                required_by_raw=False,
                typ=str,
                used_by_derived=True,
                used_by_raw=True,
                value=_get_value_or_default(kwargs, "instrument_group", None, None),
            ),
            "instrument_id": DatasetFields.Field(
                name="instrument_id",
                description="SciCat ID of the instrument used to measure the data.",
                read_only=False,
                required_by_derived=False,
                required_by_raw=False,
                typ=str,
                used_by_derived=True,
                used_by_raw=True,
                value=_get_value_or_default(kwargs, "instrument_id", None, None),
            ),
            "investigator": DatasetFields.Field(
                name="investigator",
                description="Email of the (principal) investigator. The string may contain a list of emails, which should then be separated by semicolons.",
                read_only=False,
                required_by_derived=True,
                required_by_raw=True,
                typ=str,
                used_by_derived=True,
                used_by_raw=True,
                value=_get_value_or_default(kwargs, "investigator", None, None),
            ),
            "is_published": DatasetFields.Field(
                name="is_published",
                description="Indicate whether the dataset is publicly available.",
                read_only=False,
                required_by_derived=False,
                required_by_raw=False,
                typ=bool,
                used_by_derived=True,
                used_by_raw=True,
                value=_get_value_or_default(kwargs, "is_published", False, None),
            ),
            "job_log_data": DatasetFields.Field(
                name="job_log_data",
                description="The output job logfile. Keep the size of this log data well below 15 MB.",
                read_only=False,
                required_by_derived=False,
                required_by_raw=False,
                typ=str,
                used_by_derived=True,
                used_by_raw=False,
                value=_get_value_or_default(kwargs, "job_log_data", None, None),
            ),
            "job_parameters": DatasetFields.Field(
                name="job_parameters",
                description="Input parameters to the job that produced the derived data.",
                read_only=False,
                required_by_derived=False,
                required_by_raw=False,
                typ=dict,
                used_by_derived=True,
                used_by_raw=False,
                value=_get_value_or_default(kwargs, "job_parameters", None, None),
            ),
            "keywords": DatasetFields.Field(
                name="keywords",
                description="Array of tags associated with the meaning or contents of this dataset. Values should ideally come from defined vocabularies, taxonomies, ontologies or knowledge graphs.",
                read_only=False,
                required_by_derived=False,
                required_by_raw=False,
                typ=List[str],
                used_by_derived=True,
                used_by_raw=True,
                value=_get_value_or_default(kwargs, "keywords", None, None),
            ),
            "license": DatasetFields.Field(
                name="license",
                description="Name of license under which data can be used.",
                read_only=False,
                required_by_derived=False,
                required_by_raw=False,
                typ=str,
                used_by_derived=True,
                used_by_raw=True,
                value=_get_value_or_default(kwargs, "license", None, None),
            ),
            "name": DatasetFields.Field(
                name="name",
                description="A name for the dataset.",
                read_only=False,
                required_by_derived=False,
                required_by_raw=False,
                typ=str,
                used_by_derived=True,
                used_by_raw=True,
                value=_get_value_or_default(kwargs, "name", None, None),
            ),
            "orcid_of_owner": DatasetFields.Field(
                name="orcid_of_owner",
                description="ORCID of owner/custodian. The string may contain a list of ORCID, which should then be separated by semicolons. ORCIDs must include the prefix https://orcid.org/",
                read_only=False,
                required_by_derived=False,
                required_by_raw=False,
                typ=str,
                used_by_derived=True,
                used_by_raw=True,
                value=_get_value_or_default(kwargs, "orcid_of_owner", None, None),
            ),
            "owner": DatasetFields.Field(
                name="owner",
                description="Owner or custodian of the dataset, usually first name + lastname. The string may contain a list of persons, which should then be seperated by semicolons.",
                read_only=False,
                required_by_derived=True,
                required_by_raw=True,
                typ=str,
                used_by_derived=True,
                used_by_raw=True,
                value=_get_value_or_default(kwargs, "owner", None, None),
            ),
            "owner_email": DatasetFields.Field(
                name="owner_email",
                description="Email of owner or of custodian of the dataset. The string may contain a list of emails, which should then be seperated by semicolons.",
                read_only=False,
                required_by_derived=False,
                required_by_raw=False,
                typ=str,
                used_by_derived=True,
                used_by_raw=True,
                value=_get_value_or_default(kwargs, "owner_email", None, None),
            ),
            "owner_group": DatasetFields.Field(
                name="owner_group",
                description="Defines the group which owns the data, and therefore has unrestricted access to this data. Usually a pgroup like p12151.",
                read_only=False,
                required_by_derived=True,
                required_by_raw=True,
                typ=str,
                used_by_derived=True,
                used_by_raw=True,
                value=_get_value_or_default(kwargs, "owner_group", None, None),
            ),
            "proposal_id": DatasetFields.Field(
                name="proposal_id",
                description="Identifier for the proposal that the dataset was produced for.",
                read_only=False,
                required_by_derived=False,
                required_by_raw=False,
                typ=str,
                used_by_derived=False,
                used_by_raw=True,
                value=_get_value_or_default(kwargs, "proposal_id", None, None),
            ),
            "sample_id": DatasetFields.Field(
                name="sample_id",
                description="Identifier for the sample that the dataset contains a measurement of.",
                read_only=False,
                required_by_derived=False,
                required_by_raw=False,
                typ=str,
                used_by_derived=False,
                used_by_raw=True,
                value=_get_value_or_default(kwargs, "sample_id", None, None),
            ),
            "shared_with": DatasetFields.Field(
                name="shared_with",
                description="List of users that the dataset has been shared with.",
                read_only=False,
                required_by_derived=False,
                required_by_raw=False,
                typ=List[str],
                used_by_derived=True,
                used_by_raw=True,
                value=_get_value_or_default(kwargs, "shared_with", None, None),
            ),
            "source_folder": DatasetFields.Field(
                name="source_folder",
                description="Absolute file path on file server containing the files of this dataset, e.g. /some/path/to/sourcefolder. In case of a single file dataset, e.g. HDF5 data, it contains the path up to, but excluding the filename.",
                read_only=False,
                required_by_derived=True,
                required_by_raw=True,
                typ=str,
                used_by_derived=True,
                used_by_raw=True,
                value=_get_value_or_default(kwargs, "source_folder", None, None),
            ),
            "source_folder_host": DatasetFields.Field(
                name="source_folder_host",
                description="DNS host name of file server hosting source_folder, optionally including protocol e.g. [protocol://]fileserver1.example.com",
                read_only=False,
                required_by_derived=False,
                required_by_raw=False,
                typ=str,
                used_by_derived=True,
                used_by_raw=True,
                value=_get_value_or_default(kwargs, "source_folder_host", None, None),
            ),
            "techniques": DatasetFields.Field(
                name="techniques",
                description="List of dicts with keys 'pid' and 'name' referring to techniques used to produce the data.",
                read_only=False,
                required_by_derived=False,
                required_by_raw=False,
                typ=List[dict],
                used_by_derived=True,
                used_by_raw=True,
                value=_get_value_or_default(kwargs, "techniques", None, None),
            ),
            "type": DatasetFields.Field(
                name="type",
                description="Dataset type. 'Derived' or 'Raw'",
                read_only=False,
                required_by_derived=True,
                required_by_raw=True,
                typ=DatasetType,
                used_by_derived=True,
                used_by_raw=True,
                value=_get_value_or_default(kwargs, "type", None, None),
            ),
            "updated_at": DatasetFields.Field(
                name="updated_at",
                description="Time when the object was last updated in the database.",
                read_only=True,
                required_by_derived=False,
                required_by_raw=False,
                typ=str,
                used_by_derived=True,
                used_by_raw=True,
                value=_get_value_or_default(_read_only, "updated_at", None, None),
            ),
            "updated_by": DatasetFields.Field(
                name="updated_by",
                description="Account name who last updated the object in the database.",
                read_only=True,
                required_by_derived=False,
                required_by_raw=False,
                typ=str,
                used_by_derived=True,
                used_by_raw=True,
                value=_get_value_or_default(_read_only, "updated_by", None, None),
            ),
            "used_software": DatasetFields.Field(
                name="used_software",
                description="A list of links to software repositories which uniquely identifies the software used and the version for producing the derived data.",
                read_only=False,
                required_by_derived=True,
                required_by_raw=True,
                typ=List[str],
                used_by_derived=True,
                used_by_raw=False,
                value=_get_value_or_default(kwargs, "used_software", None, None),
            ),
            "validation_status": DatasetFields.Field(
                name="validation_status",
                description="Defines a level of trust, e.g. a measure of how much data was verified or used by other persons.",
                read_only=False,
                required_by_derived=False,
                required_by_raw=False,
                typ=str,
                used_by_derived=True,
                used_by_raw=True,
                value=_get_value_or_default(kwargs, "validation_status", None, None),
            ),
            "version": DatasetFields.Field(
                name="version",
                description="Version of SciCat API used in creation of dataset.",
                read_only=True,
                required_by_derived=False,
                required_by_raw=False,
                typ=str,
                used_by_derived=True,
                used_by_raw=True,
                value=_get_value_or_default(_read_only, "version", None, None),
            ),
        }

    @property
    def access_groups(self) -> Optional[List[str]]:
        return self._fields["access_groups"]

    @access_groups.setter
    def access_groups(self, val: Optional[List[str]]):
        self._fields["access_groups"] = val

    @property
    def classification(self) -> Optional[str]:
        return self._fields["classification"]

    @classification.setter
    def classification(self, val: Optional[str]):
        self._fields["classification"] = val

    @property
    def contact_email(self) -> Optional[str]:
        return self._fields["contact_email"]

    @contact_email.setter
    def contact_email(self, val: Optional[str]):
        self._fields["contact_email"] = val

    @property
    def created_at(self) -> Optional[str]:
        return self._fields["created_at"]

    @property
    def created_by(self) -> Optional[str]:
        return self._fields["created_by"]

    @property
    def creation_location(self) -> Optional[str]:
        return self._fields["creation_location"]

    @creation_location.setter
    def creation_location(self, val: Optional[str]):
        self._fields["creation_location"] = val

    @property
    def creation_time(self) -> Optional[datetime]:
        return self._fields["creation_time"]

    @creation_time.setter
    def creation_time(self, val: Optional[datetime]):
        self._fields["creation_time"] = val

    @property
    def data_format(self) -> Optional[str]:
        return self._fields["data_format"]

    @data_format.setter
    def data_format(self, val: Optional[str]):
        self._fields["data_format"] = val

    @property
    def description(self) -> Optional[str]:
        return self._fields["description"]

    @description.setter
    def description(self, val: Optional[str]):
        self._fields["description"] = val

    @property
    def end_time(self) -> Optional[datetime]:
        return self._fields["end_time"]

    @end_time.setter
    def end_time(self, val: Optional[datetime]):
        self._fields["end_time"] = val

    @property
    def history(self) -> Optional[List[dict]]:
        return self._fields["history"]

    @property
    def input_datasets(self) -> Optional[List[str]]:
        return self._fields["input_datasets"]

    @input_datasets.setter
    def input_datasets(self, val: Optional[List[str]]):
        self._fields["input_datasets"] = val

    @property
    def instrument_group(self) -> Optional[str]:
        return self._fields["instrument_group"]

    @instrument_group.setter
    def instrument_group(self, val: Optional[str]):
        self._fields["instrument_group"] = val

    @property
    def instrument_id(self) -> Optional[str]:
        return self._fields["instrument_id"]

    @instrument_id.setter
    def instrument_id(self, val: Optional[str]):
        self._fields["instrument_id"] = val

    @property
    def investigator(self) -> Optional[str]:
        return self._fields["investigator"]

    @investigator.setter
    def investigator(self, val: Optional[str]):
        self._fields["investigator"] = val

    @property
    def is_published(self) -> Optional[bool]:
        return self._fields["is_published"]

    @is_published.setter
    def is_published(self, val: Optional[bool]):
        self._fields["is_published"] = val

    @property
    def job_log_data(self) -> Optional[str]:
        return self._fields["job_log_data"]

    @job_log_data.setter
    def job_log_data(self, val: Optional[str]):
        self._fields["job_log_data"] = val

    @property
    def job_parameters(self) -> Optional[dict]:
        return self._fields["job_parameters"]

    @job_parameters.setter
    def job_parameters(self, val: Optional[dict]):
        self._fields["job_parameters"] = val

    @property
    def keywords(self) -> Optional[List[str]]:
        return self._fields["keywords"]

    @keywords.setter
    def keywords(self, val: Optional[List[str]]):
        self._fields["keywords"] = val

    @property
    def license(self) -> Optional[str]:
        return self._fields["license"]

    @license.setter
    def license(self, val: Optional[str]):
        self._fields["license"] = val

    @property
    def meta(self) -> Optional[Dict]:
        return self._fields["meta"]

    @meta.setter
    def meta(self, val: Optional[Dict]):
        self._fields["meta"] = val

    @property
    def name(self) -> Optional[str]:
        return self._fields["name"]

    @name.setter
    def name(self, val: Optional[str]):
        self._fields["name"] = val

    @property
    def number_of_files(self) -> Optional[int]:
        return self._fields["number_of_files"]

    @property
    def number_of_files_archived(self) -> Optional[int]:
        return self._fields["number_of_files_archived"]

    @property
    def orcid_of_owner(self) -> Optional[str]:
        return self._fields["orcid_of_owner"]

    @orcid_of_owner.setter
    def orcid_of_owner(self, val: Optional[str]):
        self._fields["orcid_of_owner"] = val

    @property
    def owner(self) -> Optional[str]:
        return self._fields["owner"]

    @owner.setter
    def owner(self, val: Optional[str]):
        self._fields["owner"] = val

    @property
    def owner_email(self) -> Optional[str]:
        return self._fields["owner_email"]

    @owner_email.setter
    def owner_email(self, val: Optional[str]):
        self._fields["owner_email"] = val

    @property
    def owner_group(self) -> Optional[str]:
        return self._fields["owner_group"]

    @owner_group.setter
    def owner_group(self, val: Optional[str]):
        self._fields["owner_group"] = val

    @property
    def packed_size(self) -> Optional[int]:
        return self._fields["packed_size"]

    @property
    def pid(self) -> Optional[str]:
        return self._fields["pid"]

    @property
    def proposal_id(self) -> Optional[str]:
        return self._fields["proposal_id"]

    @proposal_id.setter
    def proposal_id(self, val: Optional[str]):
        self._fields["proposal_id"] = val

    @property
    def sample_id(self) -> Optional[str]:
        return self._fields["sample_id"]

    @sample_id.setter
    def sample_id(self, val: Optional[str]):
        self._fields["sample_id"] = val

    @property
    def shared_with(self) -> Optional[List[str]]:
        return self._fields["shared_with"]

    @shared_with.setter
    def shared_with(self, val: Optional[List[str]]):
        self._fields["shared_with"] = val

    @property
    def size(self) -> Optional[int]:
        return self._fields["size"]

    @property
    def source_folder(self) -> Optional[str]:
        return self._fields["source_folder"]

    @source_folder.setter
    def source_folder(self, val: Optional[str]):
        self._fields["source_folder"] = val

    @property
    def source_folder_host(self) -> Optional[str]:
        return self._fields["source_folder_host"]

    @source_folder_host.setter
    def source_folder_host(self, val: Optional[str]):
        self._fields["source_folder_host"] = val

    @property
    def techniques(self) -> Optional[List[dict]]:
        return self._fields["techniques"]

    @techniques.setter
    def techniques(self, val: Optional[List[dict]]):
        self._fields["techniques"] = val

    @property
    def type(self) -> Optional[DatasetType]:
        return self._fields["type"]

    @type.setter
    def type(self, val: Optional[DatasetType]):
        self._fields["type"] = val

    @property
    def updated_at(self) -> Optional[str]:
        return self._fields["updated_at"]

    @property
    def updated_by(self) -> Optional[str]:
        return self._fields["updated_by"]

    @property
    def used_software(self) -> Optional[List[str]]:
        return self._fields["used_software"]

    @used_software.setter
    def used_software(self, val: Optional[List[str]]):
        self._fields["used_software"] = val

    @property
    def validation_status(self) -> Optional[str]:
        return self._fields["validation_status"]

    @validation_status.setter
    def validation_status(self, val: Optional[str]):
        self._fields["validation_status"] = val

    @property
    def version(self) -> Optional[str]:
        return self._fields["version"]
