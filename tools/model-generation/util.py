# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen
"""Utilities for different generators."""
from spec import Field


def get_model_name(field: Field, typ: str) -> str:
    name = field.model_name
    if isinstance(name, dict):
        return name[typ]
    return name


def quote(s: str) -> str:
    if '"' in s:
        return f"'{s}'"
    return f'"{s}"'
