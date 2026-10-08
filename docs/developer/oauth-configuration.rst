.. _oauth-configuration:

OAuth Configuration
===================

This page describes how to configure an identity provider and SciCat backend for Scitacean's OAuth.

Identity provider
-----------------

The options used here are based on Keycloak.
They may differ for you identity provider but there should be equivalent options available as long as it supports OpenID Connect.

1. Find the SciCat client ID (e.g., ``"scicat"``)
    - It is configured in the SciCat setup as ``OIDC_CLIENT_ID``.
2. Create a new client
    - Name it, e.g., ``"scitacean"``
    - Configure it to use OpenID Connect if possible (this may simplify some steps)
    - Disable client authentication (This is a client for native apps without a client secret)
    - Enable one or both of
        - The standard ('normal') auth flow
        - The device authorization grant flow
    - When using a 'normal' flow, configure the callback URL
        - Scheme needs to be ``http``
        - Needs to allow ``127.0.0.1``
        - Allow one or more port
        - Optionally but recommended: use a path segment
        - E.g.: ``http://127.0.0.1:8081/login-callback``
    - Set up a custom scope (a.k.a. mapping)
        - Target: 'Audience'
        - Value: ``"scicat"`` (the SciCat client ID)
3. Perform a login to check the client
    - Configure a :class:`scitacean.auth.OAuthClientNormal` and call ``token = client.login()``
    - This token will be an access token, not an identity token.
    - The token must contain:
        - ``aud="scicat"`` (or whichever SciCat client ID use use; configured via 'Audience' mapping above)
        - ``iss="<the-identity-provider-url>``
        - ``email=<your-email>`` (Optional but needed if you use this method for the first login with SciCat before an account has been created.)

SciCat
------

Configure the SciCat backend using the following.
``"scitacean"`` is the client ID of your new client configured above.

.. code-block:: yaml

    OIDC_ADDITIONAL_AUTHORIZED_PARTIES: "scitacean"
