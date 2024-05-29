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

   transfer.link.LinkFileTransfer
   transfer.sftp.SFTPFileTransfer

Auxiliary classes
~~~~~~~~~~~~~~~~~

.. autosummary::
   :toctree: ../generated/classes
   :template: scitacean-class-template.rst
   :recursive:

   client.ScicatClient
   datablock.OrigDatablock
   dataset.DatablockUploadModels
   PID
   RemotePath
   Thumbnail
   DatasetType

Exceptions
~~~~~~~~~~

.. autosummary::
   :toctree: ../generated/classes
   :template: scitacean-class-template.rst
   :recursive:

   FileUploadError
   IntegrityError
   ScicatCommError
   ScicatLoginError

Submodules
~~~~~~~~~~

.. autosummary::
   :toctree: ../generated/modules
   :template: scitacean-module-template.rst
   :recursive:

   model
   testing
   typing

Miscellaneous
~~~~~~~~~~~~~

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
