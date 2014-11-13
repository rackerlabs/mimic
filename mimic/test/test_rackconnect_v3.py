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
        """
        response, content = self.successResultOf(
            request_with_content(self, self.helper.root, "GET",
                                 self.helper.uri + "/load_balancer_pools/X"))

        self.assertEqual(404, response.code)
        self.assertEqual("Load Balancer Pool X does not exist", content)


class LoadbalancerPoolNodesAPITests(SynchronousTestCase):
    """
    Tests for the LoadBalancerPool API for getting and updating nodes
    """
    def setUp(self):
        """
        Create a :obj:`MimicCore` with :obj:`RackConnectV3` as the only plugin
        """
        self.helper = APIMockHelper(self, [RackConnectV3()])
        _, pool_list_json = self.successResultOf(
            json_request(self, self.helper.root, "GET",
                         self.helper.uri + "/load_balancer_pools"))
        self.pool_id = pool_list_json[0]['id']

    def request_with_content(self, method, relative_uri, **kwargs):
        """
        Helper function that makes a request and gets the non-json content.
        """
        return request_with_content(self, self.helper.root, method,
                                    self.helper.uri + relative_uri, **kwargs)

    def json_request(self, method, relative_uri, **kwargs):
        """
        Helper function that makes a request and gets the json content.
        """
        return json_request(self, self.helper.root, method,
                            self.helper.uri + relative_uri, **kwargs)

    def test_get_pool_404_invalid_pool_nodes(self):
        """
        Getting nodes on a non-existant pool returns a 404.
        """
        response, content = self.successResultOf(self.request_with_content(
            "GET", "/load_balancer_pools/X/nodes".format(self.pool_id)))

        self.assertEqual(404, response.code)
        self.assertEqual("Load Balancer Pool X does not exist", content)

    def test_get_pool_nodes_empty(self):
        """
        Getting nodes for an empty existing load balancer returns a 200 with
        no nodes
        """
        response, json_content = self.successResultOf(self.json_request(
            "GET", "/load_balancer_pools/{0}/nodes".format(self.pool_id)))
        self.assertEqual(200, response.code)
        self.assertEqual(json_content, [])

    def _check_added_nodes_result(self, seconds, add_json, results_json):
        """
        Helper function to check that the results reflect the added nodes
        """
        self.assertEqual(len(add_json), len(results_json))

        # Can't construct the whole thing, because the IDs are random, so
        # compare some parts
        for node_blob in results_json:
            can_be_compared = node_blob.copy()

            the_id = can_be_compared.pop('id')
            self.assertTrue(isinstance(the_id, basestring))

            can_be_compared.pop('cloud_server', None)
            self.assertEqual({
                "created": "1970-01-01T00:00:{0:02}Z".format(seconds),
                "load_balancer_pool": {"id": self.pool_id},
                "status": "ADDING",
                "status_detail": None,
                "updated": None
            }, can_be_compared)

        result_server_bits = sorted([blob['cloud_server']
                                    for blob in results_json])
        expected_server_bits = sorted([blob['cloud_server']
                                       for blob in add_json])

        self.assertEqual(expected_server_bits, result_server_bits)

    def test_add_bulk_pool_nodes_success_response(self):
        """
        Adding multiple pool nodes successfully results in a 200 with the
        correct node detail responses
        """
        self.helper.clock.advance(60)
        add_data = [
            {"cloud_server": {"id": "12345"},
             "load_balancer_pool": self.pool_id},
            {"cloud_server": {"id": "54321"},
             "load_balancer_pool": self.pool_id}
        ]
        response, resp_json = self.successResultOf(self.json_request(
            "POST", "/load_balancer_pools/{0}/nodes".format(self.pool_id),
            body=add_data
        ))
        self.assertEqual(200, response.code)
        self._check_added_nodes_result(60, add_data, resp_json)

    def test_add_bulk_pool_nodes_then_list(self):
        """
        Adding multiple pool nodes successfully means that the next time nodes
        are listed those nodes are listed.
        """
        self.helper.clock.advance(60)
        add_data = [
            {"cloud_server": {"id": "12345"},
             "load_balancer_pool": self.pool_id},
            {"cloud_server": {"id": "54321"},
             "load_balancer_pool": self.pool_id}
        ]
        add_response, _ = self.successResultOf(self.json_request(
            "POST", "/load_balancer_pools/{0}/nodes".format(self.pool_id),
            body=add_data
        ))
        self.assertEqual(200, add_response.code)

        _, list_json = self.successResultOf(self.json_request(
            "GET", "/load_balancer_pools/{0}/nodes".format(self.pool_id)))
        self._check_added_nodes_result(60, add_data, list_json)

    def test_remove_bulk_pool_nodes_success(self):
        """
        Removing multiple pool nodes successfully results in a 204 with the
        correct node detail responses
        """
        self.helper.clock.advance(60)
        server_data = [
            {"cloud_server": {"id": "12345"},
             "load_balancer_pool": self.pool_id},
            {"cloud_server": {"id": "54321"},
             "load_balancer_pool": self.pool_id}
        ]

        # add first
        self.successResultOf(self.json_request(
            "POST", "/load_balancer_pools/{0}/nodes".format(self.pool_id),
            body=server_data
        ))

        # ensure there are 2
        _, list_json = self.successResultOf(self.json_request(
            "GET", "/load_balancer_pools/{0}/nodes".format(self.pool_id)))
        self.assertEqual(2, len(list_json))

        # delete
        response, _ = self.successResultOf(self.json_request(
            "DELETE", "/load_balancer_pools/{0}/nodes".format(self.pool_id),
            body=server_data))
        self.assertEqual(204, response.code)

        # ensure there are 0
        _, list_json = self.successResultOf(self.json_request(
            "GET", "/load_balancer_pools/{0}/nodes".format(self.pool_id)))
        self.assertEqual(0, len(list_json))

    def test_get_pool_nodes_details_unimplemented(self):
        """
        Getting pool nodes details is currently unimplemented
        """
        response, content = self.successResultOf(self.request_with_content(
            "GET",
            "/load_balancer_pools/{0}/nodes/details".format(self.pool_id)))
        self.assertEqual(501, response.code)

    def test_add_pool_node_unimplemented(self):
        """
        Adding a single pool node is currently unimplemented
        """
        response, content = self.successResultOf(self.json_content(
            "POST", "/load_balancer_pools/{0}/nodes".format(self.pool_id),
            body={
                "cloud_server": {"id": "d95ae0c4-6ab8-4873-b82f-f8433840cff2"}
            }))
        self.assertEqual(501, response.code)

    def test_get_pool_node_unimplemented(self):
        """
        Getting information a single pool node is currently unimplemented
        """
        response, content = self.successResultOf(self.request_with_content(
            "GET", "/load_balancer_pools/{0}/nodes/1".format(self.pool_id)
            ))
        self.assertEqual(501, response.code)

    def test_remove_pool_node_unimplemented(self):
        """
        Removing a single pool node is currently unimplemented
        """
        response, content = self.successResultOf(self.request_with_content(
            "DELETE", "/load_balancer_pools/{0}/nodes/1".format(self.pool_id)
            ))
        self.assertEqual(501, response.code)

    def test_get_pool_node_details_unimplemented(self):
        """
        Getting detailed information on a single pool node is currently
        unimplemented
        """
        response, content = self.successResultOf(self.request_with_content(
            "GET",
            "/load_balancer_pools/{0}/nodes/1/details".format(self.pool_id)
            ))
        self.assertEqual(501, response.code)
