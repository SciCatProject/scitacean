# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 SciCat Project (https://github.com/SciCatProject/scitacean)


import pytest

_COMMAND_LINE_OPTION: str | None = None


def add_pytest_options(parser: pytest.Parser, option: str = "--backend-tests") -> None:
    """Add command-line options to pytest to control backend tests.

    Parameters
    ----------
    parser:
        Pytest's command-line argument parser.
    option:
        Name of the command-line option to toggle backend tests.
    """
    parser.addoption(
        option,
        action="store_true",
        default=False,
        help="Select whether to run tests against a real SciCat backend",
    )
    global _COMMAND_LINE_OPTION
    _COMMAND_LINE_OPTION = option

    parser.addoption(
        "--scitacean-backend-version",
        default=None,
        help="Specify a version for the SciCat backend",
    )


def skip_if_not_backend(request: pytest.FixtureRequest) -> None:
    """Mark the current test to be skipped if backend tests are disabled."""
    if not backend_enabled(request):
        pytest.skip(
            "Tests against a real backend are disabled, "
            f"use {_COMMAND_LINE_OPTION} to enable them"
        )


def backend_enabled(request: pytest.FixtureRequest) -> bool:
    """Return True if backend tests are enabled."""
    return _COMMAND_LINE_OPTION is not None and bool(
        request.config.getoption(_COMMAND_LINE_OPTION)
    )
