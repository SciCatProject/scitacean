# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import re
from string import Template
import sys
from typing import Optional

from pyscicat.model import DerivedDataset, RawDataset

OMIT = (
    "number_of_files",
    "number_of_files_archived",
    "packed_size",
    "size",
    "scientific_metadata",
)


def read_template():
    with open(Path(__file__).parent / "templates/dataset_fields.py.in", "r") as f:
        return Template(f.read())


def camel_case_to_snake_case(s):
    return s[0] + re.sub(r"[A-Z]", lambda m: "_" + m[0].lower(), s[1:])


def normalize_derived_name(name):
    try:
        return {"investigator": "investigator", "type": "dataset_type"}[name]
    except KeyError:
        return camel_case_to_snake_case(name)


def normalize_raw_name(name):
    try:
        return {"principalInvestigator": "investigator", "type": "dataset_type"}[name]
    except KeyError:
        return camel_case_to_snake_case(name)


def join_fields():
    fields = {
        normalize_derived_name(field.name): Field.make(
            field, in_derived=field.name, in_raw=None
        )
        for field in DerivedDataset.__fields__.values()
    }
    for field in RawDataset.__fields__.values():
        name = normalize_raw_name(field.name)
        if name in fields:
            fields[name].name_in_raw = field.name
            # Must be optional if either one is optional
            fields[name].optional |= field.allow_none
        else:
            fields[name] = Field.make(field, in_derived=None, in_raw=field.name)

    # Fields present in only one model must be optional here.
    for field in fields.values():
        if not field.name_in_derived or not field.name_in_raw:
            field.optional = True
    return fields


@dataclass
class Field:
    typ: str
    optional: bool
    name_in_derived: Optional[str]
    name_in_raw: Optional[str]

    @classmethod
    def make(cls, pydantic_field, in_derived, in_raw) -> Field:
        # str of types produces, e.g., <class 'str'> which is not a valid
        # type annotation. So use __name__ in those cases but str(outer_typ)
        # for generic types like typing.List[str].
        outer_typ = pydantic_field.outer_type_
        typ = outer_typ.__name__ if isinstance(outer_typ, type) else str(outer_typ)

        return Field(
            typ=typ,
            optional=pydantic_field.allow_none,
            name_in_derived=in_derived,
            name_in_raw=in_raw,
        )

    @property
    def full_typ(self) -> str:
        return f"Optional[{self.typ}]" if self.optional else self.typ


def generate_omitted_arg_list(fields):
    return (",\n" + " " * 8).join(f"{name}: {fields[name].full_typ}" for name in OMIT)


def generate_omitted_assignment():
    return "\n".join(
        f'        mapped[name_mapping["{name}"]] = {name}' for name in OMIT
    )


def generate_name_in_derived_map():
    indent = " " * 4
    return (
        "{\n"
        + ",\n".join(
            indent + f'"{normalize_derived_name(field.name)}": "{field.name}"'
            for field in DerivedDataset.__fields__.values()
        )
        + ",\n}"
    )


def generate_name_in_raw_map():
    indent = " " * 4
    return (
        "{\n"
        + ",\n".join(
            indent + f'"{normalize_raw_name(field.name)}": "{field.name}"'
            for field in RawDataset.__fields__.values()
        )
        + ",\n}"
    )


def generate_field_spec(name, field):
    default = " = None" if field.optional else ""
    return f"{name}: {field.full_typ}{default}"


def generate_fields_spec(fields):
    return "\n".join(
        f"    {generate_field_spec(name, field)}"
        for name, field in sorted(
            sorted(fields.items(), key=lambda t: t[0]), key=lambda t: t[1].optional
        )
        if name not in OMIT
    )


def generate_dataset():
    template = read_template()
    fields = join_fields()
    src = (
        "# This file was generated by tools/generate_dataset_fields.py\n"
        + template.substitute(
            name_to_derived_map=generate_name_in_derived_map(),
            name_to_raw_map=generate_name_in_raw_map(),
            omitted_fields="(\n" + ",\n".join(f'    "{o}"' for o in OMIT) + "\n)",
            dataclass_fields=generate_fields_spec(fields),
            omitted_arg_list=generate_omitted_arg_list(fields),
            omitted_assignment=generate_omitted_assignment(),
        )
    )
    # TODO conversion to model shows camelCase names in model if validation fails
    return src


def main():
    if len(sys.argv) != 2:
        print("Usage: generate_dataset_fields.py OUTFILE")
        sys.exit(1)
    with open(sys.argv[1], "w") as f:
        f.write(generate_dataset())


if __name__ == "__main__":
    main()