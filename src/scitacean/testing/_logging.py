# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Logging for Scitacean tests."""

import logging


def get_logger() -> logging.Logger:
    """Return the Scitacean testing logger."""
    return logging.getLogger("scitacean.testing")
