# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Generate pydantic models."""

import dataclasses
from graphlib import TopologicalSorter
from pathlib import Path
from typing import Dict, List

from spec import Field, Spec
from templates import BANNER, load_template
from util import quote


def _write_model(target: Path, models: list):
    with target.open("w") as f:
        f.write(
            BANNER + load_template("model").substitute(models="\n\n\n".join(models))
        )


def _format_model_field(field: Field) -> str:
    name = field.model_name
    typ = field.type if field.required else f"Optional[{field.type}]"
    return f"    {name}: {typ}"


def _format_validator(validator: str, fields: List[Field]) -> str:
    to_validate = [
        field.model_name for field in fields if field.validation == validator
    ]
    if not to_validate:
        return ""
    return f"""    @pydantic.validator({", ".join(map(quote, to_validate))})
    def _validate_{validator}(cls, value: Any) -> Any:
        return _validate_{validator}(value)"""


def _format_validators(fields: List[Field]) -> str:
    res = "\n\n".join(
        (
            _format_validator("emails", fields),
            _format_validator("size", fields),
            _format_validator("orcid", fields),
        )
    )
    return "\n    " + res.strip()


def _format_model(spec: Spec) -> str:
    head = f"""class {spec.name}({spec.inherits}):\n"""
    fields = sorted(
        sorted(spec.fields, key=lambda f: f.name), key=lambda f: not f.required
    )
    attributes = "\n".join(_format_model_field(field) for field in fields)
    validations = _format_validators(fields)
    return head + attributes + ("\n" + validations if validations.strip() else "")


def _make_dataset_type(spec: Spec, typ: str) -> Spec:
    def handle_field(field: Field) -> Field:
        return dataclasses.replace(
            field,
            model_name=field.model_name[typ]
            if isinstance(field.model_name, dict)
            else field.model_name,
        )

    return Spec(
        name="DerivedDataset" if typ == "derived" else "RawDataset",
        inherits=spec.inherits,
        fields=[
            handle_field(field) for field in spec.fields if typ in field.extra["used"]
        ],
    )


def _split_dataset(specs: Dict[str, Spec]) -> Dict[str, Spec]:
    specs = dict(specs)
    dataset = specs.pop("Dataset")
    specs["DerivedDataset"] = _make_dataset_type(dataset, "derived")
    specs["RawDataset"] = _make_dataset_type(dataset, "raw")
    return specs


def generate_models(target: Path, specs: Dict[str, Spec]):
    specs = _split_dataset(specs)
    spec_order = TopologicalSorter(
        {
            key: {val.inherits}
            for key, val in sorted(specs.items(), key=lambda kv: kv[0])
        },
    ).static_order()
    _write_model(
        target,
        [_format_model(specs[name]) for name in spec_order if name != "BaseModel"],
    )
