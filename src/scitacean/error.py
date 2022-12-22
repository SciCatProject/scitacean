# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen
"""Exception classes."""


class FileUploadError(RuntimeError):
    """Raised when file upload fails."""


class IntegrityError(RuntimeError):
    """Raised when a dataset or file is broken."""


class ScicatCommError(RuntimeError):
    """Raised when communication with SciCat fails."""


class ScicatLoginError(RuntimeError):
    """Raised when login to SciCat server fails."""
