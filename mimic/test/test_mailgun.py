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

    def setUp(self):
        """
        Initialize core and root
        """
        self.core = MimicCore(Clock(), [])
        self.root = MimicRoot(self.core).app.resource()

    def create_message_successfully(self, root, data):
        """
        Create a message and validate the response is the
        """
        (response, content) = self.successResultOf(json_request(
            self, root, "POST", "/cloudmonitoring.rackspace.com/messages",
            urllib.urlencode(data)))
        self.assertEqual(200, response.code)

    def get_content_from_list_messages(self, root, to_filter=None):
        """
        Get messages and return content
        """
        url = "/cloudmonitoring.rackspace.com/messages"
        if to_filter:
            url = "/cloudmonitoring.rackspace.com/messages?to={0}".format(to_filter)
        (response, content) = self.successResultOf(json_request(
            self, root, "GET", url))
        self.assertEqual(200, response.code)
        return content

    def test_mailgun_send_message(self):
        """
        ``/cloudmonitoring.rackspace.com/messages`` returns response code 200
        when a create message is successful.
        """
        self.create_message_successfully(
            self.root,
            {"to": "example@eg.com", "subject": "test"})

    def test_mailgun_send_message_receives_error_500(self):
        """
        ``/cloudmonitoring.rackspace.com/messages`` returns response code 500
        when the `to` address is `bademail@example.com`.
        """
        response = self.successResultOf(request(
            self, self.root, "POST", "/cloudmonitoring.rackspace.com/messages",
            urllib.urlencode({"to": "bademail@example.com"})))
        self.assertEqual(500, response.code)

    def test_mailgun_send_message_receives_error_400(self):
        """
        ``/cloudmonitoring.rackspace.com/messages`` returns response code 400
        when the `to` address is `failingemail@example.com`.
        """
        response = self.successResultOf(request(
            self, self.root, "POST", "/cloudmonitoring.rackspace.com/messages",
            urllib.urlencode({"to": "failingemail@example.com"})))
        self.assertEqual(400, response.code)

    def test_mailgun_get_messages(self):
        """
        ``/cloudmonitoring.rackspace.com/messages`` returns response code 200
        and returns the list of messages created thus far.
        """
        for x in range(5):
            self.create_message_successfully(
                self.root,
                {"to": "example{0}@eg.com".format(x), "subject": "test"})
        content = self.get_content_from_list_messages(self.root)
        self.assertEqual(len(content["items"]), 5)

    def test_mailgun_get_messages_by_filter(self):
        """
        ``/cloudmonitoring.rackspace.com/messages`` returns response code 200
        and returns the list of messages created thus far, fitered by `to`
        address.
        """
        for x in range(5):
            self.create_message_successfully(
                self.root,
                {"to": "example{0}@eg.com".format(x), "subject": "test"})
        content = self.get_content_from_list_messages(self.root, 'example0@eg.com')
        self.assertEqual(len(content["items"]), 1)

    def test_mailgun_get_messages_resulting_in_500s(self):
        """
        ``/cloudmonitoring.rackspace.com/messages/500s`` returns response code 200
        and count of requests that resulted in 500s during message creation.
        """
        for x in range(5):
            response = self.successResultOf(request(
                self, self.root, "POST", "/cloudmonitoring.rackspace.com/messages",
                urllib.urlencode({"to": "bademail@example.com", "subject": "test"})))
            self.assertEqual(500, response.code)

        (response, content) = self.successResultOf(json_request(
            self, self.root, "GET", "/cloudmonitoring.rackspace.com/messages/500s"))
        self.assertEqual(200, response.code)
        self.assertEqual(content["count"], 5)

    def test_mailgun_get_message_header_for_message(self):
        """
        ``/cloudmonitoring.rackspace.com/messages/headers`` returns response code 200
        and headers recieved for a given `to` address.
        """
        self.create_message_successfully(
            self.root,
            {"to": "email@example.com", "h:X-State": ["WARNING"],
             "subject": "test"})

        (response, content) = self.successResultOf(json_request(
            self, self.root,
            "GET", "/cloudmonitoring.rackspace.com/messages/headers?to=email@example.com"))
        self.assertEqual(200, response.code)
        self.assertTrue(content["email@example.com"])
