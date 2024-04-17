Testing
=======

The main purpose of Scitacean is communication with a SciCat backend and a file server.
Those are difficult and expensive to test in a live environment because

- They are susceptible to failing because of internet problems.
- They can break if the servers state changes, that is, the tests depend on a particular external state which is out of our control.
- Upload tests would pollute the server with useless data.
- They are slow.

In order to avoid these problems, most of Scitacean is tested against a fake client (:class:`scitacean.testing.client.FakeClient`) and fake file transfer handler (:class:`scitacean.testing.transfer.FakeFileTransfer`).
These look and behave mostly like the real deals but never open any network connections.
Instead, they record "uploaded" datasets and files and provide them for "download".
This way, tests can run quickly and in a non-flaky manner.

However, there are two problems.
For one, the fakes do not have perfect fidelity, that is, some edge cases do not work.
And the visible behavior slightly deviates from a real client, e.g. the content of error messages or how datasets are modified during upload.
In addition, the fakes are relatively complex and may diverge from the real implementations.

To mitigate these problems, the fake client is tested alongside a real client.
But to (mostly) avoid the downsides stated in the beginning, the real client is connected to a local SciCat server.
See the `src/scitacean/backend <https://github.com/SciCatProject/scitacean/tree/main/src/scitacean/testing/backend>`_ folder and `tests/conftest.py <https://github.com/SciCatProject/scitacean/blob/main/tests/conftest.py>`_ file for the concrete setup.
The backend is launched in a docker container with the image of the latest release of the SciCat backend.
Tests in `tests/client <https://github.com/SciCatProject/scitacean/tree/main/tests/client>`_ are then run with both the fake and the real client to ensure that both produce the same results.

Use ``--backend-tests`` with ``pytest`` to run these tests.

SFTP file transfer
------------------

Testing :class:`scitacean.transfer.sftp.SFTPFileTransfer` requires an SFTP server.
:mod:`scitacean.testing.sftp` contains helpers for managing one via Docker.
Tests can use it by depending on the ``sftp_fileserver`` fixture.
See the `documentation <https://scicatproject.github.io/scitacean/user-guide/testing.html#Local-SFTP-fileserver>`_ for how it works.

Note that those tests may leave a small directory behind.
This is an issue with file ownership and permissions caused by making the Docker volumes writable.
It should not be a problem in practice as those files will only be in temporary directories which should get cleaned up at reboot.

Use ``--sftp-tests`` with ``pytest`` to run these tests.
