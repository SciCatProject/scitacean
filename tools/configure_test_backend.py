# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Configure a test backend by building a docker compose file and auxiliary files."""

import argparse
from pathlib import Path
from typing import cast

from scitacean.testing import backend


def main() -> None:
    args = parse_args()

    output_dir = cast(Path, args.output_dir).absolute()
    if output_dir.exists():
        if not output_dir.is_dir():
            raise ValueError(f"{args.output_dir} exists but is not a directory")
        if any(output_dir.iterdir()):
            raise ValueError(f"{args.output_dir} exists but is not empty")
    output_dir.mkdir(parents=True, exist_ok=True)
    backend.configure(target_path=output_dir / "docker-compose.yaml")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Configure a Scitacean test backend.")
    parser.add_argument(
        "output_dir",
        type=Path,
        help="Directory to write the generated files to",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
