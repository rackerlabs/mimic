"""
Tests for identity model objects.
"""

from __future__ import absolute_import, division, unicode_literals

import json

from twisted.internet.task import Clock
from twisted.trial.unittest import SynchronousTestCase

from mimic.canned_responses.auth import get_version_v2
from mimic.model.identity import IdentitySession
from mimic.session import SessionStore


class IdentitySessionTests(SynchronousTestCase):
    """
    Tests for identity session management.
    """
    def setUp(self):
        self.clock = Clock()
        self.session_store = SessionStore(self.clock)

    def test_get_version(self):
        """
        Check generation of keystone canned response, when providing only
        base_uri.
        """
        expected = {"version":
                    {"status": "stable",
                     "updated": "2014-04-17T00:00:00Z",
                     "media-types":
                     [{
                         "base": "application/json",
                         "type": "application/vnd.openstack.identity-v2.0+json"
                     }],
                     "id": "v2.0",
                     "links":
                     [{
                         "href": "http://ip_server:port/identity/v2.0",
                         "rel": "self"
                     }, {
                         "href": "http://docs.openstack.org/",
                         "type": "text/html",
                         "rel": "describedby"}]
                     }
                    }
        result = get_version_v2("http://ip_server:port/")

        self.assertEqual(json.dumps(result, sort_keys=True),
                         json.dumps(expected, sort_keys=True))

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
