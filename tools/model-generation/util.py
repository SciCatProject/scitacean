# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Utilities for different generators."""


def quote(s: str) -> str:
    if '"' in s:
        return f"'{s}'"
    return f'"{s}"'
