import json
import treq

from twisted.trial.unittest import SynchronousTestCase
from twisted.internet.task import Clock

from mimic.core import MimicCore
from mimic.resource import MimicRoot
from mimic.test.helpers import request
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
        self.core = MimicCore(Clock(), [QueueApi()])
        self.root = MimicRoot(self.core).app.resource()
        self.response = request(
            self, self.root, "POST", "/identity/v2.0/tokens",
            json.dumps({
                "auth": {
                    "passwordCredentials": {
                        "username": "testQueue",
                        "password": "testQueuePassword",
                    },
                }
            })
        )
        self.auth_response = self.successResultOf(self.response)
        self.json_body = self.successResultOf(
            treq.json_content(self.auth_response))
        self.uri = self.json_body['access']['serviceCatalog'][0]['endpoints'][0]['publicURL']
        self.queue_name = "test_queue"
        self.create_queue = request(
            self, self.root, "PUT", self.uri + '/queues/' + self.queue_name)
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
        list_queues = request(self, self.root, "GET", self.uri + '/queues')
        list_queues_response = self.successResultOf(list_queues)
        self.assertEqual(list_queues_response.code, 200)

    def test_delete_queue(self):
        """
        Test to verify :func:`del_queue` on ``DELETE /v2.0/<tenant_id>/servers/<queue_name>``
        """
        delete_queue = request(self, self.root, "DELETE", self.uri + '/queues/' + self.queue_name)
        delete_queue_response = self.successResultOf(delete_queue)
        self.assertEqual(delete_queue_response.code, 204)
        self.assertEqual(self.successResultOf(treq.content(delete_queue_response)), b"")
