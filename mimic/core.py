# -*- test-case-name: mimic.test.test_core -*-

"""
Service catalog hub and integration for Mimic application objects.
"""

from __future__ import unicode_literals
from characteristic import attributes

from twisted.python.urlpath import URLPath
from twisted.plugin import getPlugins
from mimic import plugins

from datetime import datetime, timedelta
from six import text_type

from mimic.imimic import IAPIMock
from uuid import uuid4


@attributes("username token tenant_id expires".split())
class Session(object):
    """
    A mimic Session is a record of an authentication token for a particular
    username and tenant_id.
    """

    @property
    def user_id(self):
        """
        Return a unique numeric ID based on the username.
        """
        return text_type(hash(self.username))


class MimicCore(object):
    """
    A MimicCore contains a mapping from URI prefixes to particular service
    mocks.
    """

    def __init__(self, clock, apis):
        """
        Create a MimicCore with an IReactorTime to do any time-based scheduling
        against.

        :param clock: an IReactorTime which will be used for session timeouts
            and determining timestamps.
        :type clock: :obj:`twisted.internet.interfaces.IReactorTime`

        :param apis: an iterable of all :obj:`IAPIMock`s that this MimicCore
            will expose.
        """
        self._clock = clock
        self._token_to_session = {
            # mapping of token (unicode) to session (Session)
        }
        self._tenant_to_token = {
            # mapping of tenant_id (unicode) to token (unicode)
        }
        self._username_to_token = {
            # mapping of token (unicode) to username (unicode: key in
            # _token_to_session)
        }
        self._uuid_to_api = {}

        for api in apis:
            this_api_id = str(uuid4())
            self._uuid_to_api[this_api_id] = api

    @classmethod
    def fromPlugins(cls, clock):
        """
        Create a :obj:`MimicCore` from all :obj:`IAPIMock` plugins.
        """
        return cls(clock, list(getPlugins(IAPIMock, plugins)))

    def _new_session(self, username_key=None, **attributes):
        """
        Create a new session and persist it according to its username and token
        values.

        :param attributes: Keyword parameters containing zero or more of
            ``username``, ``token``, and ``tenant_id``.  Any fields that are
            not specified will be filled out automatically.

        :return: A new session with all fields filled out and an expiration
                 time 1 day in the future (according to the clock associated
                 with this :obj:`MimicCore`).
        :rtype: :obj:`Session`
        """
        for key in ['username', 'token', 'tenant_id']:
            if attributes.get(key, None) is None:
                attributes[key] = key + "_" + text_type(uuid4())
        if 'expires' not in attributes:
            attributes['expires'] = (
                datetime.utcfromtimestamp(self._clock.seconds())
                + timedelta(days=1)
            )
        session = Session(**attributes)
        if username_key is None:
            username_key = session.username
        self._username_to_token[username_key] = session.token
        self._token_to_session[session.token] = session
        self._tenant_to_token[session.tenant_id] = session.token
        return session

    def session_for_token(self, token):
        """
        :param unicode token: An authentication token previously created by
            session_for_api_key or session_for_username_password.

        :return: a session for the given token, only if that token already
                 exists.
        :rtype: Session

        :raise: :obj:`KeyError` if no such thing exists.
        """
        if token in self._token_to_session:
            return self._token_to_session[token]
        return self._new_session(token=token)

    def session_for_api_key(self, username, api_key):
        """
        Create or return a :obj:`Session`.

        :param unicode username: A user name.
        :param unicode api_key: An API key that should match the username.

        :return: a session for the given user.
        :rtype: Session
        """
        # One day, API keys will be different from passwords, but not today.
        return self.session_for_username_password(username, api_key)

    def session_for_username_password(self, username, password,
                                      tenant_id=None):
        """
        Create or return a :obj:`Session` based on a user's credentials.
        """
        if username in self._username_to_token:
            return self._token_to_session[self._username_to_token[username]]
        return self._new_session(username=username,
                                 tenant_id=tenant_id)

    def session_for_impersonation(self, username, expires_in):
        """
        Create or return a :obj:`Session` impersonating a given user; this
        session is distinct from the user's normal login session in that it
        will have an independent token.
        """
        session = self.session_for_username_password(
            username, "lucky we don't check passwords, isn't it",
        )
        key = ('impersonation', session.username)
        if key in self._username_to_token:
            return self._token_to_session[self._username_to_token[key]]
        subsession = self._new_session(
            username=username,
            expires=datetime.utcfromtimestamp(self._clock.seconds() +
                                              expires_in),
            tenant_id=session.tenant_id,
            username_key=key,
        )
        return subsession

    def session_for_tenant_id(self, tenant_id):
        """
        :param unicode tenant_id: The tenant_id of a previously-created
            session.
        """
        if tenant_id not in self._tenant_to_token:
            return self._new_session(tenant_id=tenant_id)
        return self.session_for_token(self._tenant_to_token[tenant_id])

    def service_with_region(self, region_name, service_id, base_uri):
        """
        Given the name of a region and a mimic internal service ID, get a
        resource for that service.

        :param unicode region_name: the name of the region that the service
            resource exists within.
        :param unicode service_id: the UUID for the service for the
            specified region
        :param str base_uri: the base uri to use instead of the default -
            most likely comes from a request URI

        :return: A resource.
        :rtype: :obj:`twisted.web.iweb.IResource`
        """
        if service_id in self._uuid_to_api:
            api = self._uuid_to_api[service_id]
            return api.resource_for_region(
                self.uri_for_service(region_name, service_id, base_uri)
            )

    def uri_for_service(self, region, service_id, base_uri):
        """
        Generate a URI prefix for a given region and service ID.

        Each plugin loaded into mimic generates a list of catalog entries; each
        catalog entry has a list of endpoints.  Each endpoint has a URI
        associated with it, which we call a "URI prefix", because the endpoint
        will have numerous other URIs beneath it in the hierarchy, generally
        starting with a version number and tenant ID.  The URI prefixes
        generated for this function point to the top of the endpoint's
        hierarchy, not including any tenant information.

        :param unicode region: the name of the region that the service resource
            exists within.
        :param unicode service_id: the UUID for the service for the specified
            region
        :param str base_uri: the base uri to use instead of the default - most
            likely comes from a request URI

        :return: The full URI locating the service for that region
        :rtype: ``str``
        """
        return str(URLPath.fromString(base_uri)
                   .child("service").child(service_id).child(region).child(""))

    def entries_for_tenant(self, tenant_id, prefix_map, base_uri):
        """
        Get all the :obj:`mimic.catalog.Entry` objects for the given tenant ID,
        populating a mapping of :obj:`mimic.catalog.Entry` to URI prefixes (as
        described by :pyobj:`MimicCore.uri_for_service`) for that entry.

        :param unicode tenant_id: A fictional tenant ID.
        :param dict prefix_map: a mapping of entries to uris
        :param str base_uri: the base uri to use instead of the default - most
            likely comes from a request URI

        :return: The full URI locating the service for that region
        """
        for service_id, api in self._uuid_to_api.items():
            for entry in api.catalog_entries(tenant_id):
                for endpoint in entry.endpoints:
                    prefix_map[endpoint] = self.uri_for_service(
                        endpoint.region, service_id, base_uri
                    )
                yield entry
