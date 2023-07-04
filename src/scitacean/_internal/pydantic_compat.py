# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
import pydantic


def is_pydantic_v1() -> bool:
    return pydantic.__version__.split(".", 1)[0] == "1"
