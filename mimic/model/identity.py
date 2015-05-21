"""
Models relating to identity.
"""
from attr import attributes, attr, validators

from zope.interface import Interface, implementer


@attributes
class IdentitySession(object):
    """
    An identity session for a tenant.
    """
    @classmethod
    def from_store(cls, session_store, tenant_id):
        """
        Get the identity session for the given tenant.
        """
        return (session_store
                .session_for_tenant_id(tenant_id)
                .data_for_api(cls, cls))

    identity_admin = attr(default=False,
                          validator=validators.instance_of(bool))


class ICredentials(Interface):
    """
    An :obj:`ICredentials` provides identity authentication credentials.
    """
    def get_session(session_store):  # pragma:nocover
        """
        Get a session corresponding to the user and tenant from the given
        session store.

        :param session_store: a :class:`mimic.session.SessionStore`
        """

    def from_json(json_blob):  # pragma:nocover
        """
        Given a JSON dictionary containing credentials, creates a ICrednetials
        object.
        """


@implementer(ICredentials)
@attributes
class PasswordCredentials(object):
    """
    An object representing username/password + optional tenant credentials
    """
    username = attr()
    password = attr()
    tenant_id = attr(default=None)

    def get_session(self, session_store):
        """
        Get a session corresponding to the user and tenant from the given
        session store.

        :param session_store: a :class:`mimic.session.SessionStore`
        """
        return session_store.session_for_username_password(
            self.username, self.password, self.tenant_id)

    @classmethod
    def from_json(cls, json_blob):
        """
        Given an authentication JSON blob, which should look like:

        ```
        {
            "auth": {
                "passwordCredentials": {
                    "username": "user",
                    "password": "pass"
                },
                "tenantId": "111111"
            }
        }
        ```

        ``"tenantId"`` is interchanable with ``"tenantName"``, and is
        optional.

        :return: a class:`PasswordCredentials` object
        """
        tenant_id = (json_blob['auth'].get('tenantName', None) or
                     json_blob['auth'].get('tenantId', None))
        username = json_blob['auth']['passwordCredentials']['username']
        password = json_blob['auth']['passwordCredentials']['password']
        return cls(username=username, password=password, tenant_id=tenant_id)


@implementer(ICredentials)
@attributes
class APIKeyCredentials(object):
    """
    An object representing username/api-key + optional tenant credentials
    """
    username = attr()
    api_key = attr()
    tenant_id = attr(default=None)

    def get_session(self, session_store):
        """
        Get a session corresponding to the user and tenant from the given
        session store.

        :param session_store: a :class:`mimic.session.SessionStore`
        """
        return session_store.session_for_api_key(
            self.username, self.api_key, self.tenant_id)

    @classmethod
    def from_json(cls, json_blob):
        """
        Given an authentication JSON blob, which should look like:

        ```
        {
            "auth": {
                "RAX-KSKEY:apiKeyCredentials": {
                    "username": "user",
                    "apiKey": "key"
                },
                "tenantId": "111111"
            }
        }
        ```

        ``"tenantId"`` is interchanable with ``"tenantName"``, and is
        optional.

        :return: a class:`APIKeyCredentials` object
        """
        creds = json_blob['auth']
        tenant_id = (creds.get('tenantName', None) or
                     creds.get('tenantId', None))
        username = creds['RAX-KSKEY:apiKeyCredentials']['username']
        api_key = creds['RAX-KSKEY:apiKeyCredentials']['apiKey']
        return cls(username=username, api_key=api_key, tenant_id=tenant_id)


@implementer(ICredentials)
@attributes
class TokenCredentials(object):
    """
    An object representing token + optional tenant credentials
    """
    token = attr()
    tenant_id = attr(validator=validators.instance_of(basestring))

    def get_session(self, session_store):
        """
        Get a session corresponding to the user and tenant from the given
        session store.

        :param session_store: a :class:`mimic.session.SessionStore`
        """
        return session_store.session_for_token(self.token, self.tenant_id)

    @classmethod
    def from_json(cls, json_blob):
        """
        Given an authentication JSON blob, which should look like:

        ```
        {
            "auth": {
                "token": {
                    "id": "my_token"
                },
                "tenantId": "111111"
            }
        }
        ```

        ``"tenantId"`` is interchanable with ``"tenantName"``, and is
        optional.

        :return: a class:`APIKeyCredentials` object
        """
        tenant_id = (json_blob['auth'].get('tenantName', None) or
                     json_blob['auth'].get('tenantId', None))
        token = json_blob['auth']['token']['id']
        return cls(token=token, tenant_id=tenant_id)
