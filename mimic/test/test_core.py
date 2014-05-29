
from __future__ import unicode_literals

import six
from unittest import TestCase

from twisted.internet.task import Clock
from mimic.core import MimicCore
from datetime import datetime


class SessionCreationTests(TestCase):
    """
    
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

