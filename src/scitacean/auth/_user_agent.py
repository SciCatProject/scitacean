# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)
"""User agent / web browser support."""

import webbrowser


def open_in_browser(url: str) -> None:
    """Open a URL in the default web browser as a new tab."""
    try:
        result = webbrowser.open_new_tab(url)
    except webbrowser.Error as error:
        error.add_note(
            f"Please open the following URL in your browser: {url}\n"
            "If no browser is available on your system, use a different login method."
        )
        raise
    if not result:
        raise ValueError("Failed to open URL in browser")
