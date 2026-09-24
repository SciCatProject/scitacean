# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)
"""User agent / web browser support."""

from __future__ import annotations

import webbrowser
from functools import cache
from typing import Any


def open_in_browser(url: str) -> OutputHandle:
    """Open a URL in the default web browser as a new tab.

    Parameters
    ----------
    url:
        The URL to open.

    Returns
    -------
    :
        A handle to the *output widget*, not the browser window.
        The returned object closes a Jupyter widget used to open the URL
        when running in Jupyter. It does not close the opened browser window / tab.
    """
    try:
        if webbrowser.open_new_tab(url):
            return OutputHandle(None)
        if (out := _open_in_browser_from_jupyter(url)) is not None:
            return out
        raise RuntimeError("Unable to open a web browser")
    except Exception as error:
        error.add_note(
            f"Please open the following URL in your browser: {url}\n"
            "If no browser is available on your system, use a different login method."
        )
        raise


class OutputHandle:
    """An output object that needs to be closed."""

    def __init__(self, output: Any) -> None:
        self._output = output

    def close(self) -> None:
        """Close this output."""
        if self._output is not None:
            self._output.close()


def _open_in_browser_from_jupyter(url: str) -> OutputHandle | None:
    if not _running_in_jupyter():
        return None

    try:
        from IPython.display import (
            HTML,
            Javascript,
            display,
            display_html,
            display_javascript,
        )
        from ipywidgets import Output
    except ImportError:
        return None

    out = Output()
    with out:
        display_javascript(  # type: ignore[no-untyped-call]
            Javascript(  # type: ignore[no-untyped-call]
                f"""
const win = window.open("{url}", '_blank');
if (win !== null) {{win.focus();}}
"""
            )
        )
        display_html(  # type: ignore[no-untyped-call]
            HTML(f"""
<div>To <b>sign in</b> with SciCat, open this link in your browser if it did not
open automatically:<div>
<div><a href="{url}" target=_blank>{url}</a></div>
""")  # type: ignore[no-untyped-call]
        )
    display(out)  # type: ignore[no-untyped-call]

    return OutputHandle(out)


@cache
def _running_in_jupyter() -> bool:
    try:
        from IPython import get_ipython

        ipython = get_ipython()
        if ipython is None:
            return False
        # Check if it's a Jupyter kernel specifically
        return "IPKernelApp" in ipython.config
    except ImportError:
        return False
