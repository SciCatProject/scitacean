Installation
------------

.. tab-set::

    .. tab-item:: Project based

        .. tab-set::

            .. tab-item:: uv

                To add Scitacean from `pypi.org <https://pypi.org/project/scitacean/>`_:

                .. code-block:: sh

                    uv add scitacean

                If you need to transfer files via SFTP, i.e., with :class:`scitacean.transfer.sftp.SFTPFileTransfer`, specify the ``sftp``:

                .. code-block:: sh

                    uv add scitacean --extra sftp

            .. tab-item:: Pixi

                To add Scitacean from `conda-forge <https://anaconda.org/conda-forge/scitacean>`_:

                .. code-block:: sh

                    pixi add scitacean

                In contrast to to Pip package used by uv, this always installs the dependencies for SFTP.
                So no additional steps are needed to use :class:`scitacean.transfer.sftp.SFTPFileTransfer`.

    .. tab-item:: Environment based

        .. tab-set::

            .. tab-item:: Pip

                Scitacean is available on `pypi.org <https://pypi.org/project/scitacean/>`_:

                .. code-block:: sh

                    python -m pip install scitacean

                If you need to transfer files via SFTP, i.e., with :class:`scitacean.transfer.sftp.SFTPFileTransfer`, specify the ``sftp`` extra when installing:

                .. code-block:: sh

                    python -m pip install "scitacean[sftp]"

            .. tab-item:: Conda

                Scitacean is available on `conda-forge <https://anaconda.org/conda-forge/scitacean>`_:

                .. code-block:: sh

                    conda install -c conda-forge scitacean

                In contrast to installing with Pip, this always installs the dependencies for SFTP.
                So no additional steps are needed to use :class:`scitacean.transfer.sftp.SFTPFileTransfer`.
