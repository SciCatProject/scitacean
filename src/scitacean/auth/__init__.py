# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Authentication client."""

from .oauth_device_flow import OAuthClientDevice
from .oauth_normal_flow import OAuthClientNormal

__all__ = ("OAuthClientDevice", "OAuthClientNormal")
