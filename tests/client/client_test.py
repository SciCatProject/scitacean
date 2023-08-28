# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)

import pickle

import pytest

from scitacean import PID, Client
from scitacean.testing.client import FakeClient
from scitacean.util.credentials import SecretStr


def test_from_token_fake():
    # This should not call the API
    client = FakeClient.from_token(url="some.url/api/v3", token="a-token")  # noqa: S106
    assert isinstance(client, FakeClient)


def test_from_credentials_fake():
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


def test_from_credentials_real(scicat_access, scicat_backend):
    if not scicat_backend:
        pytest.skip("No backend")
    Client.from_credentials(url=scicat_access.url, **scicat_access.user.credentials)


def test_cannot_pickle_client_credentials_manual_token_str():
    client = Client.from_token(url="/", token="the-token")  # noqa: S106
    with pytest.raises(TypeError):
        pickle.dumps(client)


def test_cannot_pickle_client_credentials_manual_token_secret_str():
    client = Client.from_token(url="/", token=SecretStr("the-token"))
    with pytest.raises(TypeError):
        pickle.dumps(client)


def test_cannot_pickle_client_credentials_login(scicat_access, require_scicat_backend):
    client = Client.from_credentials(
        url=scicat_access.url, **scicat_access.user.credentials
    )
    with pytest.raises(TypeError):
        pickle.dumps(client)


def test_connection_error_does_not_contain_token():
    client = Client.from_token(
        url="https://not-actually-a_server",
        token="the token/which_must-be.kept secret",  # noqa: S106
    )
    try:
        client.get_dataset("does not exist")
        assert False, "There must be an exception"  # noqa: B011
    except Exception as exc:
        assert "the token/which_must-be.kept secret" not in str(exc)
        for arg in exc.args:
            assert "the token/which_must-be.kept secret" not in str(arg)


def test_fake_can_disable_functions():
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
