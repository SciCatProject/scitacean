# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Python version-independent dataclasses."""

import dataclasses
from typing import Callable, Type, TypeVar

T = TypeVar("T")


def dataclass_optional_args(
    kw_only: bool = False, slots: bool = False, **kwargs
) -> Callable[[Type[T]], Type[T]]:
    """Create a dataclass with modern arguments."""
    try:
        # Python 3.10+
        return dataclasses.dataclass(kw_only=kw_only, slots=slots, **kwargs)
    except TypeError:
        # Fallback for older Python
        return dataclasses.dataclass(**kwargs)
