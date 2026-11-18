# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)
"""Backend configuration."""

from dataclasses import dataclass
from typing import Any, overload

from ...client import Client
from .._services.config import SCICAT_PORT, ScicatUser, scicat_users
from ..client import FakeClient


@dataclass
class SciCatAccess:
    """Access parameters for a local SciCat backend."""

    url: str
    user: ScicatUser

    @overload
    def make_client(
        self, client_class: type[FakeClient], **kwargs: Any
    ) -> FakeClient: ...

    @overload
    def make_client(self, client_class: type[Client], **kwargs: Any) -> Client: ...

    def make_client(
        self,
        client_class: type[Client] | type[FakeClient],
        **kwargs: Any,
    ) -> Client | FakeClient:
        """Construct and authenticate a client for this SciCat backend."""
        return client_class.from_credentials(
            url=self.url, allow_http=True, **self.user.credentials, **kwargs
        )


def local_access(user: str) -> SciCatAccess:
    """Return parameters to connect a client to a local SciCat backend.

    Parameters
    ----------
    user:
        User name.
        Must be in :attr:`scitacean.testing.backend.config.USERS`.

    Returns
    -------
    :
        Parameters for the local SciCat backend.
    """
    return SciCatAccess(
        url=f"http://localhost:{SCICAT_PORT}/api/v3/", user=scicat_users()[user]
    )
