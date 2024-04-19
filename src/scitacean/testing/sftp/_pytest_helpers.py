# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)


import pytest

_COMMAND_LINE_OPTION: str | None = None


def add_pytest_option(parser: pytest.Parser, option: str = "--sftp-tests") -> None:
    """Add a command-line option to pytest to toggle SFTP tests.

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
        help="Select whether to run tests with an SFTP fileserver",
    )
    global _COMMAND_LINE_OPTION
    _COMMAND_LINE_OPTION = option


def skip_if_not_sftp(request: pytest.FixtureRequest) -> None:
    """Mark the current test to be skipped if SFTP tests are disabled."""
    if not sftp_enabled(request):
        pytest.skip(
            "Tests against an SFTP file server are disabled, "
            f"use {_COMMAND_LINE_OPTION} to enable them"
        )


def sftp_enabled(request: pytest.FixtureRequest) -> bool:
    """Return True if SFTP tests are enabled."""
    return _COMMAND_LINE_OPTION is not None and bool(
        request.config.getoption(_COMMAND_LINE_OPTION)
    )
