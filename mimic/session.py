# -*- test-case-name: mimic.test.test_session -*-

"""
Implementation of simple in-memory session storage and generation for Mimic.
"""

from six import text_type
from uuid import uuid4
from datetime import datetime, timedelta

from characteristic import attributes, Attribute


@attributes(['username', 'token', 'tenant_id', 'expires',
             Attribute('_api_objects', default_factory=dict)])
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

    def data_for_api(self, api_mock, data_factory):
        """
        Get the application data for a given API, creating it if necessary.
        """
        if api_mock not in self._api_objects:
            self._api_objects[api_mock] = data_factory()
        return self._api_objects[api_mock]


@attributes([Attribute('session', instance_of=Session),
             'desired_tenant'])
class NonMatchingTenantError(Exception):
    """
    A session's tenant ID does not match the desired tenant ID.
    """


class SessionStore(object):
    """
    A collection of sessions addressable by multiple different keys.

    Unlike many traditional types of session storage, new authenticated users
    are created on demand, since all authentication succeeds by default within
    Mimic.

    :ivar IReactorTime clock: The clock used to track session expiration.
    """

    def __init__(self, clock):
        """
        Create a session store with the given IReactorTime provider.
        """
        self.clock = clock
        self._token_to_session = {
            # mapping of token (unicode) to session (Session)
        }
        self._userid_to_session = {
            # mapping of userid (ascii) to session (Session)
        }
        self._tenant_to_token = {
            # mapping of tenant_id (unicode) to token (unicode)
        }
        self._username_to_token = {
            # mapping of token (unicode) to username (unicode: key in
            # _token_to_session)
        }

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
                if key == 'tenant_id':
                    # integer tenant IDs - uuid4 ints are too long
                    attributes[key] = text_type(int(uuid4().int % 1e15))

        if 'expires' not in attributes:
            attributes['expires'] = (
                datetime.utcfromtimestamp(self.clock.seconds())
                + timedelta(days=1)
            )
        session = Session(**attributes)
        if username_key is None:
            username_key = session.username
        self._username_to_token[username_key] = session.token
        self._token_to_session[session.token] = session
        self._userid_to_session[session.user_id] = session
        self._tenant_to_token[session.tenant_id] = session.token
        return session

    def session_for_token(self, token, tenant_id=None):
        """
        :param unicode token: An authentication token previously created by
            session_for_api_key or session_for_username_password.

        :return: a session for the given token, only if that token already
                 exists.
        :rtype: Session

        :raise: :obj:`KeyError` if no such thing exists.
        """
        if token in self._token_to_session:
            s = self._token_to_session[token]
            if tenant_id is not None and s.tenant_id != tenant_id:
                raise NonMatchingTenantError(session=s,
                                             desired_tenant=tenant_id)
            return s

        return self._new_session(token=token, tenant_id=tenant_id)

    def session_for_api_key(self, username, api_key, tenant_id=None):
        """
        Create or return a :obj:`Session`.

        :param unicode username: A user name.
        :param unicode api_key: An API key that should match the username.

        :return: a session for the given user.
        :rtype: Session
        """
        # One day, API keys will be different from passwords, but not today.
        return self.session_for_username_password(username, api_key, tenant_id)

    def session_for_username_password(self, username, password,
                                      tenant_id=None):
        """
        Create or return a :obj:`Session` based on a user's credentials.
        """
        if username in self._username_to_token:
            s = self._token_to_session[self._username_to_token[username]]
            if tenant_id is not None and s.tenant_id != tenant_id:
                raise NonMatchingTenantError(session=s,
                                             desired_tenant=tenant_id)
            return s

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
            expires=datetime.utcfromtimestamp(self.clock.seconds() +
                                              expires_in),
            tenant_id=session.tenant_id,
            username_key=key,
            api_objects=session._api_objects,
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
