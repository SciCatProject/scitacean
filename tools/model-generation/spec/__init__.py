# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Load model specification files."""

import dataclasses
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

SPEC_DIR = Path(__file__).resolve().parent

DEFAULTS = {
    "default": None,
    "default_factory": None,
    "manual": False,
    "model_name": None,  # equals field name
    "read_only": False,
    "required": False,
    "validation": None,
}


@dataclasses.dataclass
class Field:
    name: str
    default: Optional[Any]
    default_factory: Optional[str]
    description: str
    extra: Optional[dict]
    manual: bool
    model_name: str
    read_only: bool
    required: bool
    type: str
    validation: Optional[str]


@dataclasses.dataclass
class Spec:
    name: str
    inherits: str
    fields: List[Field]


def _load_raw(path: Path):
    with path.open("r") as f:
        return yaml.safe_load(f)


def _load_raw_specs() -> dict:
    return {
        spec["name"]: spec
        for spec in (
            _load_raw(path) for path in SPEC_DIR.iterdir() if path.suffix == ".yml"
        )
    }


def _get_defaults(spec: dict) -> dict:
    return {**DEFAULTS, **spec.get("default_values", {})}


def _apply_defaults_field(field: dict, defaults: dict) -> dict:
    new_field = dict(field)
    for key, default_value in defaults.items():
        if key not in new_field:
            if key == "model_name":
                new_field[key] = new_field["name"]
            else:
                new_field[key] = default_value
    return new_field


def _apply_defaults(spec: dict) -> dict:
    defaults = _get_defaults(spec)
    new_spec = dict(spec)
    new_spec["fields"] = [
        _apply_defaults_field(field, defaults) for field in spec["fields"]
    ]
    return new_spec


def _validate(spec: dict):
    for s in spec.values():
        for field in s["fields"]:
            if field.get("default") and field.get("default_factory"):
                raise ValueError("Cannot use both default and default_factory")


def _to_field_dataclass(field: dict) -> Field:
    field = dict(field)
    args = {
        f.name: field.pop(f.name)
        for f in dataclasses.fields(Field)
        if f.name != "extra"
    }
    extra = field
    return Field(**args, extra=extra)


def _to_spec_dataclasses(specs: dict) -> Dict[str, Spec]:
    return {
        name: Spec(
            name=name,
            inherits=spec.get("inherits", "BaseModel"),
            fields=[_to_field_dataclass(f) for f in spec["fields"]],
        )
        for name, spec in specs.items()
    }


def load_specs() -> Dict[str, Spec]:
    raw_specs = _load_raw_specs()
    defaults_applied = {name: _apply_defaults(spec) for name, spec in raw_specs.items()}
    _validate(defaults_applied)
    return _to_spec_dataclasses(defaults_applied)
