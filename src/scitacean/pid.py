from __future__ import annotations
from typing import Optional


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
        """

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
    def parse(cls, x: str) -> PID:
        """Build a PID from a string.

        The string is split at the first "/" to determine
        prefix and main ID.
        This means that it only works if the prefix and main ID do
        not contain any slashes.

        Parameters
        ----------
        x:
            String holding an ID with or without prefix.

        Returns
        -------
        :
            A new PID object constructed from ``x``.
        """
        pieces = x.split("/", 1)
        if len(pieces) == 1:
            return PID(pid=pieces[0], prefix=None)
        return PID(prefix=pieces[0], pid=pieces[1])

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

    def __str__(self):
        if self.prefix is not None:
            return self.prefix + "/" + self.pid
        return self.pid

    def __repr__(self):
        return f"PID(prefix={self.prefix}, pid={self.pid})"

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return str(self) == str(other)
