# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Generate dataset fields."""

import dataclasses
from pathlib import Path
from string import Template
from typing import Dict, List

from spec import Field, Spec
from templates import BANNER, load_template
from util import get_model_name, quote


def _write_dataset(target: Path, dataset: str):
    with target.open("w") as f:
        f.write(BANNER + dataset)


def _format_dataset_field_spec(fields: List[Field]) -> str:
    def format_single(template: Template, field: Field) -> str:
        return template.substitute(
            name=quote(field.name),
            description=quote(field.description),
            read_only=field.read_only,
            required_by_derived=field.required,
            required_by_raw=field.required,
            type=field.type,
            used_by_derived="derived" in field.extra.get("used", ()),
            used_by_raw="raw" in field.extra.get("used", ()),
        )

    tmpl = load_template("field_spec")
    return "[\n" + "\n".join(format_single(tmpl, f) for f in fields) + "\n    ]"


def _format_dataset_field_init_args(fields: List[Field]) -> str:
    return ",\n        ".join(
        f"{f.name}: Optional[{f.type}] = None"
        for f in fields
        if not f.read_only and not f.manual
    )


def _format_dataset_field_construction(field: Field) -> str:
    n = quote(field.name)
    d = field.default
    df = field.default_factory
    if field.read_only:
        formatted = f"{n}: _apply_default(_read_only.get({n}), {d}, {df})"
    else:
        formatted = f"{n}: _apply_default({field.name}, {d}, {df})"
    return "            " + formatted + ","


def _format_dataset_field_dict_construction(fields: List[Field]) -> str:
    return "\n".join(
        _format_dataset_field_construction(field)
        for field in fields
        if not field.manual
    )


def _format_properties(field: Field) -> str:
    getter = f'''    @property
    def {field.name}(self) -> Optional[{field.type}]:
        """{field.description}"""
        return self._fields[{quote(field.name)}]  # type: ignore[no-any-return]'''
    if field.read_only:
        return getter
    setter = f"""    @{field.name}.setter
    def {field.name}(self, val: Optional[{field.type}]) -> None:
        self._fields[{quote(field.name)}] = val"""
    return getter + "\n\n" + setter


def _format_make_model(typ: str, fields: List[Field]) -> str:
    checks = "\n".join(
        f"""    if self.{field.name} is not None:
        raise ValueError("'{field.name}' must not be set in {typ} datasets")"""
        for field in fields
        if typ not in field.extra.get("used", ())
    )
    construction = "\n        ".join(
        f"{get_model_name(field, typ)}=self.{field.name},"
        for field in fields
        if typ in field.extra.get("used", ())
    )
    formatted = f"""def _make_{typ}_model(self) -> {typ.capitalize()}Dataset:
{checks}
    return {("Derived" if typ == "derived" else "Raw")}Dataset(
        {construction}
    )"""
    return "    " + formatted.replace("\n", "\n    ")


def _format_fields_from_model(typ: str, fields: List[Field]) -> str:
    def format_assignments(read_only, indent):
        return ("\n" + " " * indent).join(
            f"{field.name}=model.{get_model_name(field, typ)},"
            for field in fields
            if typ in field.extra.get("used", ())
            and field.read_only == read_only
            and not field.manual
        )

    return f"""def _fields_from_{typ}_model(model) -> dict:
    return dict(
        _read_only=dict(
            {format_assignments(read_only=True, indent=12)}
        ),
        {format_assignments(read_only=False, indent=8)}
    )
"""


def _format_dataset_dataclass(spec: Spec) -> str:
    template = load_template("dataset")
    fields = sorted(spec.fields, key=lambda field: field.name)
    properties = "\n\n".join(
        _format_properties(field) for field in fields if not field.manual
    )
    return template.substitute(
        field_spec=_format_dataset_field_spec(fields),
        field_init_args=_format_dataset_field_init_args(fields),
        field_dict_construction=_format_dataset_field_dict_construction(fields),
        properties=properties,
        make_derived_model=_format_make_model("derived", fields),
        make_raw_model=_format_make_model("raw", fields),
        fields_from_derived_model=_format_fields_from_model("derived", fields),
        fields_from_raw_model=_format_fields_from_model("raw", fields),
    )


def _inline_base(spec: Spec, specs: Dict[str, Spec]) -> Spec:
    if spec.inherits == "BaseModel":
        return spec

    base = specs[spec.inherits]
    new_spec = Spec(
        name=spec.name, inherits="BaseModel", fields=spec.fields + base.fields
    )
    if base.inherits != "BaseModel":
        new_spec.inherits = base.inherits
        return _inline_base(new_spec, specs)
    return new_spec


def _add_used_extra(spec: Spec) -> Spec:
    """Make sure that every field has extra["used"]."""
    return dataclasses.replace(
        spec,
        fields=[
            dataclasses.replace(
                field, extra={"used": ["derived", "raw"], **field.extra}
            )
            for field in spec.fields
        ],
    )


def generate_dataset_fields(target: Path, specs: Dict[str, Spec]):
    _write_dataset(
        target,
        _format_dataset_dataclass(
            _add_used_extra(_inline_base(specs["Dataset"], specs))
        ),
    )
