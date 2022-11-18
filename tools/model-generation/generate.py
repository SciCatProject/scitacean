# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen
"""Generate pydantic models and DatasetFields."""

import argparse
from pathlib import Path
from string import Template

from spec import load_specs

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"

GENERATED_BANNER = """##########################################
# This file was automatically generated. #
# Do not modify it directly!             #
##########################################
"""


# TODO validation
# TODO model validation shows model names (aliases?)


def load_template(name: str) -> Template:
    with open(TEMPLATE_DIR / f"{name}.py.template", "r") as f:
        return Template(f.read())


def write_model(target: Path, template: Template, models: list):
    with target.open("w") as f:
        f.write(GENERATED_BANNER + template.substitute(models="\n\n\n".join(models)))


def write_dataset(target: Path, dataset: str):
    with target.open("w") as f:
        f.write(GENERATED_BANNER + dataset)


def format_model_field(dataset_type: str, field: dict) -> str:
    name = field["model_name"]
    if isinstance(name, dict):
        name = name[dataset_type]
    typ = field["type"] if field["required"] else f"Optional[{field['type']}]"
    return f"    {name}: {typ}"


def generate_dataset_model(spec: dict, typ: str) -> str:
    name = ("Derived" if typ == "derived" else "Raw") + "Dataset"
    head = f"""class {name}(BaseModel):\n"""
    body = "\n".join(
        sorted(format_model_field(typ, f) for f in spec["fields"] if typ in f["used"])
    )
    return head + body


def field_is_required(field: dict, typ: str) -> bool:
    return (isinstance(field["required"], list) and typ in field["required"]) or field[
        "required"
    ]


def quote(s: str) -> str:
    if '"' in s:
        return f"'{s}'"
    return f'"{s}"'


def format_dataset_field_spec(fields: list) -> str:
    def format_single(template: Template, field: dict) -> str:
        name = quote(field["name"])
        return template.substitute(
            name=name,
            description=quote(field["description"]),
            read_only=field["read_only"],
            required_by_derived=field_is_required(field, "derived"),
            required_by_raw=field_is_required(field, "raw"),
            type=field["type"],
            used_by_derived="derived" in field["used"],
            used_by_raw="raw" in field["used"],
        )

    tmpl = load_template("field_spec")
    return "[\n" + "\n".join(format_single(tmpl, f) for f in fields) + "\n]"


def format_dataset_field_init_args(fields: list) -> str:
    def format_single(field: dict) -> str:
        return f"{field['name']}: Optional[{field['type']}] = None"

    return ",\n                 ".join(
        format_single(f)
        for f in fields
        if not f["read_only"] and not f["manual"] and f["name"] != "type"
    )


def format_dataset_field_construction(field: dict) -> str:
    n = quote(field["name"])
    d = field["default"]
    df = field["default_factory"]
    if field["read_only"]:
        formatted = f"{n}: _apply_default(_read_only.get({n}), {d}, {df})"
    else:
        formatted = f"{n}: _apply_default({field['name']}, {d}, {df})"
    return "            " + formatted + ","


def format_dataset_field_dict_construction(fields: list) -> str:
    return "\n".join(
        format_dataset_field_construction(field)
        for field in fields
        if not field["manual"] and field["name"] != "type"
    )


def format_properties(field: dict) -> str:
    getter = f'''    @property
    def {field["name"]}(self) -> Optional[{field["type"]}]:
        """{field["description"]}"""
        return self._fields[{quote(field["name"])}]'''
    if field["read_only"]:
        return getter
    setter = f"""    @{field["name"]}.setter
    def {field["name"]}(self, val: Optional[{field["type"]}]):
        self._fields[{quote(field["name"])}] = val"""
    return getter + "\n\n" + setter


def format_make_model(typ: str, fields: list) -> str:
    def get_model_name(field: dict):
        name = field["model_name"]
        if isinstance(name, dict):
            return name[typ]
        return name

    checks = "\n".join(
        f"""    if self.{field["name"]} is not None:
        raise ValueError("'{field["name"]}' must not be set in {typ} datasets")"""
        for field in fields
        if typ not in field["used"]
    )
    construction = "\n        ".join(
        f"{get_model_name(field)}=self.{field['name']},"
        for field in fields
        if typ in field["used"]
    )
    formatted = f"""def _make_{typ}_model(self):
{checks}
    return {("Derived" if typ == "derived" else "Raw")}Dataset(
        {construction}
    )"""
    return "    " + formatted.replace("\n", "\n    ")


def generate_dataset_dataclass(spec: dict) -> str:
    template = load_template("dataset")
    fields = sorted(spec["fields"], key=lambda field: field["name"])
    properties = "\n\n".join(
        format_properties(field) for field in fields if not field["manual"]
    )
    return template.substitute(
        field_spec=format_dataset_field_spec(fields),
        field_init_args=format_dataset_field_init_args(fields),
        field_dict_construction=format_dataset_field_dict_construction(fields),
        properties=properties,
        make_derived_model=format_make_model("derived", fields),
        make_raw_model=format_make_model("raw", fields),
    )


def parse_args():
    parser = argparse.ArgumentParser("Generate models and dataclasses")
    parser.add_argument("--src-dir", type=Path, help="Scitacean source directory")
    return parser.parse_args()


def main():
    args = parse_args()
    specs = load_specs()
    models = [
        generate_dataset_model(specs["Dataset"], typ=typ) for typ in ("derived", "raw")
    ]
    write_model(args.src_dir / "model.py", load_template("model"), models)
    write_dataset(
        args.src_dir / "_dataset_fields.py",
        generate_dataset_dataclass(specs["Dataset"]),
    )


if __name__ == "__main__":
    main()
