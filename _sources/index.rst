.. image:: _static/logo.svg
   :class: only-light
   :alt: Scitacean
   :width: 25%

.. image:: _static/logo-dark.svg
   :class: only-dark
   :alt: Scitacean
   :width: 25%

.. raw:: html

   <style>
    .transparent {display: none; visibility: hidden;}
    .transparent + a.headerlink {display: none; visibility: hidden;}
   </style>

.. role:: transparent

:transparent:`Scitacean`
========================

Scitacean is a high level Python package for downloading and uploading datasets from and to `SciCat <https://scicatproject.github.io/>`_.

To get started, read the `User Guide <./user-guide/index.rst>`_.

Why Scitacean?
--------------

Scitacean abstracts away the SciCat HTTP API and makes it usable via a small number of Python functions.
However, it is not the only package that does so.
In particular `Pyscicat <https://scicatproject.github.io/pyscicat/>`_ has a similar but lower level abstraction.
Compared to Pyscicat, Scitacean offers:

- An easier to use and harder to misuse interface.
- Combined handling of metadata and files.
- Automated handling of a number of fields and some database details like data blocks.
- Basic validation of metadata.
- File upload and download utilities.

While Scitacean provides access to a lower level interface similar to Pyscicat, it only supports a small subset of the SciCat API.
Consider using Pyscicat if you need to access, e.g. sample metadata, proposals, job information, etc.

.. toctree::
   :hidden:

   user-guide/index
   reference/index
   developer/index
