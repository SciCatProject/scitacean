# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)

import json
import logging
import os
from copy import deepcopy
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any, TypedDict

import yaml

from . import assets

KEYCLOAK_PORT = 8080
"""Port of Keycloak on localhost."""
SCICAT_PORT = 3000
"""Port of the SciCat server on localhost."""
SFTP_PORT = 2222
"""Port of the SFTP server on localhost."""
SFTP_DATA_DIR_NAME = "sftp_data"
"""Name of the host directory (relative to the docker project) mounted as ``/data``."""


class ScicatCredentials(TypedDict):
    """A dict with testing credentials for SciCat."""

    username: str
    password: str


@dataclass
class ScicatUser:
    """A SciCat user.

    Warning
    -------
    Only ever use this for testing!
    This class does not have the usual protections against
    leaks of secrets used by the client.
    """

    username: str
    password: str
    email: str
    group: str
    role: str

    def __init__(
        self,
        *,
        username: str,
        password: str,
        email: str,
        role: str,
        **_kwargs: object,
    ) -> None:
        self.username = username
        self.password = password
        self.email = email
        self.group = role

    @property
    def credentials(self) -> ScicatCredentials:
        """Return login credentials for this user.

        User as

        .. code-block:: python

            client = Client.from_credentials(url="...", **user.credentials)
        """
        return {
            "username": self.username,
            "password": self.password,
        }


@cache
def scicat_users() -> dict[str, ScicatUser]:
    """Return the preconfigured functional accounts of SciCat."""
    return {
        user["username"]: ScicatUser(**user)
        for user in json.loads(assets.functional_accounts())
    }


def configure_services(
    output_dir: Path, *, docker_filename: str, scicat_version: str | None
) -> Path:
    """Write a docker compose file and aux and seed files for all testing services."""
    logging.getLogger("scitacean.testing").info(
        "Configuring testing docker services in %s", output_dir
    )
    _write_ssh_dockerfile(output_dir)
    account_config_path = _write_account_config(output_dir)
    realm_import_path = _write_keycloak_imports(output_dir)
    pubkey_dir = _write_ssh_pubkeys(output_dir)
    sftp_data_dir = _write_sftp_data(output_dir)

    config = _apply_config(
        assets.docker_compose_template(),
        scicat_version=scicat_version,
    )
    _write_env(
        output_dir,
        account_config_path=account_config_path,
        realm_import_path=realm_import_path,
        pubkey_dir=pubkey_dir,
        sftp_data_dir=sftp_data_dir,
    )
    path = output_dir.joinpath(docker_filename)
    with open(path, "w") as f:
        yaml.dump(config, f)
    return path


def _apply_config(
    template: dict[str, Any],
    *,
    scicat_version: str | None,
) -> dict[str, Any]:
    configured = deepcopy(template)
    _apply_config_scicat_in_place(
        configured["services"]["scicat"],
        scicat_version=scicat_version,
    )
    return configured


def _apply_config_scicat_in_place(
    scicat: dict[str, Any],
    *,
    scicat_version: str | None,
) -> None:
    if scicat_version is not None:
        url = scicat["image"].split(":")[0]
        scicat["image"] = f"{url}:{scicat_version}"


def _apply_config_network_in_place(network: dict[str, Any]) -> None:
    network["ports"] = [
        f"{SFTP_PORT}:{SFTP_PORT}",
        f"{SCICAT_PORT}:{SCICAT_PORT}",
        # Keycloak always listens on 8080 in the container
        f"8080:{KEYCLOAK_PORT}",
    ]


def _write_env(
    parent: Path,
    *,
    pubkey_dir: Path,
    account_config_path: Path,
    realm_import_path: Path,
    sftp_data_dir: Path,
) -> None:
    ports = (
        ("SCICAT_PORT", SCICAT_PORT),
        ("KEYCLOAK_PORT", KEYCLOAK_PORT),
        ("SFTP_PORT", SFTP_PORT),
    )
    paths = (
        ("SCICAT_ACCOUNT_CONFIG_PATH", account_config_path),
        ("SSH_PUBKEY_DIR", pubkey_dir),
        ("SFTP_DATA_DIR", sftp_data_dir),
        ("SFTP_SEED_DIR", sftp_data_dir / "seed"),
        ("KEYCLOACK_REALM_IMPORT_DIR", realm_import_path),
    )

    normalized_paths = [(name, os.fspath(path.absolute())) for name, path in paths]
    settings = [*ports, *normalized_paths]
    logging.getLogger("scitacean.testing").info(
        "Configuring test services with:\n  %s",
        "\n  ".join(f"{name} = {value}" for name, value in settings),
    )
    parent.joinpath(".env").write_text(
        "\n".join(f"{name}={value}" for name, value in settings)
    )


def _write_account_config(output_dir: Path) -> Path:
    """Write a functional account config for the backend."""
    path = output_dir.joinpath("functionalAccounts.json")
    path.write_text(assets.functional_accounts())
    return path


def _write_keycloak_imports(output_dir: Path) -> Path:
    """Write Keycloak import data."""
    path = output_dir.joinpath("keycloak-import")
    path.mkdir(exist_ok=True)
    path.joinpath("keycloak-import.json").write_text(assets.keycloak_imports())
    return path


def _write_ssh_pubkeys(output_dir: Path) -> Path:
    # This directory must contain _only_ public keys.
    pubkey_dir = output_dir / "pubkeys"
    pubkey_dir.mkdir(exist_ok=True)
    pubkey_dir.chmod(0o755)  # Required by OpenSSH

    key_file = pubkey_dir / "scitacean_test_key.pub"
    key_file.write_text(assets.ssh_public_key())
    key_file.chmod(0o644)  # Required by OpenSSH
    return pubkey_dir


def _write_sftp_data(output_dir: Path) -> Path:
    data_dir = output_dir / SFTP_DATA_DIR_NAME
    data_dir.mkdir(parents=True, exist_ok=True)
    # Make world-writable so that the docker user has write access regardless of whether
    # its UID matches the host UID.
    data_dir.chmod(0o777)

    seed_dir = data_dir / "seed"
    seed_dir.mkdir(exist_ok=True)

    for name, content in assets.sftp_seed_files():
        seed_dir.joinpath(name).write_text(content)

    return data_dir


def _write_ssh_dockerfile(output_dir: Path):
    output_dir.joinpath("Dockerfile-sftp-server").write_text(assets.ssh_dockerfile())
