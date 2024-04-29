# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)

import pickle
from datetime import datetime, timedelta, timezone

import pytest

from scitacean.util.credentials import SecretStr, Token


def test_secret_str_from_str_expose():
    secret_str = SecretStr("something hidden")
    assert secret_str.expose() == "something hidden"


def test_secret_str_from_secret_str_expose():
    secret_str = SecretStr(SecretStr("don't tell!"))
    assert secret_str.expose() == "don't tell!"


def test_secret_str_hides_content():
    secret_str = SecretStr("something hidden")
    assert "something hidden" not in str(secret_str)
    assert "hidden" not in str(secret_str)
    assert "something hidden" not in repr(secret_str)
    assert "hidden" not in repr(secret_str)


def test_secret_str_cannot_be_pickled():
    secret_str = SecretStr("something hidden")
    with pytest.raises(TypeError, match="pickle"):
        pickle.dumps(secret_str)


@pytest.mark.parametrize(
    "expires_at", [None, datetime.now(tz=timezone.utc) + timedelta(seconds=100)]
)
def test_token_from_str_expose(expires_at):
    token = Token("something hidden", expires_at=expires_at)
    assert token.expose() == "something hidden"


def test_token_from_secret_str_expose():
    token = Token(SecretStr("don't tell!"), expires_at=None)
    assert token.expose() == "don't tell!"


def test_token_from_token_expose():
    token = Token(Token("double-T", expires_at=None), expires_at=None)
    assert token.expose() == "double-T"


def test_token_hides_content():
    token = Token("something hidden", expires_at=None)
    assert "something hidden" not in str(token)
    assert "hidden" not in str(token)
    assert "something hidden" not in repr(token)
    assert "hidden" not in repr(token)


def test_token_cannot_be_pickled():
    token = Token("something hidden", expires_at=None)
    with pytest.raises(TypeError, match="pickle"):
        pickle.dumps(token)


def test_token_cannot_init_if_expired():
    with pytest.raises(RuntimeError, match="expired"):
        Token("token", expires_at=datetime.now(tz=timezone.utc) - timedelta(seconds=1))


def test_token_cannot_expose_if_expired():
    # Circumvent the check in __init__
    token = Token(
        "token", expires_at=datetime.now(tz=timezone.utc) + timedelta(seconds=100)
    )
    token._expires_at = datetime.now(tz=timezone.utc) - timedelta(seconds=1)
    with pytest.raises(RuntimeError, match="expired"):
        token.expose()


def test_token_expires_at_includes_denial_period():
    # Need a time in the future even within the denial period.
    base_expires_at = datetime.now(tz=timezone.utc) + timedelta(seconds=100)
    token = Token("", expires_at=base_expires_at, denial_period=timedelta(seconds=10))
    assert token.expires_at == base_expires_at - timedelta(seconds=10)
