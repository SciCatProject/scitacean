# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)
import importlib.resources
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple, Union

import paramiko
import yaml


@dataclass
class SFTPUser:
    username: str
    password: str


@dataclass
class SFTPAccess:
    host: str
    port: int
    user: SFTPUser


def _read_resource_text(filename: str) -> str:
    if hasattr(importlib.resources, "files"):
        # Use new API added in Python 3.9
        return (
            importlib.resources.files("scitacean.testing.sftp")
            .joinpath(filename)
            .read_text()
        )
    # Old API, deprecated as of Python 3.11
    return importlib.resources.read_text("scitacean.testing.sftp", filename)


def _read_resource_yaml(filename: str) -> Any:
    return yaml.safe_load(_read_resource_text(filename))


@lru_cache(maxsize=1)
def _docker_compose_file() -> Dict[str, Any]:
    return _read_resource_yaml(
        "docker-compose-sftp-server.yaml"
    )  # type: ignore[no-any-return]


@lru_cache(maxsize=1)
def _docker_file() -> str:
    return _read_resource_text("Dockerfile-sftp-server")


def _seed_files() -> Iterable[Tuple[str, str]]:
    if hasattr(importlib.resources, "files"):
        # Use new API added in Python 3.9
        yield from (
            (file.name, file.read_text())
            for file in importlib.resources.files("scitacean.testing.sftp")
            .joinpath("sftp_server_seed")
            .iterdir()
        )
    else:
        # Old API, deprecated as of Python 3.11
        with importlib.resources.path(
            "scitacean.testing.sftp", "sftp_server_seed"
        ) as seed_dir:
            for path in seed_dir.iterdir():
                yield path.name, path.read_text()


def local_access() -> SFTPAccess:
    config = _docker_compose_file()
    service = config["services"]["scitacean-test-sftp-server"]
    env = {k: v for k, v in map(lambda s: s.split("="), service["environment"])}
    return SFTPAccess(
        host="localhost",
        port=service["ports"][0].split(":")[0],
        user=SFTPUser(
            username=env["USER_NAME"],
            password=env["USER_PASSWORD"],
        ),
    )


def _copy_seed(target_seed_dir: Path) -> None:
    for name, content in _seed_files():
        target_seed_dir.joinpath(name).write_text(content)


def configure(target_dir: Union[Path, str]) -> Path:
    """Generate a config file for docker compose and copy seed data."""
    target_dir = Path(target_dir)
    target_seed_dir = target_dir / "data" / "seed"
    target_seed_dir.mkdir(parents=True)
    _copy_seed(target_seed_dir)

    config_target = target_dir / "docker-compose.yaml"
    config_target.write_text(yaml.dump(_docker_compose_file()))
    target_dir.joinpath("Dockerfile-sftp-server").write_text(_docker_file())

    target_dir.joinpath(".env").write_text(
        f"""DATA_DIR={target_dir / 'data'}
SEED_DIR={target_seed_dir}"""
    )

    return config_target


def can_connect(sftp_access: SFTPAccess) -> bool:
    try:
        _make_client(sftp_access)
    except paramiko.SSHException:
        return False
    return True


def wait_until_sftp_server_is_live(
    sftp_access: SFTPAccess, max_time: float, n_tries: int
) -> None:
    # The container takes a while to be fully live.
    for _ in range(n_tries):
        if can_connect(sftp_access):
            return
        time.sleep(max_time / n_tries)
    if not can_connect(sftp_access):
        raise RuntimeError("Cannot connect to SFTP server")


def cleanup_data_dir(
    sftp_access: SFTPAccess, sftp_connect_with_username_password: Any
) -> None:
    # Delete all directories created by tests.
    # These are owned by root on the host and cannot be deleted by Python's tempfile.
    connection = sftp_connect_with_username_password(
        host=sftp_access.host, port=sftp_access.port
    )
    connection.run(
        "find /data -not -path '/data' -not -path '/data/seed' | xargs rm -rf",
        hide=True,
        in_stream=False,
    )


def _make_client(sftp_access: SFTPAccess) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(IgnorePolicy())
    client.connect(
        hostname=sftp_access.host,
        port=sftp_access.port,
        username=sftp_access.user.username,
        password=sftp_access.user.password,
        allow_agent=False,
        look_for_keys=False,
    )
    return client


# Every time we create a container, it gets a new host key.
# So simply accept any host keys.
class IgnorePolicy(paramiko.MissingHostKeyPolicy):
    def missing_host_key(self, client: Any, hostname: Any, key: Any) -> None:
        return
