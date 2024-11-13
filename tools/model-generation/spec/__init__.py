# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Load model specifications."""

import dataclasses
import re
import sys
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml

from .schema import Schema, SchemaField, load_schemas


@dataclasses.dataclass
class _UpDownSchemas:
    download: Schema
    upload: Schema | None


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
    default: str | None = None
    upload: bool = False
    download: bool = False
    validation: str | None = None

    def full_type_for(self, kind: Literal["download", "upload", "user"]) -> str:
        return (
            self.type_for(kind)
            if self.required and kind != "download"
            else f"{self.type_for(kind)} | None"
        )

    def type_for(self, kind: Literal["download", "upload", "user"]) -> str:
        """Translate SciCat schema/DTO names into Scitacean model names."""
        if kind == "upload":
            prefix = "Upload"
        elif kind == "download":
            prefix = "Download"
        else:
            prefix = ""

        for spec_name in _SCHEMA_GROUPS:
            if spec_name in self.type:
                return re.sub(str(spec_name), f"{prefix}{spec_name}", self.type)
        return self.type


@dataclasses.dataclass
class Spec:
    name: str
    download_name: str = dataclasses.field(init=False)
    upload_name: str | None = dataclasses.field(init=False)
    fields: dict[str, SpecField]
    masked_fields_download: dict[str, SpecField] = dataclasses.field(init=False)
    masked_fields_upload: dict[str, SpecField] = dataclasses.field(init=False)

    def __post_init__(self) -> None:
        if _SCHEMA_GROUPS.get(self.name, (None, None))[0]:
            self.upload_name = f"Upload{self.name}"
        else:
            self.upload_name = None
        self.download_name = f"Download{self.name}"
        self.masked_fields_download = {}
        self.masked_fields_upload = {}

    def fields_for(
        self, kind: Literal["download", "upload", "user"]
    ) -> list[SpecField]:
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
    conversion: DatasetFieldConversion | None = None
    default: Any | None = None
    manual: bool = False

    # These are only used for upload models.
    # For downloads, all fields should be considered as used.
    used_by_derived: bool = False
    used_by_raw: bool = False


@dataclasses.dataclass
class DatasetSpec(Spec):
    download_name: str = dataclasses.field(default="DownloadDataset", init=False)
    upload_name: str | None = dataclasses.field(default="UploadDataset", init=False)
    fields: dict[str, DatasetField]

    def dset_fields_for(
        self,
        kind: Literal["download", "upload", "user"],
        dset_type: Literal["derived", "raw"],
    ) -> list[DatasetField]:
        return list(
            filter(
                lambda field: field.used_by_derived
                if dset_type == "derived"
                else field.used_by_raw,
                self.fields_for(kind),
            )
        )

    def user_dset_fields(self, manual: bool | None = None) -> list[DatasetField]:
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
    "DataFile": ("DataFile", "DataFile"),
    "Instrument": (None, "Instrument"),
    "Sample": ("CreateSampleDto", "SampleClass"),
}


def _collect_schemas(
    schemas: dict[str, Schema],
) -> dict[str, _UpDownSchemas | _DatasetSchemas]:
    return {
        "Dataset": _DatasetSchemas(
            upload_derived=schemas["CreateDerivedDatasetObsoleteDto"],
            upload_raw=schemas["CreateRawDatasetObsoleteDto"],
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


def _get_common_field_attr(
    name: str, allow_mismatch: bool = False, **fields: SchemaField
) -> Any:
    source_key = None
    val = None
    for key, field in fields.items():
        if field is None:
            continue
        if val is None:
            source_key = key
            val = getattr(field, name)
        else:
            if not allow_mismatch and val != getattr(field, name):
                sys.stderr.write(
                    f"Mismatch in field {name}:\n"
                    f" {source_key}:\n {val}\n {key}:\n {getattr(field, name)}\n"
                )
    return val


def _merge_field(
    name: str, download: SchemaField | None, upload: SchemaField | None
) -> SpecField:
    fields = {"download": download, "upload": upload}
    return SpecField(
        name=_camel_case_to_snake_case(_get_common_field_attr("name", **fields)),
        scicat_name=name,
        description=_get_common_field_attr(
            "description", allow_mismatch=True, **fields
        ),
        type=_get_common_field_attr("type", **fields),
        required=upload is not None and upload.required,
        download=download is not None,
        upload=upload is not None,
    )


def _build_spec(name: str, schemas: _UpDownSchemas) -> Spec:
    field_names = set(schemas.download.fields.keys())
    if schemas.upload is not None:
        field_names |= set(schemas.upload.fields.keys())
    fields = {
        name: _merge_field(
            name,
            download=schemas.download.fields.get(name),
            upload=schemas.upload.fields.get(name)
            if schemas.upload is not None
            else None,
        )
        for name in field_names
    }
    return Spec(
        name=name,
        fields=fields,
    )


def _merge_dataset_field(
    name: str,
    download: SchemaField | None,
    raw_upload: SchemaField | None,
    derived_upload: SchemaField | None,
) -> DatasetField:
    fields = {
        "download": download,
        "raw_upload": raw_upload,
        "derived_upload": derived_upload,
    }
    required = (raw_upload is not None and raw_upload.required) or (
        derived_upload is not None and derived_upload.required
    )
    return DatasetField(
        name=_camel_case_to_snake_case(_get_common_field_attr("name", **fields)),
        scicat_name=name,
        description=_get_common_field_attr(
            "description", allow_mismatch=True, **fields
        ),
        type=_get_common_field_attr("type", **fields),
        required=required,
        download=download is not None,
        upload=raw_upload is not None or derived_upload is not None,
        used_by_derived=derived_upload is not None,
        used_by_raw=raw_upload is not None,
    )


def _build_dataset_spec(name: str, schemas: _DatasetSchemas) -> DatasetSpec:
    field_names = (
        schemas.download.fields.keys()
        | schemas.upload_raw.fields.keys()
        | schemas.upload_derived.fields.keys()
    )
    fields = {
        name: _merge_dataset_field(
            name,
            download=schemas.download.fields.get(name),
            raw_upload=schemas.upload_raw.fields.get(name),
            derived_upload=schemas.upload_derived.fields.get(name),
        )
        for name in field_names
    }
    return DatasetSpec(
        name=name,
        fields=fields,
    )


@lru_cache
def _masked_fields() -> dict[str, list[str]]:
    with open(Path(__file__).resolve().parent / "masked-fields.yml") as f:
        return yaml.safe_load(f)


def _mask_fields(spec: Spec) -> Spec:
    spec = deepcopy(spec)
    masked = _masked_fields()
    for field_name in masked.get(spec.name, []):
        if isinstance(field_name, dict):
            ((field_name, updown),) = field_name.items()
            if updown == "upload":
                spec.fields[field_name].upload = False
                spec.masked_fields_upload[field_name] = spec.fields[field_name]
            elif updown == "download":
                spec.masked_fields_download[field_name] = spec.fields[field_name]
            else:
                raise ValueError("Invalid mask value")
        else:
            spec.masked_fields_upload[field_name] = spec.fields[field_name]
            spec.masked_fields_download[field_name] = spec.fields.pop(field_name)
    return spec


@lru_cache
def _field_name_overrides() -> dict[str, dict[str, str]]:
    with open(Path(__file__).resolve().parent / "field-name-overrides.yml") as f:
        return yaml.safe_load(f)


def _postprocess_field_names(spec: Spec) -> Spec:
    spec = deepcopy(spec)
    overrides = _field_name_overrides()
    for field_name, override in overrides.get(spec.name, {}).items():
        spec.fields[field_name].name = override
    return spec


@lru_cache
def _field_type_overrides() -> dict[str, dict[str, str]]:
    with open(Path(__file__).resolve().parent / "field-type-overrides.yml") as f:
        return yaml.safe_load(f)


def _postprocess_field_types(spec: Spec) -> Spec:
    spec = deepcopy(spec)

    # Convert type names in the schema to Scitacean class names.
    for field in spec.fields.values():
        for class_name, model_names in _SCHEMA_GROUPS.items():
            for name in model_names:
                if name and name in field.type:
                    field.type = re.sub(name, class_name, field.type)

    overrides = _field_type_overrides()
    for field_name, override in overrides.get(spec.name, {}).items():
        spec.fields[field_name].type = override
    return spec


@lru_cache
def _field_validations() -> dict[str, dict[str, str]]:
    with open(Path(__file__).resolve().parent / "field-validations.yml") as f:
        return yaml.safe_load(f)


def _assign_validations(spec: Spec) -> Spec:
    validations = _field_validations()
    if spec.name not in validations:
        return spec

    spec = deepcopy(spec)
    for field_name, validation in validations[spec.name].items():
        if field_name in spec.fields:
            if validation == "size":
                spec.fields[field_name].type = "NonNegativeInt"
            else:
                spec.fields[field_name].validation = validation
    return spec


@lru_cache
def _dataset_field_customizations() -> dict[str, Any]:
    with open(Path(__file__).resolve().parent / "dataset-fields.yml") as f:
        return yaml.safe_load(f)


def _extend_dataset_fields(spec: DatasetSpec) -> DatasetSpec:
    customizations = _dataset_field_customizations()
    spec = deepcopy(spec)

    for name, field in spec.fields.items():
        field.manual = name in customizations["manual"]
        field.default = customizations["defaults"].get(name)
        if (conv := customizations["conversions"].get(name)) is not None:
            field.conversion = DatasetFieldConversion(**conv)
        if name in customizations["extra_read_only"]:
            field.upload = False
    return spec


def load_specs(schema_url: str) -> dict[str, Any]:
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
            _postprocess_field_types(_postprocess_field_names(_mask_fields(spec)))
        )
        for name, spec in specs.items()
    }
