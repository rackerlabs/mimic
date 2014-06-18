
from __future__ import unicode_literals

import six

from twisted.trial.unittest import SynchronousTestCase

from twisted.internet.task import Clock
from mimic.core import MimicCore
from datetime import datetime


class SessionCreationTests(SynchronousTestCase):
    """
    Tests for requesting sessions from a MimicCore.
    """

    def test_username_password_new(self):
        """
        MimicCore.session_for_username_password creates a new session (if no
        such session exists for the given username).
        """
        clock = Clock()
        core = MimicCore(clock)
        clock.advance(4321)
        session = core.session_for_username_password("example_user",
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
        core = MimicCore(Clock())
        a = core.session_for_username_password("a", "ignored")
        b = core.session_for_username_password("b", "ignored")
        self.assertNotEqual(a.token, b.token)

    def test_by_username_after_token(self):
        """
        MimicCore.session_for_username_password should retrieve the same
        session that was created by MimicCore.session_for_token.
        """
        core = MimicCore(Clock())
        a = core.session_for_token("testtoken")
        b = core.session_for_username_password(a.username, "testpswd")
        c = core.session_for_api_key(a.username, "testapikey")
        self.assertIdentical(a, b)
        self.assertIdentical(a, c)

    def test_by_token_after_username(self):
        """
        MimicCore.session_for_token should retrieve the same session that was
        created by MimicCore.session_for_username_password.
        """
        core = MimicCore(Clock())
        a = core.session_for_username_password("username", "testpswd")
        b = core.session_for_token(a.token)
        self.assertIdentical(a, b)
        c = core.session_for_api_key("apiuser", "testkey")
        d = core.session_for_token(c.token)
        self.assertIdentical(c, d)

    def test_impersonation(self):
        """
        MimicCore.session_for_impersonation will return a session that can be
        retrieved by token_id but not username.
        """
        clock = Clock()
        core = MimicCore(clock)
        A_LITTLE = 1234
        clock.advance(A_LITTLE)
        A_LOT = 65432
        a = core.session_for_impersonation("pretender", A_LOT)
        a_prime = core.session_for_impersonation("pretender", A_LOT)
        self.assertIdentical(a, a_prime)
        b = core.session_for_token(a.token)
        self.assertEqual(
            a.expires, datetime.utcfromtimestamp(A_LITTLE + A_LOT))
        self.assertIdentical(a, b)
        c = core.session_for_username_password("pretender", "not a password")
        self.assertNotIdentical(a, c)
        self.assertEqual(a.username, c.username)
        self.assertEqual(a.tenant_id, c.tenant_id)

    def test_session_for_tenant_id(self):
        """
        MimicCore.session_for_tenant_id will return a session that can be
        retrieved by tenant_id.
        """
        clock = Clock()
        core = MimicCore(clock)
        session = core.session_for_username_password("someuser", "testpass")
        session2 = core.session_for_tenant_id(session.tenant_id)
        self.assertIdentical(session, session2)

    def test_session_for_tenant_id_with_custom_tenant(self):
        """
        MimicCore.session_for_tenant_id will return a session that can be
        retrieved by tenant_id.
        """
        clock = Clock()
        core = MimicCore(clock)
        session = core.session_for_username_password("someuser", "testpass",
                                                     "sometenant")
        session2 = core.session_for_tenant_id("sometenant")
        self.assertIdentical(session, session2)
