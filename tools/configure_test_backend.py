# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Configure the test services by writing a Docker Compose file and its assets."""

import argparse
from pathlib import Path
from typing import cast

from scitacean.testing._services.config import configure_services


def main() -> None:
    args = parse_args()

    output_dir = cast(Path, args.output_dir).absolute()
    if output_dir.exists():
        if not output_dir.is_dir():
            raise ValueError(f"{args.output_dir} exists but is not a directory")
        if any(output_dir.iterdir()):
            raise ValueError(f"{args.output_dir} exists but is not empty")
    output_dir.mkdir(parents=True, exist_ok=True)
    configure_services(
        output_dir, docker_filename="docker-compose.yaml", scicat_version=None
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Configure Scitacean test services.")
    parser.add_argument(
        "output_dir",
        type=Path,
        help="Directory to write the generated files to",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
