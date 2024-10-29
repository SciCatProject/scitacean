# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)

import base64
import json
import pickle
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from scitacean import PID, Client
from scitacean.testing.backend import config as backend_config
from scitacean.testing.backend.seed import INITIAL_DATASETS
from scitacean.testing.client import FakeClient
from scitacean.util.credentials import SecretStr


def test_from_token_fake() -> None:
    # This should not call the API
    client = FakeClient.from_token(url="some.url/api/v3", token="a-token")  # noqa: S106
    assert isinstance(client, FakeClient)


def test_from_credentials_fake() -> None:
    # This should not call the API
    client = FakeClient.from_credentials(
        url="some.url/api/v3",
        username="someone",
        password="the-fake-does-not-care",  # noqa: S106
    )
    assert isinstance(
        client,
        FakeClient,
    )


def test_from_credentials_real(
    scicat_access: backend_config.SciCatAccess, require_scicat_backend: None
) -> None:
    Client.from_credentials(url=scicat_access.url, **scicat_access.user.credentials)


def test_cannot_pickle_client_credentials_manual_token_str() -> None:
    client = Client.from_token(url="/", token="the-token")  # noqa: S106
    with pytest.raises(TypeError):
        pickle.dumps(client)


def test_cannot_pickle_client_credentials_manual_token_secret_str() -> None:
    client = Client.from_token(url="/", token=SecretStr("the-token"))
    with pytest.raises(TypeError):
        pickle.dumps(client)


def test_cannot_pickle_client_credentials_login(
    scicat_access: backend_config.SciCatAccess, require_scicat_backend: None
) -> None:
    client = Client.from_credentials(
        url=scicat_access.url, **scicat_access.user.credentials
    )
    with pytest.raises(TypeError):
        pickle.dumps(client)


def test_connection_error_does_not_contain_token() -> None:
    client = Client.from_token(
        url="https://not-actually-a_server",
        token="the token/which_must-be.kept secret",  # noqa: S106
    )
    try:
        client.get_dataset("does not exist")
        pytest.fail("There must be an exception")
    except Exception as exc:
        assert "the token/which_must-be.kept secret" not in str(exc)  # noqa: PT017
        for arg in exc.args:
            assert "the token/which_must-be.kept secret" not in str(arg)


def test_fake_can_disable_functions() -> None:
    client = FakeClient(
        disable={
            "get_dataset_model": RuntimeError("custom failure"),
            "get_orig_datablocks": IndexError("custom index error"),
        }
    )
    with pytest.raises(RuntimeError, match="custom failure"):
        client.scicat.get_dataset_model(PID(pid="some-pid"))
    with pytest.raises(IndexError, match="custom index error"):
        client.scicat.get_orig_datablocks(PID(pid="some-pid"))


def encode_jwt_part(part: dict[str, Any]) -> str:
    return base64.urlsafe_b64encode(json.dumps(part).encode("utf-8")).decode("ascii")


def make_token(exp_in: timedelta) -> str:
    now = datetime.now(tz=timezone.utc)
    exp = now + exp_in

    # This is what a SciCat token looks like as of 2024-04-19
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "_id": "7fc0856e50a8",
        "username": "Weatherwax",
        "email": "g.weatherwax@wyrd.lancre",
        "authStrategy": "ldap",
        "id": "7fc0856e50a8",
        "userId": "7fc0856e50a8",
        "iat": now.timestamp(),
        "exp": exp.timestamp(),
    }
    # Scitacean never validates the signature because it doesn't have the secret key,
    # so it doesn't matter what we use here.
    signature = "123abc"

    return ".".join((encode_jwt_part(header), encode_jwt_part(payload), signature))


def test_detects_expired_token_init() -> None:
    token = make_token(timedelta(milliseconds=0))
    with pytest.raises(RuntimeError, match="SciCat login has expired"):
        Client.from_token(url="scicat.com", token=token)


def test_detects_expired_token_get_dataset(
    scicat_access: backend_config.SciCatAccess, require_scicat_backend: None
) -> None:
    # The token is invalid, but the expiration should be detected before
    # even sending it to SciCat.
    token = make_token(timedelta(milliseconds=2100))  # > than denial period = 2s
    client = Client.from_token(url=scicat_access.url, token=token)
    time.sleep(0.5)
    with pytest.raises(RuntimeError, match="SciCat login has expired"):
        client.get_dataset(INITIAL_DATASETS["public"].pid)  # type: ignore[arg-type]
