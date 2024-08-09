# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)

"""Generate Python classes for SciCat models."""

import argparse
import subprocess
import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

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


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="generate_models.py", description="Generate models for Scitacean"
    )
    parser.add_argument(
        "--launch-scicat",
        action="store_true",
        help="Launch a temporary SciCat backend with docker",
    )
    return parser.parse_args()


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


def generate_models(specs: dict[str, Spec]) -> str:
    specs = dict(specs)
    dset_spec = specs.pop("Dataset")
    return _model_template().render(banner=BANNER, specs=specs, dset_spec=dset_spec)


def generate_dataset_fields(dset_spec: DatasetSpec) -> str:
    return _dataset_fields_template().render(banner=BANNER, spec=dset_spec)


def format_with_ruff(path: Path) -> None:
    # Root of Scitacean repo
    base_path = Path(__file__).resolve().parent.parent.parent
    subprocess.check_call(  # noqa: S603
        ["ruff", "format", path.resolve().relative_to(base_path)],  # noqa: S607
        cwd=base_path,
    )


@contextmanager
def _scicat_backend() -> Generator[None, None, None]:
    from scitacean.testing import backend

    with tempfile.TemporaryDirectory() as work_dir:
        docker_file = Path(work_dir) / "docker-compose.yaml"
        backend.configure(docker_file)
        backend.start_backend(docker_file)
        try:
            backend.wait_until_backend_is_live(max_time=20, n_tries=20)
            yield
        finally:
            backend.stop_backend(docker_file)


def load(real_backend: bool) -> dict[str, Any]:
    if not real_backend:
        return load_specs(SCHEMA_URL)

    with _scicat_backend():
        from scitacean.testing.backend import config

        return load_specs(f"http://localhost:{config.SCICAT_PORT}/explorer-json")


def main() -> None:
    args = _parse_args()
    specs = load(args.launch_scicat)
    dset_spec = specs["Dataset"]

    with open(MODEL_OUT_PATH, "w") as f:
        f.write(generate_models(specs))
    format_with_ruff(MODEL_OUT_PATH)

    with open(DSET_FIELDS_OUT_PATH, "w") as f:
        f.write(generate_dataset_fields(dset_spec))
    format_with_ruff(DSET_FIELDS_OUT_PATH)


if __name__ == "__main__":
    main()
