# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)

from typing import Optional

import pytest

_COMMAND_LINE_OPTION: Optional[str] = None


def add_pytest_option(parser: pytest.Parser, option: str = "--backend-tests") -> None:
    parser.addoption(
        option,
        action="store_true",
        default=False,
        help="Select whether to run tests against a real SciCat backend",
    )
    global _COMMAND_LINE_OPTION
    _COMMAND_LINE_OPTION = option


def skip_if_not_backend(request):
    if not backend_enabled(request):
        pytest.skip(
            "Tests against a real backend are disabled, "
            f"use {_COMMAND_LINE_OPTION} to enable them"
        )


def backend_enabled(request: pytest.FixtureRequest) -> bool:
    return _COMMAND_LINE_OPTION and request.config.getoption(_COMMAND_LINE_OPTION)
