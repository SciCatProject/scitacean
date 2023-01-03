API Reference
=============

Classes
-------

.. currentmodule:: scitacean

Main Classes
~~~~~~~~~~~~

.. There is special handling of class constructors in the template.

.. autosummary::
   :toctree: ../generated/classes
   :template: scitacean-class-template.rst
   :recursive:

   Client
   Dataset
   File
   pid.PID
   model.DatasetType

File Transfer
~~~~~~~~~~~~~

.. autosummary::
   :toctree: ../generated/classes
   :template: scitacean-class-template.rst
   :recursive:

   transfer.ssh.SSHFileTransfer

Dataclasses
~~~~~~~~~~~

.. currentmodule:: scitacean._dataset_fields

.. autosummary::
   :toctree: ../generated/classes
   :template: scitacean-dataclass-template.rst
   :recursive:

   DatasetFields

Models
~~~~~~

.. currentmodule:: scitacean

Pydantic models for communication with a SciCat server.

.. autosummary::
   :toctree: ../generated/classes

   model.Datablock
   model.DataFile
   model.DatasetLifecycle
   model.DerivedDataset
   model.MongoQueryable
   model.OrigDatablock
   model.Ownable
   model.RawDataset
   model.Technique

Typing
~~~~~~

.. currentmodule:: scitacean

.. autosummary::
   :toctree: ../generated/classes
   :template: scitacean-class-template.rst
   :recursive:

   typing.Downloader
   typing.DownloadConnection
   typing.FileTransfer
   typing.UploadConnection
   typing.Uploader

Testing
~~~~~~~

.. currentmodule:: scitacean

.. autosummary::
   :toctree: ../generated/classes
   :template: scitacean-class-template.rst
   :recursive:

   testing.client.FakeClient
   testing.transfer.FakeFileTransfer
