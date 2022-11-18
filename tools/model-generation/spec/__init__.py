# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen
"""Load model specification files."""

from pathlib import Path

import yaml

SPEC_DIR = Path(__file__).resolve().parent


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


def _inline_base(spec: dict, specs: dict) -> dict:
    if "inherits" not in spec:
        return spec

    base = specs[spec["inherits"]]
    new_spec = {**spec, "fields": spec["fields"] + base["fields"]}
    del new_spec["inherits"]
    if "inherits" in base:
        new_spec["inherits"] = base["inherits"]
        return _inline_base(new_spec, specs)
    return new_spec


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
    if "default_values" not in spec:
        return spec
    new_spec = dict(spec)
    defaults = new_spec.pop("default_values")
    new_spec["fields"] = [
        _apply_defaults_field(field, defaults) for field in spec["fields"]
    ]
    return new_spec


def _validate(spec: dict):
    for s in spec.values():
        for field in s["fields"]:
            if field.get("default") and field.get("default_factory"):
                raise ValueError("Cannot use both default and default_factory")


def load_specs() -> dict:
    raw_specs = _load_raw_specs()
    inlined = {name: _inline_base(spec, raw_specs) for name, spec in raw_specs.items()}
    processed = {name: _apply_defaults(spec) for name, spec in inlined.items()}
    _validate(processed)
    return processed
