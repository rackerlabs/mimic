from twisted.trial.unittest import SynchronousTestCase
from twisted.internet.task import Clock

from mimic.core import MimicCore
from mimic.resource import MimicRoot
from mimic.test.helpers import json_request


class MailGunAPITests(SynchronousTestCase):

    """
    Tests for the Mailgun api
    """

    def test_mailgun_send_message(self):
        """
        ``/cloudmonitoring.rackspace.com/messages`` returns response code 200.
        """
        core = MimicCore(Clock(), [])
        root = MimicRoot(core).app.resource()

        (response, content) = self.successResultOf(json_request(
            self, root, "POST", "/cloudmonitoring.rackspace.com/messages"))
        self.assertEqual(200, response.code)

    def test_mailgun_get_message_count(self):
        """
        ``/cloudmonitoring.rackspace.com/messages`` returns response code 200.
        """
        core = MimicCore(Clock(), [])
        root = MimicRoot(core).app.resource()

        for x in range(5):
            (response, content) = self.successResultOf(json_request(
                self, root, "POST", "/cloudmonitoring.rackspace.com/messages"))
            self.assertEqual(200, response.code)

        (response, content) = self.successResultOf(json_request(
            self, root, "GET", "/cloudmonitoring.rackspace.com/messages"))
        self.assertEqual(200, response.code)
        self.assertEqual(content["message_count"], 5)
