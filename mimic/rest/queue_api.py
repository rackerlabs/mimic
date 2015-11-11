"""
API mock for Rackspace Queues.
"""

from __future__ import absolute_import, division, unicode_literals

import json
import collections
from uuid import uuid4
from six import text_type

from mimic.imimic import IAPIMock
from twisted.plugin import IPlugin

from mimic.catalog import Entry
from mimic.catalog import Endpoint
from mimic.model.queue_objects import QueueCollection
from mimic.rest.mimicapp import MimicApp
from zope.interface import implementer


@implementer(IAPIMock, IPlugin)
class QueueApi(object):
    """
    API mock for Queues.
    """
    def __init__(self, regions=["ORD", "DFW", "IAD"]):
        """
        Create a QueueApi with an empty region cache
        """
        self._regions = regions

    def resource_for_region(self, uri_prefix, region, session_store):
        """
        Get an :obj:`twisted.web.iweb.IResource` for the given URI prefix;
        implement :obj:`IAPIMock`.
        """
        return (QueueApiRoutes(self, uri_prefix, session_store, region).app.resource())

    def catalog_entries(self, tenant_id):
        """
        List catalog entries for the Nova API.
        """
        return [
            Entry(
                tenant_id, "rax:queues", "cloudQueues",
                [
                    Endpoint(tenant_id, region, text_type(uuid4()),
                             prefix="v1")
                    for region in self._regions
                ]
            )
        ]


class QueueApiRoutes(object):
    """
    Klein routes for queue API methods.
    """

    app = MimicApp()

    def __init__(self, api_mock, uri_prefix, session_store, queue_name):
        """
        Create a queue region with a given URI prefix (used for generating URIs
        to queues).
        """
        self.uri_prefix = uri_prefix
        self._api_mock = api_mock
        self._session_store = session_store
        self._queue_name = queue_name

    def _queue_collection(self, tenant_id):
        """
        Get the given queue-cache object for the given tenant, creating one if
        there isn't one.
        """
        return (self._session_store.session_for_tenant_id(tenant_id)
                .data_for_api(self._api_mock,
                              lambda: collections.defaultdict(QueueCollection))
                [self._queue_name])

    @app.route("/v1/<string:tenant_id>/queues/<string:queue_name>", methods=['PUT'])
    def create_queue(self, request, tenant_id, queue_name):
        """
        Api call to create and save queue. HTTP status code of 201.
        """
        q_collection = self._queue_collection(tenant_id)
        (response_body, response_code) = q_collection.add_queue(queue_name)
        request.setResponseCode(response_code)
        return json.dumps(response_body)

    @app.route("/v1/<string:tenant_id>/queues", methods=['GET'])
    def list_queues(self, request, tenant_id):
        """
        Api call to get a list of queues. HTTP status code of 200
        """
        q_collection = self._queue_collection(tenant_id)
        (response_body, response_code) = q_collection.list_queues()
        request.setResponseCode(response_code)
        return json.dumps(response_body)

    @app.route("/v1/<string:tenant_id>/queues/<string:queue_name>", methods=['DELETE'])
    def del_queue(self, request, tenant_id, queue_name):
        """
        Api call to delete a queue. HTTP status code of 201
        """
        q_collection = self._queue_collection(tenant_id)
        (response_body, response_code) = q_collection.delete_queue(queue_name)
        request.setResponseCode(response_code)
        return json.dumps(response_body)
