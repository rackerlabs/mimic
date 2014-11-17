
import six
from datetime import datetime

from twisted.trial.unittest import SynchronousTestCase

from twisted.internet.task import Clock

from mimic.session import SessionStore


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
        session that was created by SessionStore.session_for_token.
        """
        sessions = SessionStore(Clock())
        a = sessions.session_for_token("testtoken")
        b = sessions.session_for_username_password(a.username, "testpswd")
        c = sessions.session_for_api_key(a.username, "testapikey")
        self.assertIdentical(a, b)
        self.assertIdentical(a, c)

    def test_by_token_after_username(self):
        """
        SessionStore.session_for_token should retrieve the same session that
        was created by SessionStore.session_for_username_password.
        """
        sessions = SessionStore(Clock())
        a = sessions.session_for_username_password("username",
                                                   "testpswd")
        b = sessions.session_for_token(a.token)
        self.assertIdentical(a, b)
        c = sessions.session_for_api_key("apiuser", "testkey")
        d = sessions.session_for_token(c.token)
        self.assertIdentical(c, d)

    def test_impersonation(self):
        """
        SessionStore.session_for_impersonation will return a session that can
        be retrieved by token_id but not username.
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
        self.assertNotIdentical(a, c)
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
