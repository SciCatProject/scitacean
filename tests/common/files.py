# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 SciCat Project (https://github.com/SciCatProject/scitacean)

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pyfakefs.fake_filesystem import FakeFilesystem


def make_file(
    fs: FakeFilesystem, path: str | Path, contents: bytes | None = None
) -> dict[str, Any]:
    if contents is None:
        contents = b"a bunch of file contents" * len(str(path))
    path = Path(path)

    checksum = hashlib.new("md5")
    checksum.update(contents)
    checksum_digest = checksum.hexdigest()

    fs.create_file(path, contents=contents)
    # Not exact but should at least be precise to the second
    # and avoids potential difficulties of querying the file system.
    creation_time = datetime.now().astimezone(timezone.utc)

    return {
        "path": path,
        "creation_time": creation_time,
        "checksum": checksum_digest,
        "size": len(contents),
    }
