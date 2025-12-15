# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 SciCat Project (https://github.com/SciCatProject/scitacean)

"""Validator for ORCIDs.

Based on
https://support.orcid.org/hc/en-us/articles/360006897674-Structure-of-the-ORCID-Identifier
"""

_ORCID_RESOLVER: str = "https://orcid.org"


def orcid_id_checksum(orcid_id: str) -> str:
    total = 0
    for c in orcid_id.replace("-", "")[:-1]:
        total = (total + int(c)) * 2
    result = (12 - total % 11) % 11
    return "X" if result == 10 else str(result)


def parse_orcid_id(value: str) -> str:
    match value.rsplit("/", 1):
        case [resolver, orcid_id]:
            if resolver != _ORCID_RESOLVER:
                # Must be the correct ORCID URL.
                raise ValueError(
                    f"Invalid ORCID URL: '{resolver}'. Must be '{_ORCID_RESOLVER}'"
                )
            parsed = value
        case [orcid_id]:
            parsed = f"{_ORCID_RESOLVER}/{value}"
        case _:
            raise RuntimeError("internal error")
    _check_id(orcid_id)
    return parsed


def _check_id(orcid_id: str) -> None:
    segments = orcid_id.split("-")
    if len(segments) != 4 or not all(len(s) == 4 for s in segments):
        # Must have 4 blocks of 4 digits each.
        raise ValueError(f"Invalid ORCID iD: '{orcid_id}'. Incorrect structure.")
    if orcid_id_checksum(orcid_id) != orcid_id[-1]:
        # Checksum must match the last digit.
        raise ValueError(f"Invalid ORCID iD: '{orcid_id}'. Checksum does not match.")
