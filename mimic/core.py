# -*- test-case-name: mimic.test.test_core -*-

from __future__ import unicode_literals
from characteristic import attributes

from mimic.rest.nova_api import NovaApi
from mimic.rest.loadbalancer_api import LoadBalancerApi
from datetime import datetime, timedelta
from six import text_type

from uuid import uuid4

@attributes("username token tenant_id expires".split())
class Session(object):
    pass



class MimicCore(object):
    """
    A MimicCore contains a mapping from URI prefixes to particular service
    mocks.
    """

    def __init__(self, clock):
        self._clock = clock
        self._token_to_session = {
            # mapping of token (unicode) to session (Session)
        }
        self._username_to_token = {
            # mapping of token (unicode) to username (unicode: key in
            # _token_to_session)
        }
        apis = [
            NovaApi(),
            LoadBalancerApi(),
        ]
        self.uri_prefixes = {
            # map of (region, service_id) to (somewhat ad-hoc interface) "Api"
            # object.
        }
        for api in apis:
            entries = api.catalog_entries(tenant_id=None)
            for entry in entries:
                for endpoint in entry.endpoints:
                    self.uri_prefixes[(endpoint.region, str(uuid4()))] = api


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
            if key not in attributes:
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


    def session_for_username_password(self, username, password):
        """
        Create or return a :obj:`Session` based on a user's credentials.
        """
        if username in self._username_to_token:
            return self._token_to_session[self._username_to_token[username]]
        return self._new_session(username=username)


    def session_for_impersonation(self, username, expires_in):
        """
        
        """
        session = self.session_for_username_password(
            username, "lucky we don't check passwords, isn't it",
        )
        key = ('impersonation', session.username)
        if key in self._username_to_token:
            return self._username_to_token[key]
        subsession = self._new_session(
            username=username,
            expires=datetime.utcfromtimestamp(self._clock.seconds() +
                                              expires_in),
            tenant_id=session.tenant_id,
            username_key=key,
        )
        return subsession


    def service_with_region(self, region_name, service_id):
        """
        Given the name of a region and a mimic internal service ID, get a
        resource for that service.

        :param unicode region_name: the name of the region that the service
            resource exists within.

        :return: A resource.
        :rtype: :obj:`twisted.web.iweb.IResource`
        """
        key = (region_name, service_id)
        if key in self.uri_prefixes:
            return self.uri_prefixes[key].app.resource()


    def entries_for_tenant(self, tenant_id, prefix_map, prefix):
        """
        Get all the :obj:`mimic.catalog.Entry` objects for the given tenant ID.

        :param unicode tenant_id: A fictional tenant ID.
        """
        for (region, service_id), api in sorted(self.uri_prefixes.items()):
            for entry in api.catalog_entries(tenant_id):
                prefix_map[entry] = "/".join([prefix.rstrip("/"),
                                              region, service_id,
                                              ""])
                yield entry
