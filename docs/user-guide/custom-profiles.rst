.. _custom-profiles:

Custom profiles
===============

.. py:currentmodule:: scitacean

Basic configuration
-------------------

At a minimum, each profiles needs an API URL and a file transfer.
The file transfer may be ``None`` if no default tr
ansfer can be defined.
It can always be overridden when constructing a :class:`Client`.
See also :ref:`connecting-file-transfer`.

.. testcode::

    from scitacean import Profile

    profile = Profile(
        url="https://my-scicat.org/api/v4",
        file_transfer=...,
    )


.. _custom-profiles-single-sign-on:

OAuth
-----

Using :meth:`Client.login` requires an OAuth configuration.
(See also :ref:`connecting-sso`.)
OAuth is configured via :class:`auth.OAuthClient` objects.
Scitacean provides

- :class:`auth.OAuthClientNormal` for normal OAuth clients and
- :class:`auth.OAuthClientDevice` for device flow OAuth clients.

If possible, it is best to configure both types of clients and let the user pick one via the ``flow`` argument of :meth:`Client.login`.
Below is an example for the minimal configuration of both clients.
See the documentation of each for additional options.
These may be required for your setup to, e.g., select a specific port range.

.. testcode::

    from scitacean import Profile
    from scitacean.auth import OAuthClientNormal, OAuthClientDevice

    client_normal = OAuthClientNormal(
        provider="https://login.example.org",
        client_id="my-client-id",
    )

    client_device = OAuthClientDevice(
        provider="https://login.example.org",
        client_id="my-client-id",
    )

    profile = Profile(
        # Basic:
        url="https://my-scicat.org/api/v4",
        file_transfer=...,
        # OAuth:
        oauth_clients=(client_normal, client_device),
    )

.. hint::

    See :ref:`oauth-configuration` for the server setup.


Auxiliary configuration
-----------------------

Profiles can store some additional configuration.
This is currently unused by Scitacean itself, but the
`SciCat widget <https://github.com/SciCatProject/scicat_widget>`_ uses it to generate
its interface and fill dataset fields automatically.

.. testcode::

    from scitacean import Profile

    profile = Profile(
        # Basic:
        url="https://my-scicat.org/api/v4",
        file_transfer=...,
        # Aux:
        frontend_url="https://my-scicat.org",
        scientific_metadata_schema="plain",
        field_factories=...,
    )

frontend_url
~~~~~~~~~~~~
The frontend URL refers to the SciCat web interface.
It is usually the same as the API URL (``profile.url``) but without ``/api/v4`` at the end.

scientific_metadata_schema
~~~~~~~~~~~~~~~~~~~~~~~~~~
The scientific metadata schema can be either ``"plain"`` or ``"value-unit"``.
If controls how scientific metadata (:attr:`Dataset.meta`) is handled.
Keep in mind that Scitacean does nothing with this setting, it is only used by the SciCat widget.

- ``"plain"`` is the default and means that the metadata is used verbatim as specified.
- ``"value-unit"`` means that each metadata item is expected to be a dictionary with a ``"value"`` and a ``"unit"`` key.

.. testcode::

    schema = "plain"
    # or
    schema = "value-unit"

field_factories
~~~~~~~~~~~~~~~
The field factories define a way to compute some dataset fields from other fields.
Each factory is a callable that takes the values of some fields and returns the value of another field.
The inputs are identified by their names.
See :attr:`Profile.field_factories` for more details.

Keep in mind that Scitacean does nothing with this setting, it is only used by the SciCat widget.

For example, the following sets the owner group of a dataset to the first proposal ID, stripped of whitespace:

.. testcode::

    field_factories = {
        "ownerGroup": lambda proposalId: str(proposalIds[0]).strip(),
    }

Here is a more complex example that computes the source folder from the proposal ID and the instrument name.
It returns ``None`` if there is not exactly one proposal ID or instrument name.
This indicates that the field cannot be set automatically.
Note that this factory uses the special ``instrumentNames`` field which is not part of the dataset itself, but is provided by the SciCat widget based on the selected instrument Ids.

.. testcode::

    from collections.abc import Iterable

    def format_source_folder(
        proposalIds: Iterable[str], instrumentNames: Iterable[str]
    ) -> str | None:
        try:
            [proposal_id] = proposalIds
        except ValueError:
            return None
        try:
            [instrument_name] = instrumentNames
        except ValueError:
            return None

        return f"/base/{proposal_id}/{str(instrument_name).strip().lower()}/upload"

    field_factories = {
        "sourceFolder": format_source_folder,
    }
