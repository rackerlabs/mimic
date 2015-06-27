"""
Models relating to identity.
"""
from uuid import uuid4

from attr import Factory, attributes, attr, validators

from six import string_types, text_type

from zope.interface import implementer

from mimic.imimic import ICredential


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


@implementer(ICredential)
@attributes
class PasswordCredentials(object):
    """
    An object representing the required username/password credentials plus
    an optional tenant identifier.

    :ivar username: The username of the user to authenticate.
    :ivar password: The password used to authenticate the user.
    :ivar tenant_id: Optional - the tenant ID of the user.
    """
    username = attr(validator=validators.instance_of(string_types))
    password = attr(validator=validators.instance_of(string_types))
    tenant_id = attr(default=None)
    type_key = "passwordCredentials"

    def get_session(self, session_store):
        """
        :see: :class:`ICredential.get_session`
        """
        return session_store.session_for_username_password(
            self.username, self.password, self.tenant_id)

    @classmethod
    def from_json(cls, json_blob):
        """
        Given an authentication JSON blob, which should look like::

            {
                "auth": {
                    "passwordCredentials": {
                        "username": "user",
                        "password": "pass"
                    },
                    "tenantId": "111111"
                }
            }

        ``"tenantId"`` is interchanable with ``"tenantName"``, and is
        optional.

        :return: a class:`PasswordCredentials` object
        """
        tenant_id = json_blob['auth'].get('tenantName')
        if tenant_id is None:
            tenant_id = json_blob['auth'].get('tenantId')

        username = json_blob['auth'][cls.type_key]['username']
        password = json_blob['auth'][cls.type_key]['password']
        return cls(username=username, password=password, tenant_id=tenant_id)


@implementer(ICredential)
@attributes
class APIKeyCredentials(object):
    """
    An object representing the required username/api-key credentials plus an
    optional tenant identifier.

    :ivar username: The username of the user to authenticate.
    :ivar api_key: The API key used to authenticate the user.
    :ivar tenant_id: Optional - the tenant ID of the user.
    """
    username = attr(validator=validators.instance_of(string_types))
    api_key = attr(validator=validators.instance_of(string_types))
    tenant_id = attr(default=None)
    type_key = "RAX-KSKEY:apiKeyCredentials"

    def get_session(self, session_store):
        """
        :see: :class:`ICredential.get_session`
        """
        return session_store.session_for_api_key(
            self.username, self.api_key, self.tenant_id)

    @classmethod
    def from_json(cls, json_blob):
        """
        Given an authentication JSON blob, which should look like::

            {
                "auth": {
                    "RAX-KSKEY:apiKeyCredentials": {
                        "username": "user",
                        "apiKey": "key"
                    },
                    "tenantId": "111111"
                }
            }

        ``"tenantId"`` is interchanable with ``"tenantName"``, and is
        optional.

        :return: a class:`APIKeyCredentials` object
        """
        tenant_id = json_blob['auth'].get('tenantName')
        if tenant_id is None:
            tenant_id = json_blob['auth'].get('tenantId')

        username = json_blob['auth'][cls.type_key]['username']
        api_key = json_blob['auth'][cls.type_key]['apiKey']
        return cls(username=username, api_key=api_key, tenant_id=tenant_id)


@implementer(ICredential)
@attributes
class TokenCredentials(object):
    """
    An object representing the required token/tenant credentials.

    :ivar token: The auth token to be authenticated
    :ivar tenant_id: The tenant ID the token belongs to.
    """
    token = attr(validator=validators.instance_of(string_types))
    tenant_id = attr(validator=validators.instance_of(string_types))
    type_key = "token"

    def get_session(self, session_store):
        """
        :see: :class:`ICredential.get_session`
        """
        return session_store.session_for_token(self.token, self.tenant_id)

    @classmethod
    def from_json(cls, json_blob):
        """
        Given an authentication JSON blob, which should look like::

            {
                "auth": {
                    "token": {
                        "id": "my_token"
                    },
                    "tenantId": "111111"
                }
            }

        ``"tenantId"`` is interchanable with ``"tenantName"``, and is
        optional.

        :return: a class:`TokenCredentials` object
        """
        tenant_id = json_blob['auth'].get('tenantName')
        if tenant_id is None:
            tenant_id = json_blob['auth'].get('tenantId')

        token = json_blob['auth'][cls.type_key]['id']
        return cls(token=token, tenant_id=tenant_id)


@implementer(ICredential)
@attributes
class ImpersonationCredentials(object):
    """
    An object representing the required
    impersonator-token/impersonated-username credentials.

    :ivar impersonator_token: The auth token of the user requesting an
        impersonation token.
    :ivar impersonated_username: The username of the user to be impersonated.
    :ivar impersonated_token: The impersonation token that can be used to
        authenticate as impersonated user.
    :ivar int expires_in: The number of seconds the impersonation token will
        last.
    """
    impersonator_token = attr()
    impersonated_username = attr(
        validator=validators.instance_of(string_types))
    expires_in = attr(validator=validators.instance_of(int))
    impersonated_token = attr(
        default=Factory(lambda: 'impersonated_token_' + text_type(uuid4())),
        validator=validators.instance_of(string_types))
    type_key = 'RAX-AUTH:impersonation'

    def get_session(self, session_store):
        """
        :see: :class:`ICredential.get_session`
        """
        return session_store.session_for_impersonation(
            self.impersonated_username,
            self.expires_in,
            self.impersonator_token,
            self.impersonated_token)

    @classmethod
    def from_json(cls, json_blob, auth_token):
        """
        Given an impersonation JSON blob, which should look like::

            {
                "RAX-AUTH:impersonation": {
                    "expire-in-seconds": 1000,
                    "user": {
                        "username": "my_user"
                    }
                }
            }

        Along with a header "X-Auth-Token" with the impersonator's token,

        :return: a class:`ImpersonationCredentials` object
        """
        expires_in = json_blob[cls.type_key].get('expire-in-seconds', 86400)
        username = json_blob[cls.type_key]['user']['username']
        return cls(impersonator_token=auth_token,
                   impersonated_username=username,
                   expires_in=int(expires_in))
