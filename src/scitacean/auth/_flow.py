# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)

"""The complete authentication flow."""

import os
import warnings
from collections.abc import Callable, Sequence
from datetime import timedelta
from typing import Literal

import httpx

from .._internal.url import normalize_api_url
from ..error import AuthError
from ..typing import SupportsClose
from ..util.credentials import ExpiringToken, SecretStr
from ._oauth import OAuthClient
from .oauth_device_flow import OAuthClientDevice
from .oauth_normal_flow import OAuthClientNormal

OAuthFlow = Literal["auto", "normal", "device"]

OAUTH_FLOW_ENV_VAR = "SCITACEAN_OAUTH_FLOW"


def login_via_oauth(
    flow: OAuthFlow,
    configured_oauth_clients: Sequence[OAuthClient],
    scicat_url: str,
    open_browser: Callable[[str], SupportsClose] | None = None,
) -> ExpiringToken:
    """Get a SciCat token via single-sign-on.

    Parameters
    ----------
    flow:
        Type of login method to use for authentication.
        The default is to pick the best client for the current system.
    configured_oauth_clients:
        Available OAuth clients to use for authentication.
    scicat_url:
        URL of the SciCat api.
    open_browser:
        A function that opens a given URL in the user's web browser.
        By default, the client either uses the system's default browser
        or, in Jupyter, opens a browser through JavaScript.
        The return value is intended to close the browser window or at least
        release any auxiliary resources.

    Returns
    -------
    :
        A valid SciCat token.
    """
    oauth_client = _select_oauth_client(flow, configured_oauth_clients)
    idp_token = oauth_client.login(open_browser=open_browser)
    return exchange_idp_token_for_scicat_token(
        scicat_url=scicat_url, idp_token=idp_token, timeout=oauth_client.remote_timeout
    )


def _select_oauth_client(
    flow: OAuthFlow, configured: Sequence[OAuthClient]
) -> OAuthClient:
    match flow:
        case "normal":
            return _find_client(configured, OAuthClientNormal)
        case "device":
            return _find_client(configured, OAuthClientDevice)
        case "auto":
            match _flow_override():
                case "auto":
                    try:
                        return _find_client(configured, OAuthClientNormal)
                    except ValueError:
                        return _find_client(configured, OAuthClientDevice)
                case override:
                    return _select_oauth_client(override, configured)
        case bad:
            raise ValueError(f"Unknown OAuth flow: {bad}")


def _find_client(clients: Sequence[OAuthClient], selected: type) -> OAuthClient:
    try:
        return next(client for client in clients if isinstance(client, selected))
    except StopIteration:
        raise ValueError(f"No {selected.__name__} client configured") from None


def _flow_override() -> OAuthFlow:
    if (env_var := os.environ.get(OAUTH_FLOW_ENV_VAR)) is None:
        return "auto"

    flow = env_var.lower()
    options = OAuthFlow.__args__  # type: ignore[attr-defined]
    if flow not in options:
        warnings.warn(
            "Unknown OAuth flow specified in environment variable "
            f"{OAUTH_FLOW_ENV_VAR}={env_var}\n"
            f"Supported values: {options}",
            UserWarning,
            stacklevel=3,
        )
        return "auto"
    return flow  # type: ignore[return-value]


def exchange_idp_token_for_scicat_token(
    *, scicat_url: str, idp_token: ExpiringToken, timeout: timedelta
) -> ExpiringToken:
    """Get a SciCat token for a valid identity provider token.

    Parameters
    ----------
    scicat_url:
        URL of the SciCat api.
    idp_token:
        An access token for the identity provider.
    timeout:
        Timeout for the HTTP request.

    Returns
    -------
    :
        A valid SciCat token.
    """
    response = httpx.post(
        normalize_api_url(scicat_url) + "/v3/auth/oidc/token",
        # `idp_token` is an access_token which SciCat requires despite the name:
        json={"idToken": idp_token.get_str()},
        timeout=timeout.total_seconds(),
    )
    if not response.is_success:
        raise AuthError(
            f"Failed to exchange the identity provider token for a SciCat token: "
            f"{response.text}"
        )
    if (scicat_token := response.json().get("access_token")) is None:
        raise AuthError(
            "SciCat did not return a token with the expected 'access_token' key, "
            f"got {response.json().keys()}"
        )
    return ExpiringToken.from_jwt(SecretStr(scicat_token))
