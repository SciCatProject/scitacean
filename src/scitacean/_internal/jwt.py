# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Tools for JSON web tokens."""

import base64
import json
from datetime import datetime, timezone
from typing import cast


def decode(token: str) -> tuple[dict[str, str | int], dict[str, str | int], str]:
    """Decode the components of a JSOn web token."""
    h, p, signature = token.split(".")
    header = _decode_part(h)
    payload = _decode_part(p)
    return header, payload, signature


def expiry(token: str) -> datetime:
    """Return the expiration time of a JWT in UTC."""
    _, payload, _ = decode(token)
    # 'exp' should always be given in UTC. Since we have no way of checking that,
    # assume that it is the case.
    return datetime.fromtimestamp(float(payload["exp"]), tz=timezone.utc)


def _decode_part(s: str) -> dict[str, str | int]:
    # urlsafe_b64decode requires a properly padded input but SciCat
    # doesn't pad its tokens.
    padded = s + "=" * (len(s) % 4)
    decoded_str = base64.urlsafe_b64decode(padded).decode("utf-8")
    return cast(dict[str, str | int], json.loads(decoded_str))
