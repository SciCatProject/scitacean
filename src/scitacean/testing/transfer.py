# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen
from contextlib import contextmanager
from typing import Dict


class FakeDownloadConnection:
    def __init__(self, files: Dict[str, bytes], fs):
        self.files = files
        self.fs = fs

    def download_file(self, *, remote, local):
        self.fs.create_file(local, contents=self.files[remote])


class FakeFileTransfer:
    def __init__(self, files: Dict[str, bytes], fs):
        self.files = files
        self.fs = fs

    @contextmanager
    def connect_for_download(self):
        yield FakeDownloadConnection(self.files, self.fs)

    # TODO upload
