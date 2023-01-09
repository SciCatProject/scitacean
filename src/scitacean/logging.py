# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Utilities for logging in Scitacean.

The object returned by :func:`scitacean.get_logger` is the only logger
used by Scitacean. Scitacean does not configure it in any way.
You are free to do so.
"""

import logging


def logger_name() -> str:
    """Return the name of Scitacean's logger."""
    return "scitacean"


def get_logger() -> logging.Logger:
    """Return the logger used by Scitacean."""
    return logging.getLogger(logger_name())
