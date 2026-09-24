# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)
"""General OAuth tools."""

from __future__ import annotations

import dataclasses
from functools import cache
from typing import Protocol

import httpx

from .._internal.url import url_concat
from ..util.credentials import ExpiringToken


@cache
def get_idp_config(provider_url: str) -> IdPConfig:
    """Read the IdP configuration from the given issuer.

    Assumes that the provider supports OpenID Connect and that there is a
    ``.well-known/openid-configuration`` endpoint.
    """
    response = httpx.get(url_concat(provider_url, ".well-known/openid-configuration"))
    if not response.is_success:
        raise RuntimeError(
            f"Failed to get IDP config from {provider_url}: {response.text}"
        )

    data = response.json()
    return IdPConfig(
        endpoints=Endpoints(
            authorization_endpoint=data.get("authorization_endpoint"),
            device_authorization_endpoint=data.get("device_authorization_endpoint"),
            token_endpoint=data["token_endpoint"],
        ),
        **{
            key: data[key]
            for key in (
                "code_challenge_methods_supported",
                "grant_types_supported",
                "response_types_supported",
                "scopes_supported",
            )
        },
    )


@dataclasses.dataclass(frozen=True, slots=True)
class IdPConfig:
    """Identity provider configuration."""

    endpoints: Endpoints
    code_challenge_methods_supported: list[str]
    grant_types_supported: list[str]
    response_types_supported: list[str]
    scopes_supported: list[str]


@dataclasses.dataclass(frozen=True, slots=True)
class Endpoints:
    """Endpoints for the identity provider."""

    authorization_endpoint: str | None
    device_authorization_endpoint: str | None
    token_endpoint: str


class OAuthClient(Protocol):
    """An OAuth client."""

    def login(self) -> ExpiringToken:
        """Run a login flow to get an access token from the identity provider."""
