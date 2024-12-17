# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Load schemas from a SciCat API."""

import dataclasses
from typing import Any

import httpx


@dataclasses.dataclass
class SchemaField:
    name: str
    description: str
    type: str
    required: bool
    default: str | None


@dataclasses.dataclass
class Schema:
    name: str
    fields: dict[str, SchemaField]


def parse_field_type(spec: dict[str, Any]):
    if "allOf" in spec:
        if len(spec["allOf"]) != 1:
            raise ValueError("More than one alternative type in 'allOf'")
        return parse_field_type(spec["allOf"][0])
    if "$ref" in spec:
        return spec["$ref"].rsplit("/", 1)[1]
    if spec["type"] == "number":
        return "int"
    if spec["type"] == "string":
        if spec.get("format", "") == "date-time":
            return "datetime"
        return "str"
    if spec["type"] == "boolean":
        return "bool"
    if spec["type"] == "array":
        return "list[{}]".format(parse_field_type(spec["items"]))
    if spec["type"] == "object":
        return "dict[str, Any]"
    raise ValueError(f"Unknown field type: {spec['type']}")


def parse_schema_fields(spec: dict[str, Any]) -> dict[str, SchemaField]:
    return {
        name: SchemaField(
            name=name,
            description=field_spec.get("description", ""),
            type=parse_field_type(field_spec),
            required=name in spec.get("required", ()),
            default=field_spec.get("default", None),
        )
        for name, field_spec in spec["properties"].items()
    }


def parse_schemas(spec: dict[str, Any]) -> dict[str, Schema]:
    schemas = {}
    for name, field_spec in spec.items():
        print(f"Parsing schema {name}")  # noqa: T201
        schemas[name] = Schema(name=name, fields=parse_schema_fields(field_spec))
    return schemas


def fetch_specs(url: str) -> dict[str, Any]:
    """Download the raw schema JSON from the API.

    ``url`` needs to point to a 'json-explorer' of a SciCat backend with version >= 4.
    E.g. ``http://localhost:3000/explorer-json`` for a locally running instance.
    """
    response = httpx.get(url, timeout=10)
    if not response.is_success:
        raise RuntimeError(
            f"Failed to fetch specs: {response.status_code} {response.reason_phrase}"
        )
    return response.json()


def load_schemas(url: str) -> dict[str, Schema]:
    spec_json = fetch_specs(url)
    return parse_schemas(spec_json["components"]["schemas"])
