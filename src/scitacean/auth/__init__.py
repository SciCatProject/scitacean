# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Authentication with SciCat and file servers.

.. rubric:: Classes

.. autosummary::
  :toctree: ../classes
  :template: scitacean-class-template.rst

  OAuthClient
  OAuthClientDevice
  OAuthClientNormal
  OAuthFlow

.. rubric:: Functions

.. autosummary::
  :toctree: ../functions

  login_via_oauth
"""

from ._flow import OAuthMethod, login_via_oauth
from ._oauth import OAuthClient
from .oauth_device_flow import OAuthClientDevice
from .oauth_normal_flow import OAuthClientNormal

__all__ = (
    "OAuthClient",
    "OAuthClientDevice",
    "OAuthClientNormal",
    "OAuthMethod",
    "login_via_oauth",
)
