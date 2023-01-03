# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Generate pydantic models and DatasetFields."""

import argparse
from pathlib import Path

from dataset import generate_dataset_fields
from model import generate_models
from spec import load_specs

# TODO model validation shows model names (aliases?)


def parse_args():
    parser = argparse.ArgumentParser("Generate models and dataclasses")
    parser.add_argument("--src-dir", type=Path, help="Scitacean source directory")
    return parser.parse_args()


def main():
    args = parse_args()
    specs = load_specs()
    generate_models(args.src_dir / "model.py", specs)
    generate_dataset_fields(args.src_dir / "_dataset_fields.py", specs)


if __name__ == "__main__":
    main()
