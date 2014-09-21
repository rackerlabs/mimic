"""
Defines add node and delete node from load balancers
"""

import json
from uuid import uuid4
from six import text_type
from zope.interface import implementer
from twisted.web.server import Request
from twisted.plugin import IPlugin
from mimic.canned_responses.loadbalancer import (
    add_load_balancer, del_load_balancer, list_load_balancers,
    add_node, delete_node, list_nodes, get_load_balancers, get_nodes)
from mimic.rest.mimicapp import MimicApp
from mimic.canned_responses.mimic_presets import get_presets
from mimic.imimic import IAPIMock
from mimic.catalog import Entry
from mimic.catalog import Endpoint
from random import randrange


Request.defaultContentType = 'application/json'


@implementer(IAPIMock, IPlugin)
class LoadBalancerApi(object):
    """
    Rest endpoints for mocked Load balancer api.
    """

    def catalog_entries(self, tenant_id):
        """
        Cloud load balancer entries.
        """
        # TODO: actually add some entries so load balancers show up in the
        # service catalog.
        return [
            Entry(tenant_id, "rax:load-balancer", "cloudLoadBalancers",
                  [
                      Endpoint(tenant_id, "ORD", text_type(uuid4()),
                               prefix="v2")
                  ])
        ]

    def resource_for_region(self, region, uri_prefix, session_store):
        """
        Get an :obj:`twisted.web.iweb.IResource` for the given URI prefix;
        implement :obj:`IAPIMock`.
        """
        # TODO: unit test
        return LoadBalancerApiRoutes(uri_prefix).app.resource()


class LoadBalancerApiRoutes(object):
    """
    Klein routes for load balancer API methods.
    """

    app = MimicApp()

    def __init__(self, uri_prefix):
        """
        Fetches the load balancer id for a failure, invalid scenarios and
        the count on the number of time 422 should be returned on add node.
        """
        self.uri_prefix = uri_prefix

    @app.route('/v2/<string:tenant_id>/loadbalancers', methods=['POST'])
    def add_load_balancer(self, request, tenant_id):
        """
        Creates a load balancer and adds it to the lb_cache.
        Returns the newly created load balancer with response code 202
        """
        lb_id = randrange(99999)
        content = json.loads(request.content.read())
        response_data = add_load_balancer(tenant_id, content['loadBalancer'], lb_id)
        request.setResponseCode(response_data[1])
        return json.dumps(response_data[0])

    @app.route('/v2/<string:tenant_id>/loadbalancers/<int:lb_id>', methods=['GET'])
    def get_load_balancers(self, request, tenant_id, lb_id):
        """
        Returns a list of all load balancers created using mimic with response code 200
        """
        response_data = get_load_balancers(lb_id)
        request.setResponseCode(response_data[1])
        return json.dumps(response_data[0])

    @app.route('/v2/<string:tenant_id>/loadbalancers', methods=['GET'])
    def list_load_balancers(self, request, tenant_id):
        """
        Returns a list of all load balancers created using mimic with response code 200
        """
        response_data = list_load_balancers(tenant_id)
        request.setResponseCode(response_data[1])
        return json.dumps(response_data[0])

    @app.route('/v2/<string:tenant_id>/loadbalancers/<int:lb_id>', methods=['DELETE'])
    def delete_load_balancer(self, request, tenant_id, lb_id):
        """
        Creates a load balancer and adds it to the lb_cache.
        Returns the newly created load balancer with response code 200
        """
        response_data = del_load_balancer(lb_id)
        request.setResponseCode(response_data[1])
        return json.dumps(response_data[0])

    @app.route('/v2/<string:tenant_id>/loadbalancers/<int:lb_id>/nodes', methods=['POST'])
    def add_node_to_load_balancer(self, request, tenant_id, lb_id):
        """
        Return a successful add node response with code 200
        """
        content = json.loads(request.content.read())
        node_list = content['nodes']
        response_data = add_node(node_list, lb_id)
        request.setResponseCode(response_data[1])
        return json.dumps(response_data[0])

    @app.route('/v2/<string:tenant_id>/loadbalancers/<int:lb_id>/nodes/<int:node_id>',
               methods=['GET'])
    def get_nodes(self, request, tenant_id, lb_id, node_id):
        """
        Returns a 200 response code and list of nodes on the load balancer
        """
        response_data = get_nodes(lb_id, node_id)
        request.setResponseCode(response_data[1])
        return json.dumps(response_data[0])

    @app.route('/v2/<string:tenant_id>/loadbalancers/<int:lb_id>/nodes/<int:node_id>',
               methods=['DELETE'])
    def delete_node_from_load_balancer(self, request, tenant_id, lb_id, node_id):
        """
        Returns a 204 response code, for any load balancer created using the mocks
        """
        response_data = delete_node(lb_id, node_id)
        request.setResponseCode(response_data[1])
        return json.dumps(response_data[0])

    @app.route('/v2/<string:tenant_id>/loadbalancers/<int:lb_id>/nodes',
               methods=['GET'])
    def list_nodes_for_load_balancer(self, request, tenant_id, lb_id):
        """
        Returns a 200 response code and list of nodes on the load balancer
        """
        response_data = list_nodes(lb_id)
        request.setResponseCode(response_data[1])
        return json.dumps(response_data[0])
