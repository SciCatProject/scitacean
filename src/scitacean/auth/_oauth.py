# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)
"""General OAuth tools."""

from __future__ import annotations

import dataclasses
from datetime import timedelta
from functools import cache
from typing import Any, Protocol
from urllib.parse import urlsplit

import httpx

from .._internal.url import require_scheme, url_concat
from ..util.credentials import ExpiringToken


@cache
def get_idp_config(
    provider_url: str, *, allow_http: bool, timeout: timedelta
) -> IdPConfig:
    """Read the IdP configuration from the given issuer.

    Assumes that the provider supports OpenID Connect and that there is a
    ``.well-known/openid-configuration`` endpoint.
    """
    allowed_schemes = ("https", "http") if allow_http else ("https",)
    require_scheme(
        provider_url,
        allowed=allowed_schemes,
        what="provider",
    )
    host = urlsplit(provider_url).netloc

    response = httpx.get(
        url_concat(provider_url, ".well-known/openid-configuration"),
        follow_redirects=True,
        timeout=timeout.total_seconds(),
    )
    if not response.is_success:
        raise RuntimeError(
            f"Failed to get IdP config from {provider_url}: {response.text}"
        )

    data = response.json()
    if (
        token_endpoint := _get_config_url(data, "token_endpoint", host, allowed_schemes)
    ) is None:
        raise RuntimeError("The IdP does not define a token endpoint")
    return IdPConfig(
        endpoints=Endpoints(
            authorization_endpoint=_get_config_url(
                data, "authorization_endpoint", host, allowed_schemes
            ),
            device_authorization_endpoint=_get_config_url(
                data, "device_authorization_endpoint", host, allowed_schemes
            ),
            token_endpoint=token_endpoint,
        ),
        response_types_supported=tuple(data["response_types_supported"]),
        **{
            key: tuple(data.get(key, default))
            for key, default in (
                ("code_challenge_methods_supported", ["S256"]),  # Should work anywhere
                (
                    "grant_types_supported",
                    ["authorization_code", "implicit"],  # OIDC default
                ),
                ("scopes_supported", ["openid"]),
            )
        },
    )


@dataclasses.dataclass(frozen=True, slots=True)
class IdPConfig:
    """Identity provider configuration."""

    endpoints: Endpoints
    code_challenge_methods_supported: tuple[str, ...]
    grant_types_supported: tuple[str, ...]
    response_types_supported: tuple[str, ...]
    scopes_supported: tuple[str, ...]


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

    @property
    def remote_timeout(self) -> timedelta:
        """The timeout for calls to the identity provider."""


def _get_config_url(
    data: dict[str, Any], key: str, host: str, allowed_schemes: tuple[str, ...]
) -> str | None:
    if (url := data.get(key)) is None:
        return None
    require_scheme(url, allowed=allowed_schemes, what=key)
    if urlsplit(url).netloc != host:
        raise RuntimeError(
            f"The host of the '{key}' in the IdP config differs from the "
            f"IdP itself ({host}): {url}\nThis is not allowed because this indicates "
            f"a malicious or at least dangerous config."
        )
    return url  # type: ignore[no-any-return]
