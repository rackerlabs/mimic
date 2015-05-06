"""
Tests for identity model objects.
"""
from twisted.internet.task import Clock
from twisted.trial.unittest import SynchronousTestCase

from mimic.model.identity import IdentitySession
from mimic.session import SessionStore


class IdentitySessionTests(SynchronousTestCase):
    """
    Tests for identity session management.
    """
    def setUp(self):
        self.clock = Clock()
        self.session_store = SessionStore(self.clock)

    def test_get_identity_session(self):
        """
        Identity sessions are per-tenant. They do not affect each other.
        """
        identity_session = IdentitySession.from_store(
            self.session_store, "1234")
        self.assertFalse(identity_session.identity_admin)

        same_identity_session = IdentitySession.from_store(
            self.session_store, "1234")
        self.assertIdentical(identity_session, same_identity_session)

        different_identity_session = IdentitySession.from_store(
            self.session_store, "5678")
        self.assertNotIdentical(identity_session, different_identity_session)

    def test_identity_admin(self):
        """
        :attr:`identity_admin` is boolean, readable and writable and
        :data:`False` by default.
        """
        identity_session = IdentitySession.from_store(
            self.session_store, "1234")
        self.assertFalse(identity_session.identity_admin)
        identity_session.identity_admin = True
        self.assertTrue(identity_session.identity_admin)
        self.assertRaises(TypeError, IdentitySession, identity_admin=1)
