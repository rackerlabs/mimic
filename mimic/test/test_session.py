
import six
from datetime import datetime
import re

from twisted.trial.unittest import SynchronousTestCase

from twisted.internet.task import Clock

from mimic.session import NonMatchingTenantError, SessionStore


class SessionCreationTests(SynchronousTestCase):
    """
    Tests for :class:`SessionStore`.
    """

    def test_username_password_new(self):
        """
        SessionStore.session_for_username_password creates a new session (if no
        such session exists for the given username).
        """
        clock = Clock()
        sessions = SessionStore(clock)
        clock.advance(4321)
        session = sessions.session_for_username_password("example_user",
                                                         "password")
        self.assertEqual(session.username, "example_user")
        self.assertEqual(session.expires,
                         datetime.utcfromtimestamp(4321 + 86400))
        self.assertIsInstance(session.tenant_id, six.text_type)
        self.assertIsInstance(session.token, six.text_type)
        self.assertNotEqual(session.username, session.token)
        self.assertNotEqual(session.token, session.tenant_id)

    def test_username_password_wrong_tenant(self):
        """
        Tenant ID is validated in
        :func:`SessionStore.session_for_username_password`.

        If called with the token of an existing session but the wrong tenant,
        raises :class:`NonMatchingTenantError`.
        """
        """
        SessionStore.session_for_username_password, if called with the
        username of an existing session but the wrong tenant, raises
        :class:`NonMatchingTenantError`.
        """
        clock = Clock()
        sessions = SessionStore(clock)
        clock.advance(4321)
        sessions.session_for_username_password("example_user",
                                               "password",
                                               "tenant_orig")
        self.assertRaises(
            NonMatchingTenantError,
            sessions.session_for_username_password,
            "example_user", "password", "tenant_new")

    def test_different_username_different_token(self):
        """
        Sessions are distinct if they are requested with distinct usernames.
        """
        sessions = SessionStore(Clock())
        a = sessions.session_for_username_password("a", "ignored")
        b = sessions.session_for_username_password("b", "ignored")
        self.assertNotEqual(a.token, b.token)

    def test_by_username_after_token(self):
        """
        SessionStore.session_for_username_password should retrieve the same
        session that was created by SessionStore.session_for_token.  Similarly
        for the API key.
        """
        sessions = SessionStore(Clock())
        a = sessions.session_for_token("testtoken")
        b = sessions.session_for_username_password(a.username, "testpswd")
        c = sessions.session_for_api_key(a.username, "testapikey")
        self.assertIdentical(a, b)
        self.assertIdentical(a, c)

    def test_session_for_apikey_after_username_wrong_tenant(self):
        """
        Tenant ID is validated in :func:`SessionStore.session_for_api_key`.

        If called with the token of an existing session but the wrong tenant,
        raises :class:`NonMatchingTenantError`.
        """
        sessions = SessionStore(Clock())
        a = sessions.session_for_username_password("username", "testpswd")
        self.assertRaises(
            NonMatchingTenantError,
            sessions.session_for_api_key,
            a.username, "testapikey", a.tenant_id + "wrong")

    def test_by_token_after_username(self):
        """
        Session retrieved by all the ``session_for_*`` methods are identical.

        :func:`SessionStore.session_for_token` should retrieve the same
        session that was created by
        :func:`SessionStore.session_for_username_password`.
        """
        sessions = SessionStore(Clock())
        a = sessions.session_for_username_password("username",
                                                   "testpswd")
        b = sessions.session_for_token(a.token)
        self.assertIdentical(a, b)
        c = sessions.session_for_api_key("apiuser", "testkey")
        d = sessions.session_for_token(c.token)
        self.assertIdentical(c, d)

    def test_by_token_after_username_wrong_tenant(self):
        """
        Tenant ID is validated in :func:`SessionStore.session_for_token`.

        If called with the token of an existing session but the wrong tenant,
        raises :class:`NonMatchingTenantError`.
        """
        sessions = SessionStore(Clock())
        a = sessions.session_for_username_password("username",
                                                   "testpswd")
        self.assertRaises(
            NonMatchingTenantError,
            sessions.session_for_token,
            a.token, a.tenant_id + 'wrong')

    def test_impersonation(self):
        """
        SessionStore.session_for_impersonation will return a session that can
        be retrieved by impersonated token_id or username.
        """
        clock = Clock()
        sessions = SessionStore(clock)
        A_LITTLE = 1234
        clock.advance(A_LITTLE)
        A_LOT = 65432
        a = sessions.session_for_impersonation("pretender", A_LOT)
        a_prime = sessions.session_for_impersonation("pretender", A_LOT)
        self.assertIdentical(a, a_prime)
        b = sessions.session_for_token(a.token)
        self.assertEqual(
            a.expires, datetime.utcfromtimestamp(A_LITTLE + A_LOT))
        self.assertIdentical(a, b)
        c = sessions.session_for_username_password("pretender",
                                                   "not a password")
        self.assertIdentical(a, c)
        self.assertEqual(a.username, c.username)
        self.assertEqual(a.tenant_id, c.tenant_id)

        # Right now all data_for_api cares about is hashability; this may need
        # to change if it comes to rely upon its argument actually being an API
        # mock.
        same_api = 'not_an_api'

        username_data = c.data_for_api(same_api, list)
        token_data = b.data_for_api(same_api, list)
        impersonation_data = a.data_for_api(same_api, list)

        self.assertIs(username_data, impersonation_data)
        self.assertIs(token_data, impersonation_data)

    def test_session_for_tenant_id(self):
        """
        SessionStore.session_for_tenant_id will return a session that can be
        retrieved by tenant_id.
        """
        clock = Clock()
        sessions = SessionStore(clock)
        session = sessions.session_for_username_password("someuser",
                                                         "testpass")
        session2 = sessions.session_for_tenant_id(session.tenant_id)
        self.assertIdentical(session, session2)

    def test_generate_username_from_tenant_id(self):
        """
        SessionStore.session_for_tenant_id will create a new session with a
        synthetic username if no such tenant ID yet exists.
        """
        clock = Clock()
        sessions = SessionStore(clock)
        session = sessions.session_for_tenant_id("user_specified_tenant")
        session2 = sessions.session_for_username_password(session.username,
                                                          "testpass")
        self.assertIdentical(session, session2)

    def test_session_for_tenant_id_with_custom_tenant(self):
        """
        SessionStore.session_for_tenant_id will return a session that can be
        retrieved by tenant_id.
        """
        clock = Clock()
        sessions = SessionStore(clock)
        session = sessions.session_for_username_password(
            "someuser", "testpass", "sometenant"
        )
        session2 = sessions.session_for_tenant_id("sometenant")
        self.assertIdentical(session, session2)

    def test_sessions_created_all_have_integer_tenant_ids(self):
        """
        Sessions created by
        :class:`SessionStore.session_for_username_password`,
        :class:`SessionStore.session_for_impersonation`,
        :class:`SessionStore.session_for_api_key`, and
        :class:`SessionStore.session_for_token`, when not passed a specific
        tenant ID, all generate integer-style tenant IDs.
        """
        clock = Clock()
        sessions = SessionStore(clock)
        sessions = [
            sessions.session_for_username_password("someuser1", "testpass"),
            sessions.session_for_impersonation("someuser2", 12),
            sessions.session_for_api_key("someuser3", "someapikey"),
            sessions.session_for_token("sometoken"),
        ]
        integer = re.compile('^\d+$')
        for session in sessions:
            self.assertIsNot(integer.match(session.tenant_id), None,
                             "{0} is not an integer.".format(
                                 session.tenant_id))
            self.assertTrue(int(session.tenant_id) < 1e15)

    def test_sessions_created_honor_specified_tenant_id(self):
        """
        Sessions created by
        :class:`SessionStore.session_for_username_password`,
        :class:`SessionStore.session_for_api_key`, and
        :class:`SessionStore.session_for_token`,
        :class:`SessionStore.session_for_tenant_id` all honor the passed-in
        tenant ID.
        """
        clock = Clock()
        sessions = SessionStore(clock)
        sessions = [
            sessions.session_for_username_password("user1", "pass",
                                                   "tenant1"),
            sessions.session_for_api_key("user2", "apikey",
                                         tenant_id="tenant2"),
            sessions.session_for_token("token", tenant_id="tenant3"),
            sessions.session_for_tenant_id("tenant4")
        ]
        for i, session in enumerate(sessions):
            self.assertEqual("tenant{0}".format(i + 1), session.tenant_id)

    def test_token_after_api_key_specifying_tenant(self):
        """
        Sessions created by
        :class:`SessionStore.session_for_api_key` and specifying
        the tenant ID should be returned on requests to
        :class:`SessionStore.session_for_token` that also specify
        the same tenant ID.
        """
        clock = Clock()
        sessions = SessionStore(clock)
        session_by_api_key = sessions.session_for_api_key(
            "user1", "f005ba11", tenant_id="559638")
        session_by_token = sessions.session_for_token(
            "token", tenant_id="559638")
        self.assertIs(session_by_api_key, session_by_token)

    def test_username_password_after_token_specifying_tenant(self):
        """
        Sessions created by
        :class:`SessionStore.session_for_token` and specifying
        the tenant ID should be returned on requests to
        :class:`SessionStore.session_for_username_password` that
        also specify the same tenant ID.
        """
        clock = Clock()
        sessions = SessionStore(clock)
        session_by_token = sessions.session_for_token("token", tenant_id="tenant1337")
        session_by_username_password = sessions.session_for_username_password(
            "user1", "pass", "tenant1337")
        self.assertIs(session_by_token, session_by_username_password)
