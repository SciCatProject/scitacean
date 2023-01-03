# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 SciCat Project (https://github.com/SciCatProject/scitacean)

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union


def make_file(
    fs, path=Union[str, Path], contents: Optional[bytes] = None
) -> Dict[str, Any]:
    if contents is None:
        contents = b"a bunch of file contents" * len(str(path))
    path = Path(path)

    checksum = hashlib.new("md5")
    checksum.update(contents)
    checksum = checksum.hexdigest()

    fs.create_file(path, contents=contents)
    # Not exact but should at least be precise to the second
    # and avoids potential difficulties of querying the file system.
    creation_time = datetime.now().astimezone(timezone.utc)

    return dict(
        path=path, creation_time=creation_time, checksum=checksum, size=len(contents)
    )
