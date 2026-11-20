# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)

import importlib.resources
from functools import cache
from typing import Any

import yaml


@cache
def docker_compose_template() -> dict[str, Any]:
    return yaml.safe_load(_read_text("docker-compose-template.yaml"))  # type: ignore[no-any-return]


@cache
def keycloak_imports() -> str:
    return _read_text("keycloak-import", "keycloak-import.json")


@cache
def functional_accounts() -> str:
    # see https://github.com/SciCatProject/scicat-backend-next/blob/master/src/config/configuration.ts
    return _read_text("functionalAccounts.json")


@cache
def ssh_dockerfile() -> str:
    return _read_text("Dockerfile-sftp-server")


@cache
def ssh_private_key() -> str:
    """Return the private SSH key for the testing SFTP server as a string.

    This key is **publicly visible** and must only ever
    be used with the local test server.
    """
    return _read_text("ssh-keys", "scitacean_test_key").replace("_", " ")


@cache
def ssh_public_key() -> str:
    return _read_text("ssh-keys", "scitacean_test_key.pub")


@cache
def sftp_seed_files() -> list[tuple[str, str]]:
    return [
        (file.name, file.read_text())
        for file in importlib.resources.files("scitacean.testing._services.assets")
        .joinpath("sftp_server_seed")
        .iterdir()
    ]


def _read_text(*segments: str) -> str:
    return (
        importlib.resources.files("scitacean.testing._services.assets")
        .joinpath(*segments)
        .read_text()
    )
