# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Tools for securely handling credentials."""
from __future__ import annotations

import datetime
from typing import NoReturn, Optional, Union


class StrStorage:
    """Base class for storing a string.

    Instances can be nested to combine different specialized features.
    """

    def __init__(self, value: Optional[Union[str, StrStorage]]):
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


# TODO implement
# class KeyringStr(StrStorage):
#     """Store a string in the user's keyring.
#
#     Should be the bottom level StrStorage because it erases any nested
#     StrStorage objects and stores and returns plain strs.
#     """
#
#     def __init__(self, *, key: str, value: Optional[Union[str, StrStorage]]):
#         super().__init__(None)
#         # TODO dummy implementation
#         self._ring = {}
#         self._key = key
#         if value is not None:
#             if isinstance(value, StrStorage):
#                 self._store(value.get_str())
#             else:
#                 self._store(value)
#
#     def _store(self, value: str):
#         self._ring[self._key] = value
#
#     def _retrieve(self) -> str:
#         return self._ring[self._key]
#
#     def get_str(self) -> str:
#         return self._retrieve()
#
#     def __str__(self) -> str:
#         return "???"
#
#     def __repr__(self) -> str:
#         return f"KeyringStr(key='{self._key}', value={str(self)})"


class SecretStr(StrStorage):
    """Minimize the risk of exposing a secret.

    Stores a string and blocks the most common pathways
    of leaking it to logs or files.

    Attention
    ---------
    The string may be stored as a regular, unencrypted str object and can
    still be leaked through introspection methods.
    """

    def __init__(self, value: Union[str, StrStorage]):
        super().__init__(value)

    def __str__(self) -> str:
        return "***"

    def __repr__(self) -> str:
        return "SecretStr(***)"

    # prevent pickling
    def __reduce_ex__(self, protocol: object) -> NoReturn:
        raise TypeError("SecretStr must not be pickled")


class TimeLimitedStr(StrStorage):
    """A string that expires after some time."""

    def __init__(
        self,
        *,
        value: Union[str, StrStorage],
        expires_at: datetime.datetime,
        tolerance: Optional[datetime.timedelta] = None,
    ):
        super().__init__(value)
        if tolerance is None:
            tolerance = datetime.timedelta(seconds=10)
        self._expires_at = expires_at - tolerance

    def get_str(self) -> str:
        if self._is_expired():
            raise RuntimeError("Login has expired")
        return super().get_str()

    def _is_expired(self) -> bool:
        return datetime.datetime.now() > self._expires_at

    def __repr__(self) -> str:
        return (
            f"TimeLimitedStr(expires_at={self._expires_at.isoformat()}, "
            f"value={repr(self._value)}"
        )
