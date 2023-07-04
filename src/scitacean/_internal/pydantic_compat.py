# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
from typing import Any

import pydantic


def is_pydantic_v1() -> bool:
    return pydantic.__version__.split(".", 1)[0] == "1"


def field_validator(*args: Any, **kwargs: Any) -> Any:
    if is_pydantic_v1():
        return pydantic.validator(*args, **kwargs)
    return pydantic.field_validator(*args, **kwargs)
