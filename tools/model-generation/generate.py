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


def load_template(name: str) -> Template:
    filename = {
        "model": "model.py.template",
        "dataset": "dataset.py.template",
        "field_construction": "field_construction.py.template",
    }[name]
    with open(TEMPLATE_DIR / filename, "r") as f:
        return Template(f.read())


def write_model(target: Path, template: Template, models: list):
    with target.open("w") as f:
        f.write(GENERATED_BANNER + template.substitute(models="\n\n\n".join(models)))


def write_dataset(target: Path, dataset: str):
    with target.open("w") as f:
        f.write(GENERATED_BANNER + dataset)


def format_model_field(field: dict) -> str:
    return "    {name}: {typ}".format(
        name=field["name"],
        typ=field["type"] if field["required"] else f"Optional[{field['type']}]",
    )


def generate_dataset_model(spec: dict, typ: str) -> str:
    name = ("Derived" if typ == "derived" else "Raw") + "Dataset"
    head = f"""class {name}(pydantic.BaseModel):\n"""
    body = "\n".join(
        map(format_model_field, sorted(spec["fields"], key=lambda field: field["name"]))
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


def format_dataset_field_construction(template: Template, field: dict) -> str:
    name = quote(field["name"])
    source = "_read_only" if field["read_only"] else "kwargs"
    formatted = template.substitute(
        name=name,
        description=quote(field["description"]),
        read_only=field["read_only"],
        required_by_derived=field_is_required(field, "derived"),
        required_by_raw=field_is_required(field, "raw"),
        typ=field["type"],
        used_by_derived="derived" in field["used"],
        used_by_raw="raw" in field["used"],
        value="_get_value_or_default({s}, {k}, {d}, {df})".format(
            s=source,
            k=name,
            d=field["default"],
            df=field["default_factory"],
        ),
    )
    indent = "            "
    return indent + formatted.replace("\n", "\n" + indent)


def format_properties(field: dict) -> str:
    getter = f"""    @property
    def {field["name"]}(self) -> Optional[{field["type"]}]:
        return self._fields[{quote(field["name"])}]"""
    if field["read_only"]:
        return getter
    setter = f"""    @{field["name"]}.setter
    def {field["name"]}(self, val: Optional[{field["type"]}]):
        self._fields[{quote(field["name"])}] = val"""
    return getter + "\n\n" + setter


def generate_dataset_dataclass(spec: dict) -> str:
    template = load_template("dataset")
    field_construction_template = load_template("field_construction")
    fields = sorted(spec["fields"], key=lambda field: field["name"])
    field_dict_construction = (
        "{\n"
        + "\n".join(
            format_dataset_field_construction(field_construction_template, field)
            for field in fields
            if not field["manual"]
        )
        + "\n        }"
    )
    properties = "\n\n".join(format_properties(field) for field in fields)
    return template.substitute(
        field_dict_construction=field_dict_construction, properties=properties
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
