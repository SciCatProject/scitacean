# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)

"""Generate Python classes for SciCat models."""

import subprocess
from pathlib import Path
from typing import Dict

from jinja2 import Environment, FileSystemLoader, Template
from spec import DatasetSpec, Spec, load_specs
from templates import BANNER

# Set to the URL of the JSON schema.
# See the README for details.
SCHEMA_URL = "http://localhost:3000/explorer-json"

# The root directory of the Scitacean repository.
# Modify this if the current file has moved.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
# Output file for model.py
MODEL_OUT_PATH = REPO_ROOT / "src" / "scitacean" / "model.py"
# Output file for _dataset_fields.py
DSET_FIELDS_OUT_PATH = REPO_ROOT / "src" / "scitacean" / "_dataset_fields.py"


def quote(s: str) -> str:
    if '"' in s:
        return f"'{s}'"
    return f'"{s}"'


def _template(name: str) -> Template:
    environment = Environment(  # noqa: S701
        loader=FileSystemLoader(Path(__file__).resolve().parent / "templates/"),
    )
    environment.filters["quote"] = quote
    return environment.get_template(f"{name}.py.jinja")


def _model_template() -> Template:
    return _template("model")


def _dataset_fields_template() -> Template:
    return _template("dataset_fields")


def generate_models(specs: Dict[str, Spec]) -> str:
    specs = dict(specs)
    dset_spec = specs.pop("Dataset")
    return _model_template().render(banner=BANNER, specs=specs, dset_spec=dset_spec)


def generate_dataset_fields(dset_spec: DatasetSpec) -> str:
    return _dataset_fields_template().render(banner=BANNER, spec=dset_spec)


def format_with_black(path: Path) -> None:
    # Root of Scitacean repo
    base_path = Path(__file__).resolve().parent.parent.parent
    subprocess.check_call(
        ["black", path.resolve().relative_to(base_path)], cwd=base_path
    )


def main() -> None:
    specs = load_specs(SCHEMA_URL)
    dset_spec = specs["Dataset"]

    with open(MODEL_OUT_PATH, "w") as f:
        f.write(generate_models(specs))
    format_with_black(MODEL_OUT_PATH)

    with open(DSET_FIELDS_OUT_PATH, "w") as f:
        f.write(generate_dataset_fields(dset_spec))
    format_with_black(DSET_FIELDS_OUT_PATH)


if __name__ == "__main__":
    main()
