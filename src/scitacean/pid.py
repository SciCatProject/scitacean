# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
from __future__ import annotations

import uuid
from typing import Callable, Generator, Optional, Union


class PID:
    """Stores the ID of database item.

    The ID is split into a prefix and the main identifier.
    The prefix identifies an instance of SciCat and the main identifier a dataset.

    The two components are merged using a "/", i.e.

    .. code-block:: python

        full_id = PID.prefix + '/' + PID.pid

    Equivalently, ``str`` can be used to construct the full id:

    .. code-block:: python

        full_id = str(PID)
    """

    __slots__ = ("_pid", "_prefix")

    def __init__(self, *, pid: str, prefix: Optional[str] = None):
        """Initialize an instance from individual components.

        Parameters
        ----------
        pid:
            Main part of the ID which uniquely identifies a dataset.
        prefix:
            Identifies the instance of SciCat.
        """
        self._pid = pid
        self._prefix = prefix

    @classmethod
    def parse(cls, x: Union[str, PID]) -> PID:
        """Build a PID from a string.

        The string is split at the first "/" to determine
        prefix and main ID.
        This means that it only works if the prefix and main ID do
        not contain any slashes.

        Parameters
        ----------
        x:
            String holding an ID with or without prefix.
            Or a PID object, in which case a copy is returned.

        Returns
        -------
        :
            A new PID object constructed from ``x``.
        """
        if isinstance(x, PID):
            return PID(pid=x.pid, prefix=x.prefix)
        pieces = x.split("/", 1)
        if len(pieces) == 1:
            return PID(pid=pieces[0], prefix=None)
        return PID(prefix=pieces[0], pid=pieces[1])

    @classmethod
    def generate(cls, *, prefix: Optional[str] = None) -> PID:
        """Create a new unique PID.

        Uses UUID4 to generate the ID.

        Parameters
        ----------
        prefix:
            If given, the returned PID has this prefix.

        Returns
        -------
        :
            A new PID object.
        """
        return PID(prefix=prefix, pid=str(uuid.uuid4()))

    @property
    def pid(self) -> str:
        """Main part of the ID."""
        return self._pid

    @property
    def prefix(self) -> Optional[str]:
        """Prefix part of the ID if there is one."""
        return self._prefix

    @property
    def without_prefix(self) -> PID:
        """Return a new PID with the prefix set to None."""
        return PID(pid=self.pid, prefix=None)

    def __str__(self) -> str:
        if self.prefix is not None:
            return self.prefix + "/" + self.pid
        return self.pid

    def __repr__(self) -> str:
        return f"PID(prefix={self.prefix}, pid={self.pid})"

    def __hash__(self) -> int:
        return hash(str(self))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PID):
            return False
        return self.prefix == other.prefix and self.pid == other.pid

    @classmethod
    def __get_validators__(
        cls,
    ) -> Generator[Callable[[Union[str, PID]], PID], None, None]:
        yield cls.validate

    @classmethod
    def validate(cls, value: Union[str, PID]) -> PID:
        """Pydantic validator for PID fields."""
        if isinstance(value, str):
            return PID.parse(value)
        if isinstance(value, PID):
            return value
        raise TypeError("expected a PID or str")
