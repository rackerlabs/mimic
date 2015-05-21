"""
Models relating to identity.
"""
from uuid import uuid4

from attr import Factory, attributes, attr, validators

from six import string_types, text_type

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


class ICredential(Interface):
    """
    An :obj:`ICredential` provides identity authentication credentials.
    """
    def get_session(session_store):  # pragma:nocover
        """
        Get a session corresponding to the user and tenant from the given
        session store.

        :param session_store: a :class:`mimic.session.SessionStore`
        """


@implementer(ICredential)
@attributes
class PasswordCredentials(object):
    """
    An object representing username/password + optional tenant credentials
    """
    username = attr(validator=validators.instance_of(string_types))
    password = attr(validator=validators.instance_of(string_types))
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


@implementer(ICredential)
@attributes
class APIKeyCredentials(object):
    """
    An object representing username/api-key + optional tenant credentials
    """
    username = attr(validator=validators.instance_of(string_types))
    api_key = attr(validator=validators.instance_of(string_types))
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


@implementer(ICredential)
@attributes
class TokenCredentials(object):
    """
    An object representing token + optional tenant credentials
    """
    token = attr(validator=validators.instance_of(string_types))
    tenant_id = attr(validator=validators.instance_of(string_types))

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

        :return: a class:`TokenCredentials` object
        """
        tenant_id = (json_blob['auth'].get('tenantName', None) or
                     json_blob['auth'].get('tenantId', None))
        token = json_blob['auth']['token']['id']
        return cls(token=token, tenant_id=tenant_id)


@implementer(ICredential)
@attributes
class ImpersonationCredentials(object):
    """
    An object representing an auth-token + username to impersonate credentials
    """
    impersonator_token = attr()
    username = attr(validator=validators.instance_of(string_types))
    expires_in = attr(validator=validators.instance_of(int))
    impersonated_token = attr(
        default=Factory(lambda: 'impersonated_token_' + text_type(uuid4())),
        validator=validators.instance_of(string_types))

    def get_session(self, session_store):
        """
        Get a session corresponding to the user and tenant from the given
        session store.

        :param session_store: a :class:`mimic.session.SessionStore`
        """
        return session_store.session_for_impersonation(
            self.username,
            self.expires_in,
            self.impersonator_token,
            self.impersonated_token)

    @classmethod
    def from_json(cls, json_blob, auth_token):
        """
        Given an impersonation JSON blob, which should look like:

        ```
        {
            "RAX-AUTH:impersonation": {
                "expire-in-seconds": 1000,
                "user": {
                    "username": "my_user"
                }
            }
        }
        ```

        Along with a header "X-Auth-Token" with the impersonator's token,

        :return: a class:`ImpersonationCredentials` object
        """
        expires_in = json_blob['RAX-AUTH:impersonation']['expire-in-seconds']
        username = json_blob['RAX-AUTH:impersonation']['user']['username']
        return cls(impersonator_token=auth_token,
                   username=username,
                   expires_in=int(expires_in))
