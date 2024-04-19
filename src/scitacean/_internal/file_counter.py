# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

import filelock


class FileCounter:
    """Atomic counter based on a file.

    Maintains a file with the count and a separate lock file to
    synchronize access to the counter.
    This is useful in contexts where shared variables between threads or
    processes are not (easily) accessible.
    For instance, when using ``pytest-xdist``, this counter can be used to synchronize
    access to some shared resource between workers.

    The ``increment`` and ``decrement`` functions are intended
    to be used as context managers.
    This allows holding the lock past the increment/decrement and
    synchronizing further operations.
    For example:

    .. code-block:: python

        counter = FileCounter(Path("counter"))
        with counter.increment() as count:
            # do some work that requires the lock
        # lock gets released here
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = filelock.FileLock(str(self._path) + ".lock")

    @contextmanager
    def increment(self) -> Generator[int, None, None]:
        with self._lock:
            if self._path.exists():
                count = self._read() + 1
            else:
                count = 1
            self._write(count)
            yield count

    @contextmanager
    def decrement(self) -> Generator[int, None, None]:
        with self._lock:
            count = self._read() - 1
            if count < 0:
                raise RuntimeError(
                    f"Broken file counter, got a file with a count of {count-1}."
                )
            if count == 0:
                self._path.unlink()
            else:
                self._write(count)
            yield count

    def _read(self) -> int:
        with open(self._path) as f:
            c = int(f.read())
            return c

    def _write(self, count: int) -> None:
        with open(self._path, "w") as f:
            f.write(str(count))


class NullCounter:
    """Similar to FileCounter but does not use files, a lock, or count.

    ``increment`` always returns 1 and ``decrement`` always returns 0.
    There is no lock.

    This class can be used similarly to :func:`contextlib.null_context`.
    That is, it allows for transparent handling of conditional counting and locking.
    For example

    .. code-block:: python

        def make_counter():
            if some_condition:
                return FileCounter(path)
            return NullCounter()

        counter = make_counter()
        with counter.increment() as count:
            # Do some work that requires the lock if some_condition is true.
    """

    @contextmanager
    def increment(self) -> Generator[int, None, None]:
        yield 1

    @contextmanager
    def decrement(self) -> Generator[int, None, None]:
        yield 0
