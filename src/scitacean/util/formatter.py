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
        formatter.format("{owner}-{pid.pid}", dset)
        # is equivalent to (up to escaping)
        "{0.owner}-{0.pid.pid}".format(dset)

    This means that all format fields are transformed to access attributes
    for the first argument of ``format``. ``format`` thus supports only a
    single argument.

    In addition, all field values are escaped as filesystem paths
    using :func:`scitacean.filesystem.escape_path`:

    .. code-block:: python

        formatter = DatasetPathFormatter()
        formatter.format("a string {owner}", dset)
        # is equivalent to
        "a string {}".format(escape_path("{0.owner}".format(dset)))

    Note that only formatted fields are escaped, not the result as a whole.
    """

    def parse(
        self, format_string: str
    ) -> Iterator[Tuple[str, Optional[str], Optional[str], Optional[str]]]:
        def add0(field_name: Optional[str]) -> Optional[str]:
            return "0." + field_name if isinstance(field_name, str) else None

        return map(
            lambda t: (t[0], add0(t[1]), t[2], t[3]), super().parse(format_string)
        )

    def format_field(self, value: Any, format_spec: str) -> str:
        return escape_path(super().format_field(value, format_spec))
