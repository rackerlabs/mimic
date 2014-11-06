"""
Unit tests for the Rackspace RackConnect V3 API.
"""

from twisted.trial.unittest import SynchronousTestCase
from mimic.test.fixtures import APIMockHelper
from mimic.rest.rackconnect_v3_api import (
    LoadBalancerPool, LoadBalancerPoolNode, RackConnectV3,
    lb_pool_attrs)
from mimic.util.helper import attribute_names
from mimic.test.helpers import json_request, request_with_content


class LoadBalancerObjectTests(SynchronousTestCase):
    """
    Tests for :class:`LoadBalancerPool` and :class:`LoadBalancerPoolNode`
    """
    def setUp(self):
        self.pool = LoadBalancerPool(id="pool_id", virtual_ip="10.0.0.1")
        for i in range(10):
            self.pool.nodes.append(
                LoadBalancerPoolNode(id="node_{0}".format(i),
                                     created="2000-01-01T00:00:00Z",
                                     load_balancer_pool=self.pool,
                                     updated=None,
                                     cloud_server="server_{0}".format(i)))

    def test_LBPoolNode_short_json(self):
        """
        Valid JSON response (as would be displayed when listing nodes) is
        produced by :func:`LoadBalancerPoolNode.short_json`
        """
        self.assertEqual(
            {
                "id": "node_0",
                "created": "2000-01-01T00:00:00Z",
                "updated": None,
                "load_balancer_pool": {
                    "id": "pool_id"
                },
                "cloud_server": {
                    "id": "server_0"
                },
                "status": "ACTIVE",
                "status_detail": None
            },
            self.pool.nodes[0].short_json())

    def test_LBPool_short_json(self):
        """
        Valid JSON response (as would be displayed when listing pools or
        getting pool details) is produced by :func:`LoadBalancerPool.as_json`.
        """
        self.assertEqual(
            {
                "id": "pool_id",
                "name": "default",
                "node_counts": {
                    "cloud_servers": 10,
                    "external": 0,
                    "total": 10
                },
                "port": 80,
                "virtual_ip": "10.0.0.1",
                "status": "ACTIVE",
                "status_detail": None
            },
            self.pool.as_json())

    def test_LBPool_find_nodes_by_id(self):
        """
        A node can be retrieved by its ID.
        """
        self.assertIs(self.pool.nodes[5], self.pool.node_by_id("node_5"))

    def test_LBPool_find_nodes_by_server_id(self):
        """
        A node can be retrieved by its cloud server ID.
        """
        self.assertIs(self.pool.nodes[3],
                      self.pool.node_by_cloud_server("server_3"))


class LoadbalancerPoolAPITests(SynchronousTestCase):
    """
    Tests for the LoadBalancerPool API
    """

    def setUp(self):
        """
        Create a :obj:`MimicCore` with :obj:`RackConnectV3` as the only plugin
        """
        self.helper = APIMockHelper(self, [RackConnectV3()])

    def test_list_pools_default_one(self):
        """
        Verify the JSON response from listing all load balancer pools.
        By default, all tenants have one load balancer pool.
        """
        response, response_json = self.successResultOf(
            json_request(self, self.helper.root, "GET",
                         self.helper.uri + "/load_balancer_pools"))
        self.assertEqual(200, response.code)
        self.assertEqual(['application/json'],
                         response.headers.getRawHeaders('content-type'))
        self.assertEqual(1, len(response_json))

        pool_json = response_json[0]
        # has the right JSON
        self.assertTrue(all(
            attr in pool_json for attr in attribute_names(lb_pool_attrs)
            if attr != "nodes"))
        # Generated values
        self.assertTrue(all(
            pool_json.get(attr) for attr in attribute_names(lb_pool_attrs)
            if attr not in ("nodes", "status_detail")))

        self.assertEqual(
            {
                "cloud_servers": 0,
                "external": 0,
                "total": 0
            },
            pool_json['node_counts'],
            "Pool should start off with no members.")

    def test_different_regions_same_tenant_different_pools(self):
        """
        The same tenant has different pools in different regions.
        """
        self.helper = APIMockHelper(self,
                                    [RackConnectV3(regions=["ORD", "DFW"])])

        responses = [
            self.successResultOf(json_request(
                self, self.helper.root, "GET",
                self.helper.nth_endpoint_public(i) + "/load_balancer_pools"))
            for i in range(2)]

        nodes = [response[-1][0] for response in responses]

        self.assertNotEqual(nodes[0]['id'], nodes[1]['id'])

    def test_get_pool_on_success(self):
        """
        Validate the JSON response of getting a single pool on an existing
        pool.
        """
        _, pool_list_json = self.successResultOf(
            json_request(self, self.helper.root, "GET",
                         self.helper.uri + "/load_balancer_pools"))
        pool = pool_list_json[0]

        pool_details_response, pool_details_json = self.successResultOf(
            json_request(self, self.helper.root, "GET",
                         self.helper.uri + "/load_balancer_pools/" +
                         pool['id']))

        self.assertEqual(200, pool_details_response.code)
        self.assertEqual(
            ['application/json'],
            pool_details_response.headers.getRawHeaders('content-type'))
        self.assertEqual(pool, pool_details_json)

    def test_get_pool_404_invalid_pool(self):
        """
        Getting pool on a non-existant pool returns a 404.

        TODO: test the response body if one is returned
        """
        response, _ = self.successResultOf(
            request_with_content(self, self.helper.root, "GET",
                                 self.helper.uri + "/load_balancer_pools/x"))

        self.assertEqual(404, response.code)
