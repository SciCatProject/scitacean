# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Load model specifications."""
import dataclasses
import sys
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional, Union

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
    description: str
    type: str
    required: bool  # Required in upload.
    default: Optional[str] = None
    upload: bool = False
    download: bool = False
    validation: Optional[str] = None


@dataclasses.dataclass
class Spec:
    name: str
    fields: Dict[str, SpecField]


@dataclasses.dataclass
class DatasetField(SpecField):
    used_by_derived: bool = False
    used_by_raw: bool = False


@dataclasses.dataclass
class DatasetSpec(Spec):
    fields: Dict[str, DatasetField]


_SCHEMA_GROUPS = {
    "Attachment": ("CreateAttachmentDto", "Attachment"),
    "OrigDatablock": ("CreateDatasetOrigDatablockDto", "OrigDatablock"),
    "Datablock": ("CreateDatasetDatablockDto", "Datablock"),
    "Lifecycle": (None, "LifecycleClass"),
    "Technique": (None, "TechniqueClass"),
    "Relationship": ("RelationshipClass", "RelationshipClass"),
    "History": (None, "HistoryClass"),
    "DataFile": ("DataFile", "DataFile"),
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
            name=n,
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
                    name=field.name,
                    description=field.description,
                    type=field.type,
                    required=field.required,
                    default=field.default,
                    upload=True,
                )

    return Spec(name=name, fields=fields)


def _build_dataset_spec(name: str, schemas: _DatasetSchemas) -> DatasetSpec:
    fields = {
        n: DatasetField(
            name=n,
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
                name=field.name,
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
                name=field.name,
                description=field.description,
                type=field.type,
                required=field.required,
                default=field.default,
                upload=True,
                used_by_raw=True,
            )

    return DatasetSpec(name=name, fields=fields)


@lru_cache
def _field_type_overrides() -> Dict[str, Dict[str, str]]:
    with open(Path(__file__).resolve().parent / "field-type-overrides.yml", "r") as f:
        return yaml.safe_load(f)


def _postprocess_field_types(spec: Spec) -> Spec:
    overrides = _field_type_overrides()
    if spec.name not in overrides:
        return spec

    spec = deepcopy(spec)
    for field_name, override in overrides[spec.name].items():
        spec.fields[field_name].type = override
    return spec


def load_specs(schema_url: str) -> Dict[str, Any]:
    schemas = _collect_schemas(load_schemas(schema_url))
    dataset_schema = schemas.pop("Dataset")
    specs = {
        "Dataset": _build_dataset_spec("Dataset", dataset_schema),
        **{name: _build_spec(name, updown) for name, updown in schemas.items()},
    }
    return {name: _postprocess_field_types(spec) for name, spec in specs.items()}
