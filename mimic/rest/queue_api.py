"""
API mock for Rackspace Queues.
"""
import json
from uuid import uuid4
from six import text_type

from mimic.imimic import IAPIMock
from twisted.plugin import IPlugin
from mimic.canned_responses.queue import (
    add_queue, list_queues, delete_queue)

from mimic.catalog import Entry
from mimic.catalog import Endpoint
from mimic.rest.mimicapp import MimicApp
from zope.interface import implementer
from random import randrange


@implementer(IAPIMock, IPlugin)
class QueueApi(object):
    """
    API mock for Queues.
    """

    def resource_for_region(self, uri_prefix):
        """
        Get an :obj:`twisted.web.iweb.IResource` for the given URI prefix;
        implement :obj:`IAPIMock`.
        """
        return QueueApiRoutes(uri_prefix).app.resource()

    def catalog_entries(self, tenant_id):
        """
        Catalog entry for Queues endpoints.
        """      
        return [
            Entry(tenant_id, "rax:queues", "cloudQueues", [
                Endpoint(tenant_id, "ORD", text_type(uuid4()), prefix="v1")
            ])
            # ,
            # Entry(tenant_id, "rax:queues", "cloudQueues", [
            #     Endpoint(tenant_id, "SYD", text_type(uuid4()), prefix="v1"),
            # ]),
            # Entry(tenant_id, "rax:queues", "cloudQueues", [
            #     Endpoint(tenant_id, "IAD", text_type(uuid4()), prefix="v1"),
            # ]),
            # Entry(tenant_id, "rax:queues", "cloudQueues", [
            #     Endpoint(tenant_id, "HKG", text_type(uuid4()), prefix="v1"),
            # ]),
            # Entry(tenant_id, "rax:queues", "cloudQueues", [
            #     Endpoint(tenant_id, "DFW", text_type(uuid4()), prefix="v1"),
            # ])
        ]


class QueueApiRoutes(object):
    """
    Klein routes for queue API methods.
    """

    app = MimicApp()

    def __init__(self, uri_prefix):
        """
        Create a queue region with a given URI prefix (used for generating URIs
        to queues).
        """
        self.uri_prefix = uri_prefix
     
    @app.route("/v1/<string:tenant_id>/queues/<string:queue_name>", methods=['PUT'])
    def create_queue(self, request, tenant_id, queue_name):
        """
        Api call to create and save queue. HTTP status code of 201.
        """  
        queue_id = randrange(99999)  
        response_data = add_queue(queue_id, queue_name, tenant_id)
        request.setResponseCode(response_data[1])

    @app.route("/v1/<string:tenant_id>/queues", methods=['GET'])
    def list_queues(self, request, tenant_id):
        """
        Api call to get a list of queues. HTTP status code of 200
        """
        response_data = list_queues(tenant_id)
        request.setResponseCode(response_data[1])
        return json.dumps(response_data[0])

    @app.route("/v1/<string:tenant_id>/queues/<string:queue_name>", methods=['DELETE'])
    def del_queue(self, request, tenant_id, queue_name):
        """
        Api call to delete a queue. HTTP status code of 201
        """
        response_data = delete_queue(queue_name)
        request.setResponseCode(response_data[1])
        return json.dumps(response_data[0])
