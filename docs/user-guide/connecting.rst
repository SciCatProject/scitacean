.. _connecting-to-scicat-and-file-servers:

Connecting to SciCat and file servers
=====================================

.. py:currentmodule:: scitacean

This page describes how to connect to a SciCat instance and associated file server.
(A *SciCat instance* is a specific SciCat catalogue such as `scicat.ess.eu <https://scicat.ess.eu>`_ or `discovery.psi.ch <https://discovery.psi.ch>`_.)

In Scitacean, you connect to SciCat by creating a :class:`Client` object.
And you create a Client object by calling one of its named constructors.
You need to answer three questions to choose a constructor and its arguments:

- Which instance do you want to connect to?
- How do you want to authenticate with SciCat?
- How do you want to transfer files? (Do you want to transfer files at all?)

Each question is explored in a separate section below.


.. _choosing-a-scicat-instance:

Choosing a SciCat instance
--------------------------

This section uses the :meth:`Client.from_token` constructor.
But everything here applies to all constructors.

.. _builtin-profiles:

Builtin profiles
~~~~~~~~~~~~~~~~

Scitacean provides configurations ('profiles') for some SciCat instances out of the box.
If you want to use one of them, simply specify its name as a string when constructing a client.
For example, connect to the production instance at ESS:

.. testcode::

    from scitacean import Client

    client = Client.from_token(
        "ess",
        token="<insert token>",
    )

Here is a list of the available profiles:

.. testcode::
    :hide:

    from scitacean import builtin_profiles
    print("\n".join(f"- {name!r}" for name in sorted(builtin_profiles())))

.. testoutput::

    - 'ess'
    - 'staging.ess'

If you want to add a new profile, please `open a new issue <https://github.com/SciCatProject/scitacean/issues/new>`_ or add it yourself and open a PR.

Profiles can define more than just the SciCat instance.
For example, they can define a :ref:`file transfer <connecting-file-transfer>`.

URL
~~~

You can select a SciCat instance by specifying its URL directly.
This is particularly useful when there is no builtin profile available (see above section).

For example, connect to the production instance at ESS: (Note the ``url`` keyword argument)

.. testcode::

    from scitacean import Client

    client = Client.from_token(
        url="https://scicat.ess.eu/api",
        token="<insert token>",
    )

.. admonition:: API URL

    You need to use the *API URL*, not the *frontend URL*.
    The frontend URL is what you use in a browser to visit SciCat.
    The API URL is usually formed by appending ``/api``, ``/api/v3``, or ``/api/v4`` to the frontend URL.
    In the example above, ``https://scicat.ess.eu`` is the frontend URL.

    Scitacean automatically appends the ``/api/v3`` or ``/api/v4`` suffix if the URL you specify does not have it.
    This works for most SciCat instances.
    But if your SciCat is configured differently, you need to add the suffix yourself.

.. admonition:: API Version
    :class: hint

    The API URL encodes a version (currently ``v3`` or ``v4``).
    Scitacean uses both versions for different operations and selects the correct one automatically.
    It makes no difference whether you specify the version or which version you specify.

Custom profile
~~~~~~~~~~~~~~

It is possible to define custom profiles.
This is required for some more advanced use cases like using :ref:`single sign-on <connecting-sso>` as described below.
In the most basic case, simply specify an API URL and :ref:`file transfer <connecting-file-transfer>`:

.. testcode::

    from scitacean import Client, Profile

    my_profile = Profile(
        url="https://scicat.ess.eu/api",
        file_transfer=None,  # See below in 'File transfer' section
    )
    client = Client.from_token(
        my_profile,
        token="<insert token>",
    )

:class:`Profile` has more attributes than what is shown here.
The `Custom profiles <./custom-profiles.rst>`_ page explains those attributes.


Authenticating with SciCat
--------------------------

When constructing a :class:`Client`, you need to specify how to authenticate with SciCat.
You do this by using one of its named constructors.
Each one is explained in its own subsection below.

All examples here select a SciCat instance via a profile.
You can use any method described in :ref:`choosing-a-scicat-instance` instead, with the exception of single sign-on.

Every connection with SciCat needs a token.
(In this context, a 'token' identifies you to SciCat so it knowns what you can and cannot do.)
The different client constructors ultimately represent different ways of getting a token.

.. admonition:: Note

    Tokens have a limited lifetime that can be as short as one hour.
    Scitacean will raise a :class:`RuntimeError` if you try to use an expired token.
    Create a new client when this happens.

Token
~~~~~

.. caution::

    SciCat tokens are **secrets**.
    Never share your token with anyone.
    And do not upload notebooks or scripts that contain a token.

    Tip: Use a tool like `Betterleaks <https://betterleaks.com/>`_ to catch secrets before it is too late.
    You can use it as a pre-commit hook to make sure you never commit secrets to a git repository.

You can get a token manually and call :meth:`Client.from_token`.
To get a token:

.. |copy-icon-light| image:: ../_static/icons/copy-light.svg
   :class: only-light inline-icon no-scaled-link
   :width: 16px
.. |copy-icon-dark| image:: ../_static/icons/copy-dark.svg
   :class: only-dark inline-icon no-scaled-link
   :width: 16px

1. Open SciCat in your browser.
2. Log in
3. Click on the profile icon in the top-right and select 'Settings'.
4. Click the copy button |copy-icon-light|\ |copy-icon-dark| next to the 'SciCat Token' field.
5. Paste the token into your code or environment.

.. testcode::

    from scitacean import Client

    client = Client.from_token(
        "ess",
        token="my-token",
    )

Remember to keep your token secret.
To this end, you may want to avoid inserting it directly into Python code.
Instead, you can use a secret storage through, e.g., `keyring <https://github.com/jaraco/keyring>`_ or use an environment variable.

Password
~~~~~~~~

.. caution::

    This method is more risky than using a token because passwords are valid for much longer than tokens.
    So make extra sure not to upload notebooks or scripts where you hard coded a password!

You can authenticate with your username and password by calling :meth:`Client.from_credentials`:

.. code-block::

    from scitacean import Client

    client = Client.from_credentials(
        "ess",
        username="my-user",
        password="my-password",
    )

Unauthenticated
~~~~~~~~~~~~~~~

You can use Scitacean without authenticating with SciCat.
This way, you can only download public data.
Create a client without authentication by calling :meth:`Client.without_login`:

.. testcode::

    from scitacean import Client

    client = Client.without_login("ess")

.. _connecting-sso:

Single sign-on
~~~~~~~~~~~~~~

For some SciCat instances, you can authenticate using single sign-on (SSO).
This requires a :class:`Profile`, either builtin or custom that defines how to connect to the identity provider.
See the documentation on :ref:`building custom profiles <custom-profiles-single-sign-on>` if you want to configure your own profile.
And see :ref:`oauth-configuration` if you want to configure your SciCat instance and identity provider.

Call :meth:`Client.login` to create a client that uses SSO:

.. code-block::

    from scitacean import Client

    client = Client.login("ess")

This opens the identity provider's login page for the selected SciCat instance in your web browser.
You need to log in there and, afterwards, you can use the client to access SciCat.
If you already logged in with the same identity provider in your browser before, the client may be authenticated automatically.
This may still open a browser window and close it immediately.

Note that this method is interactive and therefore not suitable for automated scripts or notebooks that are run without user interaction.

Login flows
^^^^^^^^^^^

There are two different possible login flows.
Choosing one depends on context.

- **Normal** flow: This is the more convenient flow. But it requires that Python is running on the same machine as your browser. This is the case when you use your laptop or workstation or in a virtual desktop. But it is not the case with a remote JupyterLab / JupyterHub where Python runs on a virtual machine and the browser on your own laptop / workstation.
- **Device** flow: This flow requires an additional approval step that needs to be repeated every time you call ``Client.login``. But it works even when the normal flow does not.

You can select a flow by passing the ``flow`` argument to :meth:`Client.login`:

.. code-block::

    from scitacean import Client

    client = Client.login("ess", flow="normal")
    # or
    client = Client.login("ess", flow="device")

By default, ``login`` uses the normal flow unless it is overridden by an environment variable.

You can set the environment variable ``SCITACEAN_LOGIN_FLOW`` to either ``normal`` or ``device`` to select a flow.
This sets the default login flow.
It can be overridden by passing the ``flow`` argument to :meth:`Client.login`.
Some systems may set this variable automatically for you.


.. _connecting-file-transfer:

File transfer
-------------

Everything discussed above describes how to connect to SciCat itself.
You can use the above clients with SciCat as long as you don't need to transfer data files.
Files are stored outside of SciCat on a file server (often called 'remote system' in Scitacean).
File servers are usually not connected directly to SciCat and require a separate configuration.
Scitacean handles this via :class:`typing.FileTransfer` objects.
See `here <../reference/index.rst#file-transfer>`_ of a list of builtin file transfers

Set a transfer in the client constructor: (The examples here use :meth:`Client.from_token` but the same applies to all constructors.)

.. testcode::

    from scitacean import Client

    client = Client.from_token(
        "ess",
        token="<insert token>",
        file_transfer=...,   # set file transfer here
    )

When using a :class:`Profile` to :ref:`choose a SciCat instance <choosing-a-scicat-instance>`, a file transfer may be preconfigured.
You can still override that by passing a different file transfer to the client constructor.


SSH / SFTP
~~~~~~~~~~

This is currently the only builtin file transfer that can send files to / from a remote server.

The :class:`transfer.sftp.SFTPFileTransfer` sends files via SFTP (SSH File Transfer Protocol).
In its most basic form, you can use it like so:

.. testcode::

    from scitacean import Client
    from scitacean.transfer.sftp import SFTPFileTransfer

    transfer = SFTPFileTransfer(host="sftp.esss.dk")
    client = Client.from_token(
        "ess",
        token="<insert token>",
        file_transfer=transfer,
    )

This connects to the file server at ``sftp.esss.dk`` and attempts to connect in the same way as OpenSSH would.
That is, it will use your SSH agent or any configured SSH key.

.. admonition:: Note

    If you have never connected to this specific SSH server before, you will likely get an error about an **unknown host key**.
    In this case, connect to the server once using the ``ssh`` command line tool or a similar tool to accept the host key.
    Afterwards, the ``SFTPFileTransfer`` should connect properly.

    See also :ref:`custom-sftp-connection` if you need something more advanced.

If the default method fails, try one of the following.

.. _set-ssh-key-file:

Set SSH key file
^^^^^^^^^^^^^^^^

You can specify a key file to use for authentication by passing the ``key_filename`` argument to :class:`SFTPFileTransfer`.
You also need to set a username if the remote username is different from your local username.
Note that the SFTP username may be different from your SciCat username.

.. testcode::

    from scitacean import Client
    from scitacean.transfer.sftp import SFTPFileTransfer

    transfer = SFTPFileTransfer(
        host="sftp.esss.dk",
        username="my-username",
        key_filename="/home/my-user/.ssh/scicat-key"
    )
    client = Client.from_token(
        "ess",
        token="<insert token>",
        file_transfer=transfer,
    )

Username + password
^^^^^^^^^^^^^^^^^^^

.. caution::

    Make extra sure not to upload notebooks or scripts where you hard coded a password!

You can specify a username and password to use for authentication by passing the ``username`` and ``password`` arguments to :class:`SFTPFileTransfer`:

.. testcode::

    from scitacean import Client
    from scitacean.transfer.sftp import SFTPFileTransfer

    transfer = SFTPFileTransfer(
        host="sftp.esss.dk",
        username="my-username",
        password="my-password",
    )
    client = Client.from_token(
        "ess",
        token="<insert token>",
        file_transfer=transfer,
    )

Note that the SFTP username and password may be different from your SciCat username and password.

.. _custom-sftp-connection:

Custom SFTP connection
^^^^^^^^^^^^^^^^^^^^^^

Sometimes, the methods described above do not work for you. In this case, you can define your own ``connect`` function. It operates with the underlying `paramiko.SSHClient <https://docs.paramiko.org/en/latest/api/client.html>`_ and returns a `paramiko.SFTPClient <https://docs.paramiko.org/en/latest/api/sftp.html#paramiko.sftp_client.SFTPClient>`_.

As an example, the following is equivalent to :ref:`setting an SSH key file <set-ssh-key-file>`:

.. code-block::

    from paramiko import SFTPClient, SSHClient
    from scitacean.transfer.sftp import SFTPFileTransfer

    def connect(host: str, port: int) -> SFTPClient:
        ssh_client = SSHClient()

        # Load known host keys from the system (e.g., /home/my-user/.ssh/known_hosts).
        # Or use a custom `MissingHostKeyPolicy`.
        ssh_client.load_system_host_keys()

        # Call `connect` with any custom arguments here:
        ssh_client.connect(
            hostname=host,
            port=port,
            username="my-username",
            key_filename="/home/my-user/.ssh/scicat-key",
        )

        return ssh_client.open_sftp()

    transfer = SFTPFileTransfer(
        host="sftp.esss.dk",
        connect=connect,
    )



Copy & link
~~~~~~~~~~~

If you are running Scitacean on the same machine as the file server, you can simply copy data files or create symlinks.
This is faster and requires less setup than using SFTP.

Scitacean provides

- :class:`transfer.copy.CopyFileTransfer` for copying files
- :class:`transfer.link.LinkFileTransfer` for creating symlinks

``LinkFileTransfer`` is the fastest and does not duplicate potentially large files.
But it can only download files, not upload because uploading should always produce a file that SciCat can take ownership of.
For this purpose, you can use ``CopyFileTransfer``.

You can use them like so:

.. testcode::

    from scitacean import Client
    from scitacean.transfer.link import LinkFileTransfer

    client = Client.from_token(
        "ess",
        token="<insert token>",
        file_transfer=LinkFileTransfer(),
    )

and

.. testcode::

    from scitacean import Client
    from scitacean.transfer.copy import CopyFileTransfer

    client = Client.from_token(
        "ess",
        token="<insert token>",
        file_transfer=CopyFileTransfer(),
    )

Automatically selected file transfer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`transfer.select.SelectFileTransfer` automatically selects a file transfer from a list.
This is most useful when writing generic code and :ref:`builtin profiles <builtin-profiles>` use this.

``SelectFileTransfer`` tries all candidate transfers in the order they are given until it finds one that can handle the transfer or runs out of options.

For example, the following makes symlinks if possible, otherwise, it copies files, and if that fails, it uses SFTP:
This means that on a system that has direct access to the files, it will use symlinks for downloads and copies for uploads.
On other systems, it will always use SFTP.

.. testcode::

    from scitacean.transfer.copy import CopyFileTransfer
    from scitacean.transfer.link import LinkFileTransfer
    from scitacean.transfer.select import SelectFileTransfer
    from scitacean.transfer.sftp import SFTPFileTransfer
    from scitacean import Client

    copy_transfer = CopyFileTransfer()
    link_transfer = LinkFileTransfer()
    sftp_transfer = SFTPFileTransfer(host="sftp.esss.dk")
    transfer = SelectFileTransfer([link_transfer, copy_transfer, sftp_transfer])
    client = Client.from_token(
        "ess",
        token="<insert-token>",
        file_transfer=transfer,
    )

Custom file transfer
~~~~~~~~~~~~~~~~~~~~

If none of the builtin file transfers work for you, you can create your own by implementing the :class:`typing.FileTransfer`, :class:`typing.DownloadConnection`, and :class:`typing.UploadConnection` protocols:

.. testcode::

    from collections.abc import Generator
    from contextlib import contextmanager
    from pathlib import Path

    from scitacean import Dataset, File, RemotePath


    class MyDownloadConnection:
        def download_files(self, *, remote: list[RemotePath], local: list[Path]) -> None:
            """Download files from remote to local."""


    class MyUploadConnection:
        def __init__(self, *, source_folder: RemotePath) -> None:
            self._source_folder = source_folder

        def upload_files(self, *files: File) -> list[File]:
            """Upload files to the remote folder."""
            # Upload to `self._source_folder`.
            # Return the uploaded files with their remote paths set.

        def revert_upload(self, *files: File) -> None:
            """Remove uploaded files from the remote folder."""


    class MyFileTransfer:
        @contextmanager
        def connect_for_download(
            self, dataset: Dataset, representative_file_path: RemotePath
        ) -> Generator[MyDownloadConnection, None, None]:
            """Create a download connection."""
            # Check if `representative_file_path` is accessible
            # and raise `FileNotAccessibleError` otherwise.
            yield MyDownloadConnection()

        @contextmanager
        def connect_for_upload(
            self, dataset: Dataset, representative_file_path: RemotePath
        ) -> Generator[MyUploadConnection, None, None]:
            """Create an upload connection."""
            # Check if `representative_file_path` is accessible
            # and raise `FileNotAccessibleError` otherwise.
            yield MyUploadConnection(source_folder=dataset.source_folder)

The mechanism with ``representative_file_path`` exists so that :class:`transfer.select.SelectFileTransfer` can select a transfer without having to start any actual file transfers.
