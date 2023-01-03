# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)

"""Validator for ORCIDs.

Based on
https://support.orcid.org/hc/en-us/articles/360006897674-Structure-of-the-ORCID-Identifier
"""


def orcid_checksum(orcid_id: str) -> str:
    total = 0
    for c in orcid_id.replace("-", "")[:-1]:
        total = (total + int(c)) * 2
    result = (12 - total % 11) % 11
    return "X" if result == 10 else str(result)


def is_valid_orcid(orcid_uri: str) -> bool:
    base, orcid_id = orcid_uri.rsplit("/", 1)
    if base != "https://orcid.org":
        # must start with the ORCID URL
        return False
    if orcid_id.count("-") != 3:
        # must have four blocks of numbers
        return False
    if not all(len(x) == 4 for x in orcid_id.split("-")):
        # each block must have 4 digits
        return False
    if orcid_checksum(orcid_id) != orcid_id[-1]:
        # checksum must match last digit
        return False
    return True
