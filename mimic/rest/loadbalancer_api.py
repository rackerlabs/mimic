"""
Defines add node and delete node from load balancers
"""

import json
from twisted.web.server import Request
from mimic.canned_responses.loadbalancer import (add_node, delete_node, list_nodes)
from mimic.rest.mimicapp import MimicApp
from mimic.canned_responses.mimic_presets import get_presets


Request.defaultContentType = 'application/json'


class LoadBalancerApi(object):

    """
    Rest endpoints for mocked Load balancer api.
    """
    app = MimicApp()

    def __init__(self):
        self.failing_lb_id = get_presets['loadbalancers']['failing_lb_id']
        self.invalid_lb = get_presets['loadbalancers']['invalid_lb']
        self.count = get_presets['loadbalancers']['return_422_on_add_node_count']

    @app.route('/v2/<string:tenant_id>/loadbalancers/<string:lb_id>/nodes', methods=['POST'])
    def add_node_to_load_balancer(self, request, tenant_id, lb_id):
        """
        Return a successful add node response
        """
        if str(lb_id) == self.failing_lb_id:
            if self.count != 0:
                self.count = self.count - 1
                request.setResponseCode(422)
                return json.dumps({'message': "Load Balancer {0} has a status of 'PENDING_UPDATE' \
                    and is considered immutable.".format(lb_id), 'code': 422})
        if str(lb_id) == self.invalid_lb:
            return request.setResponseCode(404)
        content = json.loads(request.content.read())
        node_list = content['nodes']
        request.setResponseCode(200)
        return json.dumps(add_node(node_list, lb_id))

    @app.route('/v2/<string:tenant_id>/loadbalancers/<string:lb_id>/nodes/<string:node_id>',
               methods=['DELETE'])
    def delete_node_from_load_balancer(self, request, tenant_id, lb_id, node_id):
        """
        Returns a 204 response code, for any load balancer created using the mocks
        """
        # if str(lb_id) == failing_lb_id:
        #     request.setResponseCode(422)
        #     return json.dumps({'message': "Load Balancer {0} has a status of 'PENDING_UPDATE' \
        #         and is considered immutable.".format(lb_id), 'code': 422})
        return request.setResponseCode(delete_node(lb_id, node_id))

    @app.route('/v2/<string:tenant_id>/loadbalancers/<string:lb_id>/nodes',
               methods=['GET'])
    def list_nodes_for_load_balancer(self, request, tenant_id, lb_id):
        """
        Returns a 200 response code and list of nodes on the load balancer
        """
        request.setResponseCode(200)
        return json.dumps({"nodes": list_nodes(lb_id)})
