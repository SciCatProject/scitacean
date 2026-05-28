# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Profiles for connecting to SciCat."""

from ._common import (
    Profile,
    ScientificMetadataSchema,
    gather_login_params,
    locate_profile,
)

__all__ = [
    "Profile",
    "ScientificMetadataSchema",
    "gather_login_params",
    "locate_profile",
]
