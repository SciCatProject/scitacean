# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)
"""User agent / web browser support."""

from __future__ import annotations

import html
import json
import webbrowser
from functools import cache
from typing import Any

from ..typing import SupportsClose


def open_in_browser(url: str) -> SupportsClose:
    """Open a URL in the default web browser as a new tab.

    This uses the standard library :mod:`webbrowser` if possible.
    When running on a remote Jupyter Lab instance, this function emits
    some JavaScript into the notebook and displays a help message.

    Parameters
    ----------
    url:
        The URL to open.

    Returns
    -------
    :
        When using Jupyter to open the tab, this is a handle that
        removes the generated output from the notebook.
        It does *not* close the browser tab.

        When using the ``webbrowser`` module, the returned handle does nothing.
    """
    try:
        if webbrowser.open_new_tab(url):
            return _NullClosingHandle()
        if (out := _open_in_browser_from_jupyter(url)) is not None:
            return out
    except (RuntimeError, webbrowser.Error):
        pass
    print(  # noqa: T201
        "Failed to open a web browser. "
        f"Please open this URL in a web browser to log in: {url}"
    )
    return _NullClosingHandle()


class _NullClosingHandle:
    """An object with a close method that does nothing."""

    def close(self) -> None:
        pass


class _NbClosingHandle:
    """An output object that needs to be closed."""

    def __init__(self, *handles: Any) -> None:
        self._handles = handles

    def close(self) -> None:
        """Close this output."""
        from IPython.display import HTML

        for handle in self._handles:
            handle.update(HTML(""))  # type: ignore[no-untyped-call]


def _open_in_browser_from_jupyter(url: str) -> _NbClosingHandle | None:
    if not _running_in_jupyter():
        return None

    try:
        from IPython.display import HTML, Javascript, display
    except ImportError:
        return None

    js_handle = display(  # type: ignore[no-untyped-call]
        Javascript(  # type: ignore[no-untyped-call]
            f"""
const win = window.open({json.dumps(url)}, '_blank');
if (win !== null) {{win.focus();}}
"""
        ),
        display_id=True,
    )
    html_handle = display(  # type: ignore[no-untyped-call]
        HTML(  # type: ignore[no-untyped-call]
            f"""
<div>To <b>sign in</b> with SciCat, open this link in your browser if it did not
open automatically:<div>
<div><a href="{html.escape(url)}" target=_blank>{html.escape(url)}</a></div>
"""
        ),
        display_id=True,
    )

    return _NbClosingHandle(js_handle, html_handle)


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
