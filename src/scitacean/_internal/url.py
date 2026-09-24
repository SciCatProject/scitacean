# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)

from collections.abc import Sequence
from urllib.parse import urlsplit


def url_concat(a: str, b: str) -> str:
    """Combine two pieces or a URL without handling absolute paths as in urljoin."""
    a = a if a.endswith("/") else (a + "/")
    b = b.removeprefix("/")
    return a + b


def require_scheme(url: str, allowed: Sequence[str], what: str) -> None:
    """Raise ValueError if the URL does not have one of the allowed schemes."""
    scheme = urlsplit(url).scheme
    if scheme not in allowed:
        what = what + " " if what else ""
        raise ValueError(
            f"The {what}URL must have one of the following schemes: "
            f"{list(allowed)}\nGot {url}"
        )
