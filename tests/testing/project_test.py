# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 SciCat Project (https://github.com/SciCatProject/scitacean)

from pathlib import Path
from unittest.mock import Mock

import pytest

from scitacean.testing import _testing_project
from scitacean.testing._services import config, docker


def test_teardown_does_not_invoke_docker_without_started_services(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = _testing_project.TestingProject.new(tmp_path, project_name="test")
    docker_down = Mock()
    monkeypatch.setattr(docker, "docker_compose_down", docker_down)

    project.teardown()

    docker_down.assert_not_called()


def test_service_configuration_retries_after_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = _testing_project.TestingProject.new(tmp_path, project_name="test")
    calls = 0

    def configure(path: Path, *, docker_filename: str, **_kwargs: object) -> None:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("configuration failed")
        path.joinpath(docker_filename).touch()

    monkeypatch.setattr(config, "configure_services", configure)

    with pytest.raises(RuntimeError, match="configuration failed"):
        project._configure_services()

    assert project._configure_services().is_file()
    assert calls == 2


def test_teardown_stops_services_started_by_project(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = _testing_project.TestingProject.new(tmp_path, project_name="test")
    compose_down = Mock()

    def configure(path: Path, *, docker_filename: str, **_kwargs: object) -> None:
        path.joinpath(docker_filename).touch()

    monkeypatch.setattr(config, "configure_services", configure)
    monkeypatch.setattr(
        docker, "docker_compose_service_status", Mock(return_value="missing")
    )
    monkeypatch.setattr(docker, "docker_compose_up", Mock())
    monkeypatch.setattr(docker, "docker_compose_down", compose_down)

    project.ensure_running("sftp")
    project.teardown()

    compose_down.assert_called_once()
    assert not project.path.joinpath(".docker-compose-started").exists()


def test_teardown_cleans_up_after_service_start_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = _testing_project.TestingProject.new(tmp_path, project_name="test")
    compose_down = Mock()

    def configure(path: Path, *, docker_filename: str, **_kwargs: object) -> None:
        path.joinpath(docker_filename).touch()

    monkeypatch.setattr(config, "configure_services", configure)
    monkeypatch.setattr(
        docker, "docker_compose_service_status", Mock(return_value="missing")
    )
    monkeypatch.setattr(
        docker, "docker_compose_up", Mock(side_effect=RuntimeError("startup failed"))
    )
    monkeypatch.setattr(docker, "docker_compose_down", compose_down)

    with pytest.raises(RuntimeError, match="startup failed"):
        project.ensure_running("sftp")

    project.teardown()

    compose_down.assert_called_once()
