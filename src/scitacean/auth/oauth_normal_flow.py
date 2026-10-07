# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)

"""An OAuth client for 'normal' authentication flows."""

import secrets
import warnings
from collections.abc import Callable, Iterable
from contextlib import closing
from datetime import timedelta

import httpx

from ..error import AuthError
from ..typing import SupportsClose
from ..util.credentials import ExpiringToken, SecretStr
from . import _pkce
from ._oauth import IdPConfig, get_idp_config
from ._oauth_redirect_server import launch_auth_redirect_server
from ._user_agent import open_in_browser


class OAuthClientNormal:
    """An OAuth client for 'normal' authentication flows.

    This client implements the 'normal' flow of OAuth. It runs an interactive login
    flow via the user's web browser and a callback server on localhost.

    This requires that Python is running on the same machine as the user interface
    so that opening ``127.0.0.1`` in a browser connects with the machine
    running the Python code. This is notably *not* the case when using a remote
    Jupyter instance. Use a different login method in such a case.

    See Also
    --------
    :ref:`connecting-sso`
    """

    def __init__(
        self,
        *,
        provider: str,
        client_id: str,
        local_port: int | Iterable[int] = 0,
        callback_path: str = "/callback",
        local_timeout: timedelta = timedelta(seconds=60),
        remote_timeout: timedelta = timedelta(seconds=5),
        scopes: Iterable[str] = ("openid",),
        allow_http: bool = False,
    ) -> None:
        """Create a new client.

        This client uses a callback server that will be launched on

        .. code-block::

            127.0.0.1:{port}{callback_path}

        This path needs to be whitelisted in the OAuth provider's
        configuration for the client ID.

        Parameters
        ----------
        provider:
            The URL of the OAuth provider.
        client_id:
            The client ID of the OAuth client.
        local_port:
            The port(s) to use for the callback server on localhost.
            If multiple, tries all ports in order until one is available.
            Defaults to 0, which means that the server will pick any free port.
        callback_path:
            The path to use for the callback server on localhost.
        local_timeout:
            Timeout for the callback server.
        remote_timeout:
            Timeout for calls to the identity provider.
        scopes:
            The scopes to request from the identity provider.
            Only change this if login fails with the default.
        allow_http:
            Whether to allow the use of HTTP instead of HTTPS.
            Only use this for testing!
            Otherwise, secrets are transmitted unencrypted.
        """
        self._provider = provider
        self._client_id = client_id
        self._local_port = local_port
        self._callback_path = "/" + callback_path.removeprefix("/")
        self._local_timeout = local_timeout
        self._remote_timeout = remote_timeout
        self._scopes = set(scopes)
        self._allow_http = allow_http

    def login(
        self,
        *,
        open_browser: Callable[[str], SupportsClose] | None = None,
    ) -> ExpiringToken:
        """Log in with the IdP.

        This runs an interactive login flow via the user's web browser.

        Parameters
        ----------
        open_browser:
            A function that opens a given URL in the user's web browser.
            By default, the client either uses the system's default browser
            or, in Jupyter, opens a browser through JavaScript.
            The return value is intended to close the browser window or at least
            release any auxiliary resources.

        Returns
        -------
        :
            An IdP access token.
            (This is *not* a SciCat token.)
        """
        self._check_idp_compatibility()

        state = secrets.token_urlsafe()
        code_verifier, (code_challenge, code_challenge_method) = (
            _pkce.generate_pkce_pair(self._idp_config.code_challenge_methods_supported)
        )

        with httpx.Client(timeout=self._remote_timeout.total_seconds()) as client:
            auth_code, redirect_url = self._listen_for_authorization_code(
                client,
                code_challenge,
                code_challenge_method,
                state,
                open_browser=open_browser or open_in_browser,
            )
            token = self._exchange_auth_code_for_token(
                client,
                auth_code=auth_code,
                code_verifier=code_verifier,
                redirect_url=redirect_url,
            )
        return ExpiringToken.from_jwt(SecretStr(token))

    @property
    def remote_timeout(self) -> timedelta:
        """The timeout for calls to the identity provider."""
        return self._remote_timeout

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
        return get_idp_config(
            self._provider, allow_http=self._allow_http, timeout=self._remote_timeout
        )

    def _listen_for_authorization_code(
        self,
        client: httpx.Client,
        code_challenge: str,
        code_challenge_method: str,
        state: str,
        open_browser: Callable[[str], SupportsClose],
    ) -> tuple[str, str]:
        with launch_auth_redirect_server(
            port=self._local_port,
            timeout=self._local_timeout,
            state=state,
            path=self._callback_path,
        ) as server:
            # Derive the URL from the server port in case the server picks a port.
            redirect_url = self._redirect_url(server.server_port)
            auth_url = self._build_auth_url(
                client,
                code_challenge=code_challenge,
                code_challenge_method=code_challenge_method,
                state=state,
                redirect_url=redirect_url,
            )
            with closing(open_browser(auth_url)):
                server.wait_for_authorization_code()

        if (auth_code := server.authorization_code) is not None:
            return auth_code, redirect_url

        raise AuthError(
            server.failure
            + " Please check that you logged in correctly and check the login "
            "configuration.\nTip: Configure Python's logging framework to output "
            "INFO messages to the terminal and try again."
        )

    def _exchange_auth_code_for_token(
        self,
        client: httpx.Client,
        *,
        auth_code: str,
        code_verifier: str,
        redirect_url: str,
    ) -> str:
        data = {
            "code": auth_code,
            "client_id": self._client_id,
            "grant_type": _GRANT_TYPE,
            "scope": self._scope_param(),
            "redirect_uri": redirect_url,
            "code_verifier": code_verifier,
        }

        try:
            response = client.post(self._idp_config.endpoints.token_endpoint, data=data)
            response.raise_for_status()
            result = response.json()

            try:
                access_token = result["access_token"]
            except KeyError:
                raise AuthError(
                    "Failed to get an access token from the identity provider: "
                    f"The provider returned an unknown message format: \n{result}"
                ) from None

            if (token_type := result.get("token_type")) != "Bearer":
                raise AuthError(
                    "Failed to get an access token from the identity provider: "
                    f"The provider returned an unknown token type: {token_type}"
                ) from None
        except Exception as error:
            error.add_note(
                "When exchanging an OAuth authorization code for an access token"
            )
            raise

        return access_token  # type: ignore[no-any-return]

    def _build_auth_url(
        self,
        client: httpx.Client,
        *,
        code_challenge: str,
        code_challenge_method: str,
        state: str,
        redirect_url: str,
    ) -> str:
        """Build a URL to open in a browser for the user to log in."""
        if (auth_endpoint := self._idp_config.endpoints.authorization_endpoint) is None:
            raise AuthError(
                "The identity provider does not support the normal flow of OAuth."
            )

        url = client.build_request(
            "GET",
            auth_endpoint,
            params={
                "response_type": _RESPONSE_TYPE,
                "client_id": self._client_id,
                "redirect_uri": redirect_url,
                "scope": self._scope_param(),
                "state": state,
                "code_challenge": code_challenge,
                "code_challenge_method": code_challenge_method,
            },
        ).url
        return str(url)

    def _redirect_url(self, local_port: int) -> str:
        return f"http://127.0.0.1:{local_port}{self._callback_path}"

    def _scope_param(self) -> str:
        # join by " " which translated to "+" when escaped:
        return " ".join(self._scopes)

    def _check_idp_compatibility(self) -> None:
        cfg = self._idp_config

        messages = []
        if _GRANT_TYPE not in cfg.grant_types_supported:
            messages.append(
                f"It does not support the required grant type '{_GRANT_TYPE}'. "
                f"It only supports {cfg.grant_types_supported}."
            )
        if _RESPONSE_TYPE not in cfg.response_types_supported:
            messages.append(
                f"It does not support the required response type '{_RESPONSE_TYPE}'. "
                f"It only supports {cfg.response_types_supported}."
            )
        if not self._scopes.issubset(cfg.scopes_supported):
            messages.append(
                f"It does not support the required scopes: {self._scope_param()} "
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
_GRANT_TYPE = "authorization_code"
_RESPONSE_TYPE = "code"
