# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Assets for authentication."""

import importlib.resources
from functools import cache
from string import Template


@cache
def auth_redirect_page_template() -> Template:
    """Return a template for an HTML page to display after redirecting from the IdP."""
    return Template(_read_text("auth_redirect_page.html.template"))


@cache
def auth_redirect_success() -> str:
    """Return HTML code for a successful authentication."""
    return _read_text("auth_redirect_success.html")


@cache
def auth_redirect_failure() -> str:
    """Return HTML code for a failed authentication."""
    return _read_text("auth_redirect_failure.html")


def _read_text(filename: str) -> str:
    return (
        importlib.resources.files("scitacean.auth._assets")
        .joinpath(filename)
        .read_text()
    )
