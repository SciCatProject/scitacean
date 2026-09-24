# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)

"""An OAuth client for 'device' authentication flows."""

import time
import warnings
from collections.abc import Iterable
from datetime import timedelta
from typing import Any

import httpx

from ..error import AuthError
from ..util.credentials import ExpiringToken, SecretStr
from . import _pkce
from ._oauth import IdPConfig, get_idp_config
from ._user_agent import open_in_browser


class OAuthClientDevice:
    """An OAuth client for 'device' authentication flows.

    This client implements the 'device' flow of OAuth. It runs an interactive login
    flow via the user's web browser and a device code. The browser can be opened
    on any machine as long as the user enters the correct device code. This client
    is therefore usable on systems without a GUI and on remote Jupyter instances.
    """

    def __init__(
        self,
        *,
        provider: str,
        client_id: str,
        local_timeout: timedelta = timedelta(seconds=30),
        remote_timeout: timedelta = timedelta(seconds=5),
        scopes: Iterable[str] = ("openid",),
    ) -> None:
        """Create a new client.

        Parameters
        ----------
        provider:
            The URL of the OAuth provider.
        client_id:
            The client ID of the OAuth client.
        local_timeout:
            Timeout for receiving a confirmation from the identity provider.
        remote_timeout:
            Timeout for calls to the identity provider.
        scopes:
            The scopes to request from the identity provider.
            Only change this if login fails with the default.
        """
        self._provider = provider
        self._client_id = client_id
        self._local_timeout = local_timeout
        self._remote_timeout = remote_timeout
        self._scopes = set(scopes)

    def login(self) -> ExpiringToken:
        """Log in with the IdP.

        This runs an interactive login flow via a web browser.

        Returns
        -------
        :
            An IdP access token.
            (This is *not* a SciCat token.)
        """
        self._check_idp_compatibility()

        code_verifier, (code_challenge, code_challenge_method) = (
            _pkce.generate_pkce_pair(self._idp_config.code_challenge_methods_supported)
        )

        with httpx.Client(timeout=self._remote_timeout.total_seconds()) as client:
            flow_data = self._start_auth_flow(
                client,
                code_challenge=code_challenge,
                code_challenge_method=code_challenge_method,
            )
            verification_url = (
                f"{flow_data['verification_uri']}?user_code={flow_data['user_code']}"
            )
            open_in_browser(verification_url)

            token = self._wait_for_token(
                client,
                code_verifier=code_verifier,
                device_code=flow_data["device_code"],
                interval=flow_data["interval"],
            )
        return ExpiringToken.from_jwt(SecretStr(token))

    @property
    def _idp_config(self) -> IdPConfig:
        """Get the IdP configuration on demand.

        ``get_idp_config`` is cached, so this only makes a single request during the
        lifetime of the process.

        The request is made here instead of directly in ``__init__`` so that failures
        only happen when the client is used. This way, a SciCat profile can be
        constructed and used even when there are problems with the IdP as long as
        the user uses a different login method.
        """
        return get_idp_config(self._provider)

    def _start_auth_flow(
        self,
        client: httpx.Client,
        code_challenge: str,
        code_challenge_method: str,
    ) -> dict[str, Any]:
        if (
            auth_endpoint := self._idp_config.endpoints.device_authorization_endpoint
        ) is None:
            raise AuthError(
                "The identity provider does not support the device flow of OAuth."
            )

        response = client.post(
            auth_endpoint,
            data={
                "client_id": self._client_id,
                "code_challenge": code_challenge,
                "code_challenge_method": code_challenge_method,
                # join by " " which translated to "+" when escaped:
                "scope": " ".join(self._scopes),
            },
        )
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]

    def _wait_for_token(
        self,
        client: httpx.Client,
        *,
        code_verifier: str,
        device_code: str,
        interval: int,
    ) -> str:
        start_time = time.time()
        while time.time() - start_time < self._local_timeout.total_seconds():
            response = client.post(
                self._idp_config.endpoints.token_endpoint,
                data={
                    "client_id": self._client_id,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "device_code": device_code,
                    "code_verifier": code_verifier,
                },
            )
            if response.is_success:
                return response.json()["access_token"]  # type: ignore[no-any-return]
            # The IdP will either keep returning 400 or an 'authorization_pending'
            # error until the user has verified the device code.
            if (
                response.status_code != 400
                or response.json().get("error") != "authorization_pending"
            ):
                raise AuthError(f"Bad reply: {response} {response.text}")

            time.sleep(interval)

        raise TimeoutError(
            "The OAuth client was unable to get an access token after "
            f"{self._local_timeout.total_seconds()} seconds. This likely means that "
            "nobody confirmed the device login in time. Please make sure to open the "
            "login page in your browser if it does not do so automatically."
        )

    def _check_idp_compatibility(self) -> None:
        cfg = self._idp_config

        messages = []
        if _GRANT_TYPE not in cfg.grant_types_supported:
            messages.append(
                f"It does not support the required grant type '{_GRANT_TYPE}'. "
                f"It only supports {cfg.grant_types_supported}."
            )
        if not self._scopes.issubset(cfg.scopes_supported):
            messages.append(
                f"It does not support the required scopes: {self._scopes} "
                f"It only supports {cfg.scopes_supported}",
            )

        if messages:
            warnings.warn(
                "There are problems with the identity provider:\n  - "
                + "\n  - ".join(messages)
                + "\nProceeding regardless, but authentication may fail.",
                UserWarning,
                stacklevel=3,
            )


# OAuth parameters
_GRANT_TYPE = "urn:ietf:params:oauth:grant-type:device_code"
