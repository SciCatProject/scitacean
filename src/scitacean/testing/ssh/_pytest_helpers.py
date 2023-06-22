# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)

from typing import Optional

import pytest

_COMMAND_LINE_OPTION: Optional[str] = None


def add_pytest_option(parser: pytest.Parser, option: str = "--ssh-tests") -> None:
    """Add a command-line option to pytest to toggle SSH tests.

    Parameters
    ----------
    parser:
        Pytest's command-line argument parser.
    option:
        Name of the command-line option.
    """
    parser.addoption(
        option,
        action="store_true",
        default=False,
        help="Select whether to run tests with an SSH fileserver",
    )
    global _COMMAND_LINE_OPTION
    _COMMAND_LINE_OPTION = option


def skip_if_not_ssh(request: pytest.FixtureRequest) -> None:
    """Mark the current test to be skipped if SSH tests are disabled."""
    if not ssh_enabled(request):
        pytest.skip(
            "Tests against an SSH file server are disabled, "
            f"use {_COMMAND_LINE_OPTION} to enable them"
        )


def ssh_enabled(request: pytest.FixtureRequest) -> bool:
    """Return True if SSH tests are enabled."""
    return _COMMAND_LINE_OPTION is not None and bool(
        request.config.getoption(_COMMAND_LINE_OPTION)
    )
