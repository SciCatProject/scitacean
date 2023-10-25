# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
from typing import Any, Callable, Literal

import pydantic


def is_pydantic_v1() -> bool:
    if pydantic.__version__.split(".", 1)[0] == "1":
        import warnings

        from ..warning import VisibleDeprecationWarning

        warnings.warn(
            "Support for Pydantic v1 is deprecated in Scitacean"
            "23.10.0 and will be removed in Scitacean v23.12.0."
            "If you cannot update your Pydantic version, please comment in this issue:"
            " https://github.com/SciCatProject/scitacean/issues/158",
            VisibleDeprecationWarning,
            stacklevel=2,
        )
        return True

    return False


def field_validator(
    *args: Any,
    mode: Literal["before", "after", "wrap", "plain"] = "after",
    **kwargs: Any,
) -> Callable[[Any], Any]:
    if is_pydantic_v1():
        return pydantic.validator(*args, pre=(mode == "before"), **kwargs)
    return pydantic.field_validator(*args, mode=mode, **kwargs)
