# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)

from pathlib import Path

import pytest

from .._internal.file_counter import FileCounter, NullCounter


def using_xdist(request: pytest.FixtureRequest) -> bool:
    """Return True if we are running with one or more pytest-xdist workers."""
    try:
        is_master = request.getfixturevalue("worker_id") == "master"
        return not is_master
    except pytest.FixtureLookupError:
        return False


def root_tmp_dir(
    request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory
) -> Path:
    """Get the temp directory for this invocation of pytest shared by all workers."""
    if using_xdist(request):
        return tmp_path_factory.getbasetemp().parent
    return tmp_path_factory.getbasetemp()


def init_pytest_work_dir(
    request: pytest.FixtureRequest,
    tmp_path_factory: pytest.TempPathFactory,
    name: str | None,
) -> tuple[Path, FileCounter | NullCounter]:
    """Create a working directory and initialize an atomic counter and lock for it."""
    return init_work_dir(request, root_tmp_dir(request, tmp_path_factory), name)


def init_work_dir(
    request: pytest.FixtureRequest, base_path: Path, name: str | None
) -> tuple[Path, FileCounter | NullCounter]:
    """Create a working directory and initialize an atomic counter and lock for it."""
    target_dir = base_path / name if name else base_path
    target_dir.mkdir(exist_ok=True)

    counter: FileCounter | NullCounter
    if using_xdist(request):
        counter = FileCounter(target_dir / "counter")
    else:
        counter = NullCounter()

    return target_dir, counter
