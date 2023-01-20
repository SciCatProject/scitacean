.. _release-notes:

.. currentmodule:: scitacean

Release notes
=============


.. Template, copy this to create a new section after a release:

   vYY.0M.MICRO (Unreleased)
   -------------------------

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
* ``ESSTestFileTransfer`` was renamed to :class:`transfer.ssh.SSHFileTransfer`.

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
