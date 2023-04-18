# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Process and merge dataset specs."""

import dataclasses
import sys
from typing import Dict, Optional

from .schemas import Schema, SchemaField


@dataclasses.dataclass
class DatasetSchemas:
    create_derived: Schema
    create_raw: Schema
    get: Schema


@dataclasses.dataclass
class DatasetField:
    name: str
    description: str
    type: str
    required: bool
    default: Optional[str]
    used_by_derived: bool
    used_by_raw: bool
    readonly: bool


@dataclasses.dataclass
class DatasetSpec:
    fields: Dict[str, DatasetField]


def get_dataset_schemas(schemas: Dict[str, Schema]) -> DatasetSchemas:
    return DatasetSchemas(
        create_derived=schemas["CreateDerivedDatasetDto"],
        create_raw=schemas["CreateRawDatasetDto"],
        get=schemas["DatasetClass"],
    )


def merge_raw_field(base_field: DatasetField, raw_field: SchemaField) -> DatasetField:
    for field in dataclasses.fields(raw_field):
        if getattr(raw_field, field.name) != getattr(base_field, field.name):
            sys.stderr.write(
                f"Mismatch in field {field.name} of raw and derived "
                "dataset schemas.\n"
                f"Derived:\n{base_field}\nRaw:\n{raw_field}\n"
            )
    return dataclasses.replace(base_field, used_by_raw=True)


def merge_get_field(base_field: DatasetField, get_field: SchemaField) -> DatasetField:
    if base_field.type != get_field.type:
        sys.stderr.write(
            f"Mismatch in field {base_field.name} of dataset schemas "
            "for creation and download.\n"
            f"Create:\n{base_field}\nDownload:\n{get_field}\n"
        )
    # not all DTOs / classes contain descriptions
    return dataclasses.replace(
        base_field, description=base_field.description or get_field.description
    )


def merged_dataset_spec(schemas: DatasetSchemas) -> DatasetSpec:
    fields = {
        name: DatasetField(
            name=field.name,
            description=field.description,
            type=field.type,
            required=field.required,
            default=field.default,
            used_by_derived=True,
            used_by_raw=False,
            readonly=False,
        )
        for name, field in schemas.create_derived.fields.items()
    }

    for name, field in schemas.create_raw.fields.items():
        if name in fields:
            fields[name] = merge_raw_field(fields[name], field)
        else:
            fields[name] = DatasetField(
                name=field.name,
                description=field.description,
                type=field.type,
                required=field.required,
                default=field.default,
                used_by_derived=False,
                used_by_raw=True,
                readonly=False,
            )

    for name, field in schemas.get.fields.items():
        if name in fields:
            fields[name] = merge_get_field(fields[name], field)
        else:
            fields[name] = DatasetField(
                name=field.name,
                description=field.description,
                type=field.type,
                required=False,  # required is only for fields that users have to set.
                default=field.default,
                used_by_derived=True,
                used_by_raw=True,
                readonly=True,
            )

    return DatasetSpec(fields=fields)
