.. _release-notes:

Release Notes
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


vYY.0M.MICRO (Unreleased)
-------------------------

Features
~~~~~~~~

* Added :meth:`Dataset.fields` to inspect dataset fields.

Breaking changes
~~~~~~~~~~~~~~~~

* A number of attributes of Dataset are now read only.
* :meth:`Dataset.new` was removed, use the regular ``__init__`` method instead.

Bugfixes
~~~~~~~~

* It is not possible to log in with username+password as a non-functional user.

Documentation
~~~~~~~~~~~~~

Stability, Maintainability, and Testing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Removed dependency on PySciCat by reimplementing the relevant parts.
* Added tests to verify SciCat models and assumptions on them.


v22.11.0 (2022-11-16)
---------------------

Initial release
