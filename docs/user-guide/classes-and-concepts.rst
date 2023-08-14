Classes and concepts
====================

Scitacean uses a number of different classes to store metadata and interact with the data catalogue.
This page gives an overview of the most important ones.
See the `API reference <../reference/index.rst>`_ for a complete list.

Encoding metadata
-----------------

Dataset
~~~~~~~

:class:`scitacean.Dataset` is the main class for encoding metadata.
Each instance represents a single SciCat dataset.
But unlike in SciCat itself, it also contains links to files and their metadata via :ref:`files` objects.

``Dataset`` contains all fields of both raw and derived datasets.
Some fields are managed automatically (e.g. ``size``) and some are read-only as they are not allowed to be set during uploads (e.g. ``created_by``).
Some fields hold sub models like :class:`scitacean.model.Relationship`; those models are always :ref:`user-models`.
Field names use Scitacean's and thereby Python's naming convention, that is snake_case as opposed to camelCase as used by SciCat.

Datablocks
~~~~~~~~~~

SciCat separates general metadata and file-specific metadata into 'datasets' and 'datablocks', respectively.
In Scitacean, those are large unified into :class:`scitacean.Dataset` and for a user, it is usually possible to ignore datablocks entirely.
Datablocks (for archived files) and Original Datablocks (for directly accessible files) are managed automatically by the high-level interface.
But :class:`scitacean.Dataset` and :ref:`scicat-client` support handling them manually if need be.

.. _files:

Files
~~~~~

:class:`scitacean.File` links to a single file that may be located on the remote fileserver or the local filesystem or both.
It also encodes a number of metadata fields as specified by :class:`scitacean.model.DownloadDataFile` and :class:`scitacean.model.UploadDataFile`.
See the class documentation for details on how local vs. remote files are handled.

Models
~~~~~~

Models are Python representations of the various objects in a SciCat database.
See :mod:`scitacean.model` for a list.

.. _user-models:

User models
^^^^^^^^^^^

User models are dataclasses that are exposed as part of the high-level interface of Scitacean.
They have writable fields that can be set in both uploads and downloads as well as read-only fields that may only be set in downloads.
Field names use Scitacean's and thereby Python's convention, that is snake_case as opposed to camelCase as used by SciCat.

``Dataset``, ``(Orig)Datablock``, and ``File`` don't have separate user models.
Instead they are represented by the specialized classes described above.

.. _download-models:

Download models
^^^^^^^^^^^^^^^

Download models are `Pydantic <https://docs.pydantic.dev/latest/>`_ models that encode the data received from SciCat in downloads.
They may contain fields that correspond to read-only fields in user models and cannot be set in uploads.
Field names use SciCat's convention, that is camelCase.

Download models can be converted to user models by using the appropriate user model's ``from_download_model`` class method.
In the case of Dataset, :meth:`scitacean.Dataset.from_download_models` requires models for a dataset and (orig) datablocks.

.. _upload-models:

Upload models
^^^^^^^^^^^^^

Upload models are `Pydantic <https://docs.pydantic.dev/latest/>`_ models that encode the data sent to SciCat in uploads.
Field names use SciCat's convention, that is camelCase.

Upload models can be constructed by the corresponding user models using their ``to_upload_model`` method.

For :class:`scitacean.Dataset`, there are two distinct upload models, namely :class:`scitacean.model.UploadRawDataset` and :class:`scitacean.model.UploadDerivedDataset`.
In addition, :class:`scitacean.model.UploadOrigDatablock` and :class:`scitacean.model.UploadDataFile` are needed to fully represent Scitacean's ``Dataset`` objects.

Downloading & uploading (meta) data
-----------------------------------

.. _client:

Client
~~~~~~

:class:`scitacean.Client` is the high-level interface for downloading and uploading datasets from and to SciCat.
It deals directly with :class:`scitacean.Dataset` and :ref:`user-models`.
It also controls the download and upload of files as implemented by :ref:`file-transfers`.

.. _file-transfers:

File transfers
~~~~~~~~~~~~~~

SciCat itself only deals with metadata and files are stored separately.
However, for ease of use, :class:`scitacean.Dataset` and :class:`scitacean.Client` unify handling of metadata and files.
The latter requires `file transfers <../reference/index.rst#file-transfer>`_ to implement concrete download and upload methods.
File transfers should not be used directly but passed as arguments when constructing a ``Client``.

SciCat is deployed in diverse environments and each facility has its own ways of accessing files.
So it is necessary to pick an appropriate one for the concrete SciCat instance in use.
Scitacean cannot guarantee that it can download or upload files for every instance of SciCat.
But it is possible to implement custom file transfers if the bundled ones are not enough.
Each transfer must satisfy the :class:`scitacean.typing.FileTransfer` protocol.

.. _scicat-client:

ScicatClient
~~~~~~~~~~~~

:class:`scitacean.client.ScicatClient` is the low-level interface for downloading and uploading metadata from and to SciCat.
In contrast to :ref:`client`, it deals with :ref:`download-models` and :ref:`upload-models`.
It does not handle files.

It should almost never be necessary to use ``ScicatClient`` directly.
If you find yourself reaching for it because ``Client`` is insufficient, please consider starting a `discussion <https://github.com/SciCatProject/scitacean/discussions>`_ or opening an `issue <https://github.com/SciCatProject/scitacean/issues/new>`_ on GitHub as this likely indicates a missing feature in the high-level client.

There are two notable exceptions to this.
The first is testing with a fake client as described in the `Testing user guide <./testing.ipynb#FakeClient>`_.
The second is needing direct control over data blocks and Scitacean's automated handling doesn't work for you.
The latter is considered an advanced use case and out of scope for Scitacean's high-level interface.
