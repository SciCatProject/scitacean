# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)
"""An HTTP server to handle OAuth redirects."""

from __future__ import annotations

import logging
from collections.abc import Generator
from contextlib import contextmanager
from datetime import timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib import parse

from . import _assets

_LOGGER_NAME = "OAuth-server"


@contextmanager
def launch_auth_redirect_server(
    *, port: int, timeout: timedelta, state: str
) -> Generator[OAuthRedirectServer, None, None]:
    """Launch a server to listen for OAuth redirects and store an authorization code.

    Each server instance should only be used once.

    The server returns 200 with an HTML page containing instruction on success or
    failure. The page closes automatically under some circumstances but not always,
    see https://developer.mozilla.org/en-US/docs/Web/API/Window/close.
    All other responses are 501.

    The server writes logs to a logger called "OAuth-server".

    Parameters
    ----------
    port:
        The port to listen on.
    timeout:
        Timeout for waiting for the authorization code.
        A ``TimeoutError`` is raised if the timeout is reached.
    state:
        The random OAuth state string for this interaction.

    Returns
    -------
    :
        A context manager for an OAuthHttpServer.
        The authorization code can be read after the context manager exits via
        ``server.authorization_code``. This attribute is ``None`` if no code
        was received.
    """
    with OAuthRedirectServer(
        ("127.0.0.1", port),
        _OAuthRedirectHandler,
        timeout=int(timeout.total_seconds()),
        state=state,
    ) as server:
        yield server


class OAuthRedirectServer(HTTPServer):
    """A Server to receive an OAuth authorization code.

    Should always be created and managed via ``launch_auth_server``.
    """

    def __init__(
        self,
        server_address: tuple[str, int],
        RequestHandlerClass: type,
        *,
        timeout: int,
        state: str,
    ) -> None:
        super().__init__(server_address, RequestHandlerClass)
        self.timeout = timeout
        self.state = state
        self.authorization_code: str | None = None
        self.failure: str = ""

    def handle_timeout(self) -> None:
        super().handle_timeout()
        raise TimeoutError(
            "The OAuth server did not receive an authorization code after "
            f"{self.timeout} seconds. This means either that nobody logged "
            "in successfully in time or that the identity provider did "
            "not redirect or did not redirect correctly."
        )


class _OAuthRedirectHandler(BaseHTTPRequestHandler):
    """Handler for the OAuth HTTP server."""

    def do_GET(self) -> None:
        """Handle GET requests.

        Only allows OAuth redirects.
        """
        server: OAuthRedirectServer = self.server  # type: ignore[assignment]

        parsed = parse.urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            return

        qs = parse.parse_qs(parsed.query)
        if errors := qs.get("error", []):
            self._send_result_page(success=False)
            server.failure = f"Authentication failed: {errors}."
        elif qs.get("state", None) != [server.state]:
            self._send_result_page(success=False)
            server.failure = "The identity provider used an invalid OAuth state."
        elif (code := qs.get("code", [None])[0]) is None:
            self._send_result_page(success=False)
            server.failure = "The identity provider did not send an authorization code."
        else:
            server.authorization_code = code
            self._send_result_page(success=True)

    def _send_result_page(self, *, success: bool) -> None:
        if success:
            text = _success_page()
        else:
            text = _failure_page()
        data = text.encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_request(
        self, code: int | str = "-", *args: object, **kwargs: object
    ) -> None:
        # `self.path` contains the auth token, so only show basics about the request
        logging.getLogger(_LOGGER_NAME).info(
            "%s (%s) from %s", self.command, code, self.client_address
        )

    def log_error(self, *args: object, **kwargs: object) -> None:
        # Override to avoid leaking the auth token
        logging.getLogger(_LOGGER_NAME).error("Received error")

    def log_message(self, *args: object, **kwargs: object) -> None:
        # Override to avoid leaking the auth token
        logging.getLogger(_LOGGER_NAME).info("Received message")


def _success_page() -> str:
    content = _assets.auth_redirect_success()
    base = _assets.auth_redirect_page_template()
    return base.substitute(content=content, title="Authenticated")


def _failure_page() -> str:
    content = _assets.auth_redirect_failure()
    base = _assets.auth_redirect_page_template()
    return base.substitute(content=content, title="Login failed")
