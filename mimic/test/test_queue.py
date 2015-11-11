from __future__ import absolute_import, division, unicode_literals

import json
import treq

from twisted.trial.unittest import SynchronousTestCase
from twisted.internet.task import Clock

from mimic.core import MimicCore
from mimic.resource import MimicRoot
from mimic.test.helpers import json_request, request
from mimic.rest.queue_api import QueueApi


class QueueAPITests(SynchronousTestCase):

    """
    Tests for the Queue plugin api
    """

    def setUp(self):
        """
        Create a :obj:`MimicCore` with :obj:`QueueApi` as the only plugin,
        and create a queue
        """
        self.clock = Clock()
        self.core = MimicCore(self.clock, [QueueApi()])
        self.root = MimicRoot(self.core).app.resource()
        self.response = request(
            self, self.root, b"POST", "/identity/v2.0/tokens",
            json.dumps({
                "auth": {
                    "passwordCredentials": {
                        "username": "testQueue",
                        "password": "testQueuePassword",
                    },
                }
            }).encode("utf-8")
        )
        self.auth_response = self.successResultOf(self.response)
        self.json_body = self.successResultOf(
            treq.json_content(self.auth_response))
        self.uri = self.json_body['access']['serviceCatalog'][0]['endpoints'][0]['publicURL']
        self.queue_name = "test_queue"
        self.create_queue = request(
            self, self.root, b"PUT", self.uri + '/queues/' + self.queue_name)
        self.create_queue_response = self.successResultOf(self.create_queue)

    def test_create_queue(self):
        """
        Test to verify :func:`add queue` on ``PUT /v2.0/<tenant_id>/queues/<queue_name>``
        """
        self.create_queue_body = self.successResultOf(
            treq.json_content(self.create_queue_response))
        self.assertEqual(self.create_queue_response.code, 201)
        self.assertTrue(str(self.create_queue_body), 'null')

    def test_list_queues(self):
        """
        Test to verify :func:`list_queues` on ``GET /v2.0/<tenant_id>/queues``
        """
        list_queues = request(self, self.root, b"GET", self.uri + '/queues')
        list_queues_response = self.successResultOf(list_queues)
        self.assertEqual(list_queues_response.code, 200)

    def test_delete_queue(self):
        """
        Test to verify :func:`del_queue` on ``DELETE /v2.0/<tenant_id>/servers/<queue_name>``
        """
        delete_queue = request(self, self.root, b"DELETE", self.uri + '/queues/' + self.queue_name)
        delete_queue_response = self.successResultOf(delete_queue)
        self.assertEqual(delete_queue_response.code, 204)
        self.assertEqual(self.successResultOf(treq.content(delete_queue_response)), b"")

    def test_post_and_list_messages(self):
        """
        Posting a message to the queue should cause the message to be
        visible to another client.
        """
        (resp, data) = self.successResultOf(
            json_request(self, self.root, b"POST",
                         '{0}/queues/{1}/messages'.format(self.uri, self.queue_name),
                         [{'ttl': 60, 'body': {'text': 'Wow'}}],
                         headers={b'Client-ID': [b'client-1']}))
        self.assertEquals(resp.code, 201)
        self.assertEquals(len(data['resources']), 1)
        (resp, data) = self.successResultOf(
            json_request(self, self.root, b"GET",
                         '{0}/queues/{1}/messages'.format(self.uri, self.queue_name),
                         headers={b'Client-ID': [b'client-2']}))
        self.assertEquals(resp.code, 200)
        self.assertEquals(data['messages'][0]['body']['text'], 'Wow')

    def test_list_messages_nonexisting_queue(self):
        """
        Listing messages for a non-existing queue returns 204.
        """
        resp = self.successResultOf(
            request(self, self.root, b"GET",
                    '{0}/queues/does-not-exist/messages'.format(self.uri, self.queue_name),
                    headers={b'Client-ID': [b'client-2']}))
        self.assertEquals(resp.code, 204)

    def test_post_to_nonexisting_queue(self):
        """
        Attempting to post a message to a non-existing queue returns 404.
        """
        (resp, _) = self.successResultOf(
            json_request(self, self.root, b"POST",
                         '{0}/queues/does-not-exist/messages'.format(self.uri),
                         [{'ttl': 60, 'body': {'text': 'Wow'}}],
                         headers={b'Client-ID': [b'client-1']}))
        self.assertEquals(resp.code, 404)

    def test_same_client_message_is_invisible(self):
        """
        By default, the client does not see messages they themselves posted.
        """
        (resp, data) = self.successResultOf(
            json_request(self, self.root, b"POST",
                         '{0}/queues/{1}/messages'.format(self.uri, self.queue_name),
                         [{'ttl': 60, 'body': {'text': 'Wow'}}],
                         headers={b'Client-ID': [b'client-1']}))
        self.assertEquals(resp.code, 201)
        self.assertEquals(len(data['resources']), 1)
        resp = self.successResultOf(
            request(self, self.root, b"GET",
                    '{0}/queues/{1}/messages'.format(self.uri, self.queue_name),
                    headers={b'Client-ID': [b'client-1']}))
        self.assertEquals(resp.code, 204)

    def test_same_client_message_shows_with_echo(self):
        """
        With echo=true, the client can see messages they posted.
        """
        (resp, data) = self.successResultOf(
            json_request(self, self.root, b"POST",
                         '{0}/queues/{1}/messages'.format(self.uri, self.queue_name),
                         [{'ttl': 60, 'body': {'text': 'Wow'}}],
                         headers={b'Client-ID': [b'client-1']}))
        self.assertEquals(resp.code, 201)
        self.assertEquals(len(data['resources']), 1)
        (resp, data) = self.successResultOf(
            json_request(self, self.root, b"GET",
                         '{0}/queues/{1}/messages?echo=true'.format(
                             self.uri, self.queue_name),
                         headers={b'Client-ID': [b'client-1']}))
        self.assertEquals(resp.code, 200)
        self.assertEquals(data['messages'][0]['body']['text'], 'Wow')

    def test_old_messages_expire(self):
        """
        Messages expire after their TTL.
        """
        (resp, data) = self.successResultOf(
            json_request(self, self.root, b"POST",
                         '{0}/queues/{1}/messages'.format(self.uri, self.queue_name),
                         [{'ttl': 60, 'body': {'text': 'Wow'}}],
                         headers={b'Client-ID': [b'client-1']}))
        self.assertEquals(resp.code, 201)
        self.assertEquals(len(data['resources']), 1)
        self.clock.advance(61)
        resp = self.successResultOf(request(self, self.root, b"GET",
                                            '{0}/queues/{1}/messages?echo=true'.format(
                                                self.uri, self.queue_name),
                                            headers={b'Client-ID': [b'client-2']}))
        self.assertEquals(resp.code, 204)
