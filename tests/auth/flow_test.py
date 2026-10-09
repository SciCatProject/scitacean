# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)

from collections.abc import Sequence

import pytest

from scitacean.auth import OAuthClient, OAuthClientDevice, OAuthClientNormal

# There are tests for an internal function because it is difficult
# to test thoroughly through the public interface.
from scitacean.auth._flow import OAuthFlow, _select_oauth_client


def _configured_clients() -> Sequence[OAuthClient]:
    return (
        OAuthClientDevice(provider="http://localhost:1234", client_id="test"),
        OAuthClientNormal(provider="http://localhost:1234", client_id="test"),
    )


@pytest.mark.parametrize(
    ("flow", "expected"),
    [("normal", OAuthClientNormal), ("device", OAuthClientDevice)],
)
@pytest.mark.parametrize("env", [None, "", "normal", "device", "auto", "bad"])
def test_select_oauth_client_explicit_flow(
    flow: OAuthFlow,
    expected: type,
    env: str | None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if env is not None:
        monkeypatch.setenv("SCITACEAN_OAUTH_FLOW", env)

    client = _select_oauth_client(flow, _configured_clients())
    assert isinstance(client, expected)


@pytest.mark.parametrize(
    ("env", "expected"),
    [
        (None, OAuthClientNormal),
        ("normal", OAuthClientNormal),
        ("device", OAuthClientDevice),
        ("auto", OAuthClientNormal),
    ],
)
def test_select_oauth_client_auto(
    env: str | None,
    expected: type,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if env is not None:
        monkeypatch.setenv("SCITACEAN_OAUTH_FLOW", env)

    client = _select_oauth_client("auto", _configured_clients())
    assert isinstance(client, expected)


@pytest.mark.parametrize(
    ("env", "expected"),
    [
        ("", OAuthClientNormal),
        ("unknown", OAuthClientNormal),
    ],
)
def test_select_oauth_client_auto_bad_env_var(
    env: str | None,
    expected: type,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if env is not None:
        monkeypatch.setenv("SCITACEAN_OAUTH_FLOW", env)

    with pytest.warns(UserWarning, match="Unknown OAuth flow"):
        client = _select_oauth_client("auto", _configured_clients())
    assert isinstance(client, expected)


@pytest.mark.parametrize("env", [None, "normal", "bad"])
def test_select_oauth_client_bad_flow(
    env: str | None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if env is not None:
        monkeypatch.setenv("SCITACEAN_OAUTH_FLOW", env)

    with pytest.raises(ValueError, match="Unknown OAuth flow"):
        _select_oauth_client("bad", _configured_clients())  # type: ignore[arg-type]


def test_select_oauth_client_not_configured() -> None:
    with pytest.raises(ValueError, match="client configured"):
        _select_oauth_client(
            "normal",
            [OAuthClientDevice(provider="http://localhost:1234", client_id="test")],
        )
