# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen
"""Templates to generate models and other classes."""

from pathlib import Path
from string import Template

TEMPLATE_DIR = Path(__file__).resolve().parent

BANNER = """##########################################
# This file was automatically generated. #
# Do not modify it directly!             #
##########################################
"""


def load_template(name: str) -> Template:
    with open(TEMPLATE_DIR / f"{name}.py.template", "r") as f:
        return Template(f.read())
