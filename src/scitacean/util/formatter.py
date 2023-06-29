# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
"""String-formatting tools."""

from string import Formatter
from typing import Any, Iterator, Optional, Tuple

from ..filesystem import escape_path


class DatasetPathFormatter(Formatter):
    """Formatter that inserts dataset fields and escapes paths.

    This formatter automatically modifies format strings such that the
    following two are equivalent (up to escaping, see below).

    .. code-block:: python

        formatter = DatasetPathFormatter()
        formatter.format("{owner}-{pid.pid}-{uid}", dset=dset, uid=uid)
        # is equivalent to (up to escaping)
        "{dset.owner}-{dset.pid.pid}-{uid}".format(dset=dset, uid=uid)

    This means that all format fields are transformed to access attributes
    of the keyword argument ``dset``.
    Except for ``"uid"`` which is preserved to allow for a dedicated ``uid`` keyword.

    In addition, all field values are escaped as filesystem paths
    using :func:`scitacean.filesystem.escape_path`:

    .. code-block:: python

        formatter = DatasetPathFormatter()
        formatter.format("a string {owner}", dset=dset)
        # is equivalent to
        "a string {}".format(escape_path("{dset.owner}".format(dset=dset)))

    Note that only formatted fields are escaped, not the result as a whole.

    Fields that are used by the formatter must not be ``None``.
    Otherwise, a :class:`ValueError` will be raised.
    """

    def parse(
        self, format_string: str
    ) -> Iterator[Tuple[str, Optional[str], Optional[str], Optional[str]]]:
        def add0(field_name: Optional[str]) -> Optional[str]:
            if field_name == "uid":
                return field_name
            if isinstance(field_name, str):
                return "dset." + field_name
            return None

        return map(
            lambda t: (t[0], add0(t[1]), t[2], t[3]), super().parse(format_string)
        )

    def format_field(self, value: Any, format_spec: str) -> str:
        if value is None:
            raise ValueError("Cannot format path, dataset field is None")
        return escape_path(super().format_field(value, format_spec))
