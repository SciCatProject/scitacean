# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Tools for Proof Key for Code Exchange (PKCE)."""

# The code here was adapted from https://github.com/RomeoDespres/pkce

import base64
import hashlib
import secrets
import warnings
from collections.abc import Sequence


def generate_pkce_pair(
    challenge_methods_supported: Sequence[str], code_verifier_length: int = 128
) -> tuple[str, tuple[str, str]]:
    """Generate a PKCE code verifier and matching code challenge."""
    code_verifier = _generate_code_verifier(code_verifier_length)
    code_challenge_and_method = _compute_code_challenge(
        code_verifier, challenge_methods_supported
    )
    return code_verifier, code_challenge_and_method


def _generate_code_verifier(length: int = 128) -> str:
    """Generate a code verifier of the given length."""
    if not 43 <= length <= 128:
        raise ValueError("Parameter `length` must be between 43 and 128.")

    # Need to generate enough bytes to get `length` characters:
    code_verifier = secrets.token_urlsafe(128)[:length]
    return code_verifier


def _compute_code_challenge(
    code_verifier: str, challenge_methods_supported: Sequence[str]
) -> tuple[str, str]:
    """Compute the code challenge from the given code verifier.

    Returns the code challenge and the code challenge method.
    """
    method = "S256"
    if method not in challenge_methods_supported:
        warnings.warn(
            "The identity provider does not promise support for challenge "
            f"method '{method}'. It only reports methods "
            f"({', '.join(challenge_methods_supported)}). Proceeding with method "
            f"'{method}' regardless because nothing else is implemented. "
            f"This may fail.",
            UserWarning,
            stacklevel=3,
        )

    hashed = hashlib.sha256(code_verifier.encode("ascii")).digest()
    encoded = base64.urlsafe_b64encode(hashed)
    return encoded.decode("ascii").rstrip("="), method
