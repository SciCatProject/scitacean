# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Python version-independent dataclasses."""

import dataclasses
from typing import Any, Callable, Type, TypeVar

T = TypeVar("T")


try:
    from typing import dataclass_transform
except ImportError:
    from typing import Tuple, Union

    F = TypeVar("F")

    def dataclass_transform(
        *,
        eq_default: bool = True,
        order_default: bool = False,
        kw_only_default: bool = False,
        frozen_default: bool = False,
        field_specifiers: Tuple[Union[Type[Any], Callable[..., Any]], ...] = (),
        **kwargs: Any,
    ) -> Callable[[T], T]:
        def impl(f: F) -> F:
            return f

        return impl


@dataclass_transform()
def dataclass_optional_args(
    kw_only: bool = False, slots: bool = False, **kwargs: Any
) -> Callable[[Type[T]], Type[T]]:
    """Create a dataclass with modern arguments."""
    try:
        # Python 3.10+
        return dataclasses.dataclass(kw_only=kw_only, slots=slots, **kwargs)
    except TypeError:
        # Fallback for older Python
        return dataclasses.dataclass(**kwargs)
