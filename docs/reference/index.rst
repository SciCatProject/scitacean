API reference
=============

Classes
-------

.. currentmodule:: scitacean

Main classes
~~~~~~~~~~~~

.. There is special handling of class constructors in the template.

.. autosummary::
   :toctree: ../generated/classes
   :template: scitacean-class-template.rst
   :recursive:

   Client
   Dataset
   File

File transfer
~~~~~~~~~~~~~

.. autosummary::
   :toctree: ../generated/classes
   :template: scitacean-class-template.rst
   :recursive:

   transfer.ssh.SSHFileTransfer

Auxiliary classes
~~~~~~~~~~~~~~~~~

.. autosummary::
   :toctree: ../generated/classes
   :template: scitacean-class-template.rst
   :recursive:

   datablock.OrigDatablockProxy
   dataset.DatablockModels
   PID
   RemotePath
   model.DatasetType

Dataclasses
~~~~~~~~~~~

.. currentmodule:: scitacean._dataset_fields

.. autosummary::
   :toctree: ../generated/classes
   :template: scitacean-dataclass-template.rst
   :recursive:

   DatasetFields

Exceptions
~~~~~~~~~~

.. currentmodule:: scitacean

.. autosummary::
   :toctree: ../generated/classes
   :template: scitacean-class-template.rst
   :recursive:

   FileUploadError
   IntegrityError
   ScicatCommError
   ScicatLoginError

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

Miscellaneous
~~~~~~~~~~~~~

.. currentmodule:: scitacean

.. autosummary::
   :toctree: ../generated/functions
   :recursive:

   filesystem.checksum_of_file
   filesystem.escape_path
   filesystem.file_size
   filesystem.file_modification_time
   logging.logger_name
   logging.get_logger
   util.formatter.DatasetPathFormatter
