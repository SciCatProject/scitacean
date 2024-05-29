.. _release-notes:

.. currentmodule:: scitacean

Release notes
=============


.. Template, copy this to create a new section after a release:

   vversion
   --------

   Security
   ~~~~~~~~

   Features
   ~~~~~~~~

   Breaking changes
   ~~~~~~~~~~~~~~~~

   Bugfixes
   ~~~~~~~~

   Documentation
   ~~~~~~~~~~~~~

   Deprecations
   ~~~~~~~~~~~~

   Stability, Maintainability, and Testing
   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

vversion
--------

Security
~~~~~~~~

Features
~~~~~~~~

* Added experimental :meth:`client.ScicatClient.query_datasets` for querying datasets by field.

Breaking changes
~~~~~~~~~~~~~~~~

Bugfixes
~~~~~~~~

Documentation
~~~~~~~~~~~~~

Deprecations
~~~~~~~~~~~~

Stability, Maintainability, and Testing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Replaced networking dependency ``requests`` with ``httpx``.

v24.04.0
--------

Features
~~~~~~~~

* Added functions for downloading and uploading samples: :meth:`Client.get_sample`, :meth:`Client.upload_new_sample_now`.
* Added :class:`transfer.link.LinkFileTransfer`.
* :class:`Client` and :class:`ScicatClient` now check whether a token has expired and raise and exception if it has.

Breaking changes
~~~~~~~~~~~~~~~~

* **Dropped support for Python 3.9.**
* **Dropped support for Pydantic v1.**
* Removed deprecated ``transfer.ssh.SSHFileTransfer`` in favor of :class:`transfer.sftp.SFTPFileTransfer`.

Bugfixes
~~~~~~~~

* Fixed testing setup to explicitly define user accounts in the test backend.

v23.10.0
--------

Features
~~~~~~~~

* Python 3.12 is officially supported.
* Added dict-like methods, :meth:`Dataset.keys`, :meth:`Dataset.values` and :meth:`Dataset.items`.
* Added dict-like item setter/getter, :meth:`Dataset.__getitem__` and :meth:`Dataset.__setitem__`.

Breaking changes
~~~~~~~~~~~~~~~~

* **Dropped support for Python 3.8.**
* ``Dataset.type`` is now read only.

Bugfixes
~~~~~~~~

* :class:`scitacean.Client` no longer requires a file transfer during upload if the dataset has no files that need to be uploaded.
* The HTML representation of datasets no longer flags read-only fields with a value as broken.
* Preserve ``meta`` in ``Dataset.replace`` and allow replacing it.
  This also affects ``Dataset.replace_files`` and ``Client.download_files``.

Deprecations
~~~~~~~~~~~~

* Deprecated support for Pydantic v1. It is scheduled for full removal in release 23.12.0.

Stability, Maintainability, and Testing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* The codebase now gets type-checked in CI.

v23.08.0 (2023-08-28)
---------------------

Features
~~~~~~~~

* File downloads now use the checksum algorithm stored in SciCat when possible.
  So it is no longer necessary to specify it by hand in many cases.
* Added ``SFTPFileTransfer`` which is similar to ``SSHFileTransfer`` but relies only on SFTP.
* Added support for attachments.

Bugfixes
~~~~~~~~

* Fields of derived datasets are no longer initialized when downloading raw datasets and vice versa.
* Consistent table styling implemented for Jupyter notebooks in browser and vscode for both dark and light themes.

Deprecations
~~~~~~~~~~~~

* Deprecated ``SSHFileTransfer`` in favor of ``SFTPFileTransfer``.

v23.07.0 (2023-07-07)
---------------------

Features
~~~~~~~~

* Proper support for the new SciCat backend version 4.
* ``scitacean.testing`` now contains tools for managing locally deployed SciCat servers and SSH servers.
* Pydantic version 2 is not supported in addition to version 1.
  Prior versions of Scitacean are incompatible with Pydantic version 2 and users need to ensure to install a compatible version.

Breaking changes
~~~~~~~~~~~~~~~~

* Models have been split into 'download' and 'upload' models for communication with SciCat as well as 'user' models that are exposed in the high level interface.
  For users, this mostly affects tests with ``FakeClient``.

v23.05.0 (2023-05-15)
---------------------

Features
~~~~~~~~

* Early support for the new SciCat backend version 4.
  It is possible to upload and download datasets as before.
  But the new fields added in v4 are not supported yet.

Breaking changes
~~~~~~~~~~~~~~~~

* It is no longer possible to set the dataset PID during upload.

Bugfixes
~~~~~~~~

* Fixed a bug in ``Client.download_files`` where if a file already existed on local, its local path was not set. This was introduced in v23.04.0.

v23.04.0 (2023-04-05)
---------------------

Features
~~~~~~~~

* Better HTML formatting of ESS-style scientific metadata.
* Added the ``force`` argument to :func:`scitacean.Client.download_files`.
* Try the default checksum algorithm if the dataset has no algorithm set to check if a local

Breaking changes
~~~~~~~~~~~~~~~~

* Changed default checksum algorithm from md5 to blake2b.

Bugfixes
~~~~~~~~

* Fixed getting the timezone of a file server on Windows if it is the local timezone.

Stability, Maintainability, and Testing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Added testing for ``SSHFileTransfer``.
* Fixed bug in CI setup that meant that all tests were running on Ubuntu.

v23.03.2 (2023-03-17)
---------------------

Bugfixes
~~~~~~~~

* Remove ``instrument_id`` from ``keep`` argument of :func:`scitacean.Dataset.derive`.
  The instrument id is not allowed in derived datasets.

v23.03.1 (2023-03-16)
---------------------

Security
~~~~~~~~

* Hide user tokens in exceptions raised on HTTP connection failures.

v23.03.0 (2023-03-08)
---------------------

Features
~~~~~~~~

* Added :func:`scitacean.Dataset.as_new` and :func:`scitacean.Dataset.derive`.

Breaking changes
~~~~~~~~~~~~~~~~

* The ``remote_base_path`` argument of ``SSHFileTransfer`` has been replaced with ``source_folder`` which may now contain format specifiers.
* ``Dataset.investigator`` is no longer required to be an email address as this does not match common usage.
* For raw datasets, ``Dataset.investigator`` has been replaced with ``Dataset.principal_investigator`` to match the names in SciCat.

Bugfixes
~~~~~~~~

* Removed ``Dataset.instrument_id`` for derived datasets.

v23.03.1 (2023-03-15)
---------------------

Security
~~~~~~~~

* Remove user token from error messages.

v23.01.1 (2023-01-20)
---------------------

Bugfixes
~~~~~~~~

* Store file creation times as proper datetimes with the timezone of the fileserver.

v23.01.0 (2023-01-10)
---------------------

Features
~~~~~~~~

* Added :meth:`Dataset.fields` to inspect dataset fields.
* Added :meth:`Client.without_login` to create a client without login credentials which can only download public datasets.

Breaking changes
~~~~~~~~~~~~~~~~

* A number of attributes of Dataset are now read only.
* ``Dataset.new`` was removed, use the regular ``__init__`` method instead.
* ``File.provide_locally`` was removed in favor of :meth:`Client.download_files`.
* ``ESSTestFileTransfer`` was renamed to ``transfer.ssh.SSHFileTransfer``.

Bugfixes
~~~~~~~~

* It is not possible to log in with username+password as a non-functional user.
* Added and fixed a number of type annotations.

Documentation
~~~~~~~~~~~~~

* Document fakes for testing.

Stability, Maintainability, and Testing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Removed dependency on PySciCat by reimplementing the relevant parts.
* Added tests to verify SciCat models and assumptions on them.


v22.11.0 (2022-11-16)
---------------------

Initial release
