# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Exception classes."""


class FileUploadError(RuntimeError):
    """Raised when file upload fails."""


class IntegrityError(RuntimeError):
    """Raised when a dataset or file is broken."""


class ScicatCommError(RuntimeError):
    """Raised when communication with SciCat fails."""


class ScicatLoginError(RuntimeError):
    """Raised when login to SciCat server fails."""
