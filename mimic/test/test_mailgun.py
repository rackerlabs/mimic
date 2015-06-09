import urllib

from twisted.trial.unittest import SynchronousTestCase
from twisted.internet.task import Clock

from mimic.core import MimicCore
from mimic.resource import MimicRoot
from mimic.test.helpers import json_request, request


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
            self, root, "POST", "/cloudmonitoring.rackspace.com/messages",
            urllib.urlencode({"to": "example@eg.com", "subject": "test"})))
        self.assertEqual(200, response.code)

    def test_mailgun_send_message_receives_error_500(self):
        """
        ``/cloudmonitoring.rackspace.com/messages`` returns response code 500
        when the `to` address is `bademail@example.com`.
        """
        core = MimicCore(Clock(), [])
        root = MimicRoot(core).app.resource()

        response = self.successResultOf(request(
            self, root, "POST", "/cloudmonitoring.rackspace.com/messages",
            urllib.urlencode({"to": "bademail@example.com"})))
        self.assertEqual(500, response.code)

    def test_mailgun_send_message_receives_error_400(self):
        """
        ``/cloudmonitoring.rackspace.com/messages`` returns response code 500
        when the `to` address is `bademail@example.com`.
        """
        core = MimicCore(Clock(), [])
        root = MimicRoot(core).app.resource()

        response = self.successResultOf(request(
            self, root, "POST", "/cloudmonitoring.rackspace.com/messages",
            urllib.urlencode({"to": "failingemail@example.com"})))
        self.assertEqual(400, response.code)

    def test_mailgun_get_messages(self):
        """
        ``/cloudmonitoring.rackspace.com/messages`` returns response code 200.
        """
        core = MimicCore(Clock(), [])
        root = MimicRoot(core).app.resource()

        for x in range(5):
            (response, content) = self.successResultOf(json_request(
                self, root, "POST", "/cloudmonitoring.rackspace.com/messages",
                urllib.urlencode({"to": "example{0}@eg.com".format(x), "subject": "test"})))
            self.assertEqual(200, response.code)

        (response, content) = self.successResultOf(json_request(
            self, root, "GET", "/cloudmonitoring.rackspace.com/messages"))
        self.assertEqual(200, response.code)
        self.assertEqual(len(content["items"]), 5)

    def test_mailgun_get_messages_by_filter(self):
        """
        ``/cloudmonitoring.rackspace.com/messages`` returns response code 200
        and is fitered by `to`.
        """
        core = MimicCore(Clock(), [])
        root = MimicRoot(core).app.resource()

        for x in range(5):
            (response, content) = self.successResultOf(json_request(
                self, root, "POST", "/cloudmonitoring.rackspace.com/messages",
                urllib.urlencode({"to": "example{0}@eg.com".format(x), "subject": "test"})))
            self.assertEqual(200, response.code)

        (response, content) = self.successResultOf(json_request(
            self, root, "GET", "/cloudmonitoring.rackspace.com/messages?to=example0@eg.com"))
        self.assertEqual(200, response.code)
        self.assertEqual(len(content["items"]), 1)

    def test_mailgun_get_messages_resulting_in_500s(self):
        """
        ``/cloudmonitoring.rackspace.com/messages/500s`` returns response code 200
        and count of requests that resulted in 500s during message creation.
        """
        core = MimicCore(Clock(), [])
        root = MimicRoot(core).app.resource()

        for x in range(5):
            response = self.successResultOf(request(
                self, root, "POST", "/cloudmonitoring.rackspace.com/messages",
                urllib.urlencode({"to": "bademail@example.com", "subject": "test"})))
            self.assertEqual(500, response.code)

        (response, content) = self.successResultOf(json_request(
            self, root, "GET", "/cloudmonitoring.rackspace.com/messages/500s"))
        self.assertEqual(200, response.code)
        self.assertEqual(content["count"], 5)

    def test_mailgun_get_message_header_for_message(self):
        """
        ``/cloudmonitoring.rackspace.com/messages/headers`` returns response code 200
        and headers recieved for a given `to` address.
        """
        core = MimicCore(Clock(), [])
        root = MimicRoot(core).app.resource()

        (response, content) = self.successResultOf(json_request(
            self, root, "POST", "/cloudmonitoring.rackspace.com/messages",
            urllib.urlencode({"to": "email@example.com", "h:X-State": ["WARNING"],
                              "subject": "test"})))
        self.assertEqual(200, response.code)

        (response, content) = self.successResultOf(json_request(
            self, root, "GET", "/cloudmonitoring.rackspace.com/messages/headers?to=email@example.com"))
        self.assertEqual(200, response.code)
        self.assertTrue(content["email@example.com"])
