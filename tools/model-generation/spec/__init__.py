# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Load model specifications."""
import dataclasses
import re
import sys
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

import yaml

from .schema import Schema, SchemaField, load_schemas


@dataclasses.dataclass
class _UpDownSchemas:
    download: Schema
    upload: Optional[Schema]


@dataclasses.dataclass
class _DatasetSchemas:
    download: Schema
    upload_derived: Schema
    upload_raw: Schema


@dataclasses.dataclass
class SpecField:
    name: str
    scicat_name: str
    description: str
    type: str
    required: bool  # Required in upload.
    default: Optional[str] = None
    upload: bool = False
    download: bool = False
    validation: Optional[str] = None

    def full_type_for(self, kind: Literal["download", "upload", "user"]) -> str:
        return (
            self.type_for(kind) if self.required else f"Optional[{self.type_for(kind)}]"
        )

    def type_for(self, kind: Literal["download", "upload", "user"]) -> str:
        """Translate SciCat schema/DTO names into Scitacean model names."""
        for spec_name in _SCHEMA_GROUPS:
            if spec_name in self.type:
                if kind == "user":
                    name = _SCHEMA_GROUPS[spec_name][0] or _SCHEMA_GROUPS[spec_name][1]
                    return re.sub(str(name), f"{spec_name}", self.type)
                name = _SCHEMA_GROUPS[spec_name][0 if kind == "upload" else 1]
                return re.sub(str(name), f"{kind.capitalize()}{spec_name}", self.type)
        return self.type


@dataclasses.dataclass
class Spec:
    name: str
    download_name: str = dataclasses.field(init=False)
    upload_name: Optional[str] = dataclasses.field(init=False)
    fields: Dict[str, SpecField]

    def __post_init__(self) -> None:
        if _SCHEMA_GROUPS.get(self.name, (None, None))[0]:
            self.upload_name = f"Upload{self.name}"
        self.download_name = f"Download{self.name}"

    def fields_for(
        self, kind: Literal["download", "upload", "user"]
    ) -> List[SpecField]:
        return sorted(
            sorted(
                filter(
                    lambda field: (kind == "download" and field.download)
                    or (kind == "upload" and field.upload)
                    or (kind == "user"),
                    self.fields.values(),
                ),
                key=lambda field: field.name,
            ),
            key=lambda field: not field.required,
        )


@dataclasses.dataclass
class DatasetFieldConversion:
    func: str
    arg_type: str


@dataclasses.dataclass
class DatasetField(SpecField):
    conversion: Optional[DatasetFieldConversion] = None
    default: Optional[Any] = None
    manual: bool = False

    # These are only used for upload models.
    # For downloads, all fields should be considered as used.
    used_by_derived: bool = False
    used_by_raw: bool = False


@dataclasses.dataclass
class DatasetSpec(Spec):
    download_name: str = dataclasses.field(default="DownloadDataset", init=False)
    upload_name: Optional[str] = dataclasses.field(default="UploadDataset", init=False)
    fields: Dict[str, DatasetField]

    def dset_fields_for(
        self,
        kind: Literal["download", "upload", "user"],
        dset_type: Literal["derived", "raw"],
    ) -> List[DatasetField]:
        return list(
            filter(
                lambda field: field.used_by_derived
                if dset_type == "derived"
                else field.used_by_raw,
                self.fields_for(kind),
            )
        )

    def user_dset_fields(self, manual: Optional[bool] = None) -> List[DatasetField]:
        if manual is None:
            return list(self.fields.values())
        return [field for field in self.fields.values() if field.manual == manual]


_SCHEMA_GROUPS = {
    "Attachment": ("CreateAttachmentDto", "Attachment"),
    "OrigDatablock": ("CreateDatasetOrigDatablockDto", "OrigDatablock"),
    "Datablock": ("CreateDatasetDatablockDto", "Datablock"),
    "Lifecycle": (None, "LifecycleClass"),
    "Technique": ("TechniqueClass", "TechniqueClass"),
    "Relationship": ("RelationshipClass", "RelationshipClass"),
    "History": (None, "HistoryClass"),
    "DataFile": ("DataFile", "DataFile"),  # TODO everything marked as required
    "Instrument": (None, "Instrument"),
    "Sample": ("CreateSampleDto", "SampleClass"),
}


def _collect_schemas(
    schemas: Dict[str, Schema]
) -> Dict[str, Union[_UpDownSchemas, _DatasetSchemas]]:
    return {
        "Dataset": _DatasetSchemas(
            upload_derived=schemas["CreateDerivedDatasetDto"],
            upload_raw=schemas["CreateRawDatasetDto"],
            download=schemas["DatasetClass"],
        ),
        **{
            name: _UpDownSchemas(
                download=schemas[down_name],
                upload=schemas[up_name] if up_name else None,
            )
            for name, (up_name, down_name) in _SCHEMA_GROUPS.items()
        },
    }


def _camel_case_to_snake_case(string: str) -> str:
    """Convert a string from camelCase to snake_case."""

    def repl(match):
        return "_" + match[1].lower()

    return re.sub(r"([A-Z])", repl, string)


def _merge_upload_and_download_field(
    spec_name: str, download_field: SpecField, upload_field: SchemaField
) -> SpecField:
    if upload_field.type != download_field.type:
        sys.stderr.write(
            f"Mismatch in field {upload_field.name} of schemas "
            f"for upload and download of {spec_name}.\n"
            f" Upload:\n {upload_field}\n Download:\n {download_field}\n"
        )
    # not all DTOs / classes contain descriptions
    return dataclasses.replace(
        download_field,
        description=upload_field.description or download_field.description,
        upload=True,
        required=upload_field.required,
    )


def _merge_derived_and_raw_field(
    derived_field: DatasetField, raw_field: SchemaField
) -> DatasetField:
    for field_name in ("type", "default"):
        if getattr(raw_field, field_name) != getattr(derived_field, field_name):
            sys.stderr.write(
                f"Mismatch in field {derived_field.name} of raw and "
                "derived dataset schemas.\n"
                f" Derived:\n {derived_field}\n Raw:\n {raw_field}\n"
            )
    return dataclasses.replace(
        derived_field,
        used_by_raw=True,
        upload=True,
        required=derived_field.required or raw_field.required,
    )


def _build_spec(name: str, schemas: _UpDownSchemas) -> Spec:
    fields = {
        n: SpecField(
            name=_camel_case_to_snake_case(n),
            scicat_name=n,
            description=field.description,
            type=field.type,
            required=False,  # required is only for fields that users have to set.
            download=True,
        )
        for n, field in schemas.download.fields.items()
    }

    if schemas.upload is not None:
        for n, field in schemas.upload.fields.items():
            if n in fields:
                fields[n] = _merge_upload_and_download_field(name, fields[n], field)
            else:
                fields[n] = SpecField(
                    name=_camel_case_to_snake_case(field.name),
                    scicat_name=field.name,
                    description=field.description,
                    type=field.type,
                    required=field.required,
                    default=field.default,
                    upload=True,
                )

    return Spec(
        name=name,
        fields=fields,
    )


def _build_dataset_spec(name: str, schemas: _DatasetSchemas) -> DatasetSpec:
    fields = {
        n: DatasetField(
            name=_camel_case_to_snake_case(n),
            scicat_name=n,
            description=field.description,
            type=field.type,
            required=False,  # required is only for fields that users have to set.
            download=True,
        )
        for n, field in schemas.download.fields.items()
    }

    for n, field in schemas.upload_derived.fields.items():
        if n in fields:
            f = _merge_upload_and_download_field(name, fields[n], field)
            fields[n] = dataclasses.replace(
                f,
                used_by_derived=True,
                required=field.required,
                default=field.default,
                upload=True,
            )
        else:
            fields[n] = DatasetField(
                name=_camel_case_to_snake_case(field.name),
                scicat_name=field.name,
                description=field.description,
                type=field.type,
                required=field.required,
                default=field.default,
                download=False,
                used_by_derived=True,
            )

    for n, field in schemas.upload_raw.fields.items():
        if n in fields:
            fields[n] = _merge_derived_and_raw_field(fields[n], field)
        else:
            fields[n] = DatasetField(
                name=_camel_case_to_snake_case(field.name),
                scicat_name=field.name,
                description=field.description,
                type=field.type,
                required=field.required,
                default=field.default,
                upload=True,
                used_by_raw=True,
            )

    return DatasetSpec(
        name=name,
        fields=fields,
    )


@lru_cache
def _field_name_overrides() -> Dict[str, Dict[str, str]]:
    with open(Path(__file__).resolve().parent / "field-name-overrides.yml", "r") as f:
        return yaml.safe_load(f)


def _postprocess_field_names(spec: Spec) -> Spec:
    spec = deepcopy(spec)
    overrides = _field_name_overrides()
    for field_name, override in overrides.get(spec.name, {}).items():
        spec.fields[field_name].name = override
    return spec


@lru_cache
def _field_type_overrides() -> Dict[str, Dict[str, str]]:
    with open(Path(__file__).resolve().parent / "field-type-overrides.yml", "r") as f:
        return yaml.safe_load(f)


def _postprocess_field_types(spec: Spec) -> Spec:
    spec = deepcopy(spec)

    # Convert type names in the schema to Scitacean class names.
    for field in spec.fields.values():
        for class_name, model_names in _SCHEMA_GROUPS.items():
            if field.type in model_names:
                field.type = class_name

    overrides = _field_type_overrides()
    for field_name, override in overrides.get(spec.name, {}).items():
        spec.fields[field_name].type = override
    return spec


@lru_cache
def _field_validations() -> Dict[str, Dict[str, str]]:
    with open(Path(__file__).resolve().parent / "field-validations.yml", "r") as f:
        return yaml.safe_load(f)


def _assign_validations(spec: Spec) -> Spec:
    validations = _field_validations()
    if spec.name not in validations:
        return spec

    spec = deepcopy(spec)
    for field_name, validation in validations[spec.name].items():
        if validation == "size":
            spec.fields[field_name].type = "NonNegativeInt"
        else:
            spec.fields[field_name].validation = validation
    return spec


@lru_cache
def _dataset_field_customizations() -> Dict[str, Any]:
    with open(Path(__file__).resolve().parent / "dataset-fields.yml", "r") as f:
        return yaml.safe_load(f)


def _extend_dataset_fields(spec: DatasetSpec) -> DatasetSpec:
    customizations = _dataset_field_customizations()
    spec = deepcopy(spec)

    for name, field in spec.fields.items():
        field.manual = name in customizations["manual"]
        field.default = customizations["defaults"].get(name)
        if (conv := customizations["conversions"].get(name)) is not None:
            field.conversion = DatasetFieldConversion(**conv)
    return spec


def load_specs(schema_url: str) -> Dict[str, Any]:
    schemas = _collect_schemas(load_schemas(schema_url))
    dataset_schema = schemas.pop("Dataset")
    specs = {
        "Dataset": _extend_dataset_fields(
            _build_dataset_spec("Dataset", dataset_schema)
        ),
        **{name: _build_spec(name, updown) for name, updown in schemas.items()},
    }
    return {
        name: _assign_validations(
            _postprocess_field_types(_postprocess_field_names(spec))
        )
        for name, spec in specs.items()
    }
