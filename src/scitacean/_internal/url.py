# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)


def url_concat(a: str, b: str) -> str:
    """Combine two pieces or a URL without handling absolute paths as in urljoin."""
    a = a if a.endswith("/") else (a + "/")
    b = b[1:] if b.endswith("/") else b
    return a + b
