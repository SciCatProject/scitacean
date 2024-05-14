# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Tools for securely handling credentials."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import NoReturn

from .._internal.jwt import expiry


class SecretStr:
    """Minimize the risk of exposing a secret.

    Stores a string and blocks the most common pathways
    of leaking it to logs or files.

    Attention
    ---------
    The string may be stored as a regular, unencrypted str object and can
    still be leaked through introspection methods.
    """

    def __init__(self, value: str | SecretStr) -> None:
        """Initialize from a plain str or other SecretStr.

        Parameters
        ----------
        value:
            The string to store.
        """
        self._value = value if isinstance(value, str) else value.expose()

    def expose(self) -> str:
        """Return the stored plain str object."""
        return self._value

    def __str__(self) -> str:
        return "***"

    def __repr__(self) -> str:
        return "SecretStr(***)"

    # prevent pickling
    def __reduce_ex__(self, protocol: object) -> NoReturn:
        raise TypeError(
            "SecretStr must not be pickled to avoid storing or sharing "
            "it accidentally."
        )


class Token(SecretStr):
    """A SciCat token that may expire after some time."""

    def __init__(
        self,
        value: str | SecretStr | Token,
        *,
        expires_at: datetime | None,
        denial_period: timedelta | None = None,
    ) -> None:
        """Initialize from a plain or secret string or other token.

        Parameters
        ----------
        value:
            The string of the token to store.
            If a ``Token`` object, the expiry date is overridden by ``expires_at``.
        expires_at:
            Datetime after which the token is no longer valid.
            If ``None``, the token is assumed to never expire.
        denial_period:
            If given, the token will be treated as expired after
            ``expires_at - denial_period``.
            This is useful to give an operation enough leeway to finish before the
            token actually expires.
        """
        super().__init__(value.expose() if isinstance(value, Token) else value)
        if expires_at is None:
            self._expires_at = None
        else:
            if denial_period is None:
                self._expires_at = expires_at
            else:
                self._expires_at = expires_at - denial_period
        self._check_expiry()

    @classmethod
    def from_jwt(
        cls,
        value: str | SecretStr,
        denial_period: timedelta | None = None,
    ) -> Token:
        """Create a new ExpiringToken from a JSON web token.

        Parameters
        ----------
        value:
            A JSON web token.
        denial_period:
            If given, the token will be treated as expired after
            ``expires_at - denial_period``.
            This is useful to give an operation enough leeway to finish before the
            token actually expires.

        Returns
        -------
        :
            A ``Token`` object that contains ``value`` and is
            set up with an expiry date parsed from the JWT.
        """
        value_str = value if isinstance(value, str) else value.expose()
        try:
            expires_at = expiry(value_str)
        except ValueError:
            expires_at = None
        return cls(
            value=value,
            expires_at=expires_at,
            denial_period=denial_period,
        )

    def expose(self) -> str:
        """Return the stored plain str object.

        Returns
        -------
        :
            A plain string with the token.

        Raises
        ------
        RuntimeError
            If the token has expired.
        """
        self._check_expiry()
        return super().expose()

    @property
    def expires_at(self) -> datetime | None:
        """Return the expiration date including denial period."""
        return self._expires_at

    def _check_expiry(self) -> None:
        if (
            self._expires_at is not None
            and datetime.now(tz=self._expires_at.tzinfo) > self._expires_at
        ):
            raise RuntimeError(
                "SciCat login has expired. You need to create a new client either by "
                "logging in through `Client.from_credentials` or by getting a new "
                "access token from the SciCat web interface."
            )

    def __repr__(self) -> str:
        expires = self.expires_at.isoformat() if self.expires_at is not None else None
        return f"Token(***, expires_at={expires})"
