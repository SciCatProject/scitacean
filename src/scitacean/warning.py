# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)

"""Custom warning classes."""


class VisibleDeprecationWarning(UserWarning):
    """Visible deprecation warning.

    By default, Python and in particular Jupyter will not show deprecation
    warnings, so this class can be used when a very visible warning is helpful.
    """


VisibleDeprecationWarning.__module__ = "scitacean"
