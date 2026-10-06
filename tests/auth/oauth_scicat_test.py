# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Test complete OAuth flows with SciCat.

These tests use a fake browser to simulate the login flow without user interaction.
This 'browser' relies on a specific form used by Keycloak and te associated behavior.
It may need to be changed if Keycloak changes.
"""

import threading
from datetime import timedelta
from html.parser import HTMLParser

import httpx
import pytest

from scitacean import Client, Profile
from scitacean.auth import OAuthClientDevice, OAuthClientNormal
from scitacean.testing.backend import config

ISSUER = "http://localhost:8080/realms/scitacean"
USERNAME = "user1"
PASSWORD = "testpassword"  # noqa: S105 # betterleaks:allow


@pytest.fixture
def profile() -> Profile:
    client_normal = OAuthClientNormal(
        provider=ISSUER,
        client_id="scitacean-test",
        allow_http=True,
        local_port=8081,
        callback_path="login-callback",
        local_timeout=timedelta(seconds=2),
        remote_timeout=timedelta(seconds=2),
    )
    client_device = OAuthClientDevice(
        provider=ISSUER,
        client_id="scitacean-test",
        allow_http=True,
        local_timeout=timedelta(seconds=2),
        remote_timeout=timedelta(seconds=2),
    )
    return Profile(
        url=f"http://localhost:{config.SCICAT_PORT}/api/v3",
        file_transfer=None,
        oauth_clients=(client_normal, client_device),
    )


class _BrowserHandle:
    """Runs the login in a thread and reports errors when closed.

    The interaction runs in a background thread because the last redirect goes
    back to Scitacean's local redirect server. That server only starts handling
    requests *after* this function returns, so doing everything synchronously
    here would deadlock.
    """

    def __init__(self, url: str) -> None:
        self._url = url
        self._error: BaseException | None = None
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        try:
            _log_in(self._url)
        except BaseException as exc:
            self._error = exc

    def close(self) -> None:
        self._thread.join(timeout=30.0)
        if self._error is not None:
            raise self._error


def _log_in(url: str) -> None:
    with httpx.Client(follow_redirects=True, timeout=5.0) as client:
        response = client.get(url)
        if not response.is_success:
            raise RuntimeError(
                f"Keycloak login failed: {response.status_code} "
                f"{response.reason_phrase}:\n{response.text}"
            )

        # Keycloak marks its session cookies (AUTH_SESSION_ID, KC_RESTART, ...)
        # as `Secure`. httpx (http.cookiejar) therefore refuses to send them back
        # over plain http, and Keycloak answers the login POST with
        # 400 "Restart login cookie not found".
        # A real browser does send them because it treats localhost as secure.
        # So collect the cookies manually and set the header explicitly.
        cookies = _collect_cookies(response)

        # The action URL may be relative to the page we just loaded and contains
        # the session/execution parameters that Keycloak needs.
        login_page_url = response.url
        submit_url = str(login_page_url.join(_extract_submit_url(response.text)))

        response = client.post(
            submit_url,
            data={"username": USERNAME, "password": PASSWORD, "credentialId": ""},
            headers={
                "Cookie": "; ".join(f"{k}={v}" for k, v in cookies.items()),
                "Referer": str(login_page_url),
            },
        )
        response.raise_for_status()

        # After a successful login, we end up on the local redirect server.
        if response.url.host not in ("localhost", "127.0.0.1"):
            raise RuntimeError(
                "Login did not redirect to the local redirect server. "
                "The credentials were probably rejected.\n"
                f"Final URL: {response.url}"
            )


def _collect_cookies(response: httpx.Response) -> dict[str, str]:
    """Return all cookies set by a response and its redirects."""
    cookies: dict[str, str] = {}
    for resp in [*response.history, response]:
        for name, value in resp.headers.multi_items():
            if name.lower() != "set-cookie":
                continue
            key, _, val = value.split(";")[0].partition("=")
            cookies[key.strip()] = val.strip()
    return cookies


def _extract_submit_url(html: str) -> str:
    parser = _LoginFormParser()
    parser.feed(html)
    parser.close()

    if parser.submit_url is None:
        raise ValueError("No login form found")
    return parser.submit_url


class _LoginFormParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.submit_url: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "form":
            return
        attr_dict = dict(attrs)
        if (attr_dict.get("method") or "").lower() != "post":
            return
        action = attr_dict.get("action")
        if action is None:
            return
        if self.submit_url is not None:
            raise ValueError("Multiple login forms found")
        self.submit_url = action


# The device flow needs some more complicated interaction with Keycloak around
# handling cookies and how redirect addresses are constructed.
# This is too complicated for the tests. So we rely on the normal flow to test the
# general setup and hope that the device flow continues to work.
def test_oauth_scicat_login_normal(
    profile: Profile, require_scicat_backend: None
) -> None:
    client = Client.login(profile, flow="normal", open_browser=_BrowserHandle)
    info = client.scicat.call_endpoint(
        cmd="GET", url="users/my/identity", operation="get_user_info"
    )
    assert info["profile"]["username"] == USERNAME
