# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Tools for securely handling credentials."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import NoReturn

from .._internal.jwt import expiry


class StrStorage:
    """Base class for storing a string.

    Instances can be nested to combine different specialized features.
    """

    def __init__(self, value: str | StrStorage | None):
        self._value = value

    def get_str(self) -> str:
        """Return the stored plain str object."""
        if self._value is None:
            # If the implementation chooses to not
            # store the string in memory.
            # The method must be overridden in this case.
            raise NotImplementedError("String not available")

        if isinstance(self._value, StrStorage):
            return self._value.get_str()
        return self._value

    def __str__(self) -> str:
        return str(self._value)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._value!r})"


class SecretStr(StrStorage):
    """Minimize the risk of exposing a secret.

    Stores a string and blocks the most common pathways
    of leaking it to logs or files.

    Attention
    ---------
    The string may be stored as a regular, unencrypted str object and can
    still be leaked through introspection methods.
    """

    def __init__(self, value: str | StrStorage):
        super().__init__(value)

    def __str__(self) -> str:
        return "***"

    def __repr__(self) -> str:
        return "SecretStr(***)"

    # prevent pickling
    def __reduce_ex__(self, protocol: object) -> NoReturn:
        raise TypeError("SecretStr must not be pickled")


class ExpiringToken(StrStorage):
    """A JWT token that expires after some time."""

    def __init__(
        self,
        *,
        value: str | StrStorage,
        expires_at: datetime,
        denial_period: timedelta | None = None,
    ):
        super().__init__(value)
        if denial_period is None:
            denial_period = timedelta(seconds=2)
        self._expires_at = expires_at - denial_period
        self._check_expiry()

    @classmethod
    def from_jwt(cls, value: str | StrStorage) -> ExpiringToken:
        """Create a new ExpiringToken from a JSON web token."""
        value_str = value if isinstance(value, str) else value.get_str()
        try:
            expires_at = expiry(value_str)
        except ValueError:
            expires_at = datetime.now(tz=timezone.utc) + timedelta(weeks=100)
        return cls(
            value=value,
            expires_at=expires_at,
        )

    def get_str(self) -> str:
        """Return the stored plain str object."""
        self._check_expiry()
        return super().get_str()

    def _check_expiry(self) -> None:
        if datetime.now(tz=self._expires_at.tzinfo) > self._expires_at:
            raise RuntimeError(
                "SciCat login has expired. You need to create a new client either by "
                "logging in through `Client.from_credentials` or by getting a new "
                "access token from the SciCat web interface."
            )

    def __repr__(self) -> str:
        return (
            f"TimeLimitedStr(expires_at={self._expires_at.isoformat()}, "
            f"value={self._value!r}"
        )
