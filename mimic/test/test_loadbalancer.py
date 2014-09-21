"""
Unit tests for the
"""

import json
import treq

from twisted.trial.unittest import SynchronousTestCase
from mimic.canned_responses.loadbalancer import load_balancer_example
from mimic.test.fixtures import APIMockHelper
from mimic.rest.loadbalancer_api import LoadBalancerApi
from mimic.test.helpers import request


class ResponseGenerationTests(SynchronousTestCase):
    """
    Tests for Loud Balancer response generation.
    """

    def test_canned_loadbalancer(self):
        """
        Test that the canned load balancer response is returned as expected.
        """

        expect_lb_name = "cannedTestLB"
        expect_lb_protocol = "protocol"
        expect_lb_port = 70
        expect_lb_algorithm = "RANDOM"
        expect_lb_httpsRedirect = "redirect"
        expect_lb_halfClosed = "halfClosed"
        expect_lb_connectionLogging = {"enabled": True}
        expect_lb_contentCaching = True
        expect_lb_timeout = 35

        input_lb_info = {"name": expect_lb_name,
                         "protocol": expect_lb_protocol,
                         "port": expect_lb_port,
                         "timeout": expect_lb_timeout,
                         "httpsRedirect": expect_lb_httpsRedirect,
                         "halfClosed": expect_lb_halfClosed,
                         "connectionLogging": expect_lb_connectionLogging,
                         "contentCaching": expect_lb_contentCaching}

        input_lb_id = "13579"
        input_lb_time = "current_time"
        input_lb_status = "ACTIVE"

        actual = load_balancer_example(input_lb_info, input_lb_id, input_lb_status,
                                       lambda: input_lb_time)

        lb_example = {"name": expect_lb_name,
                      "id": input_lb_id,
                      "protocol": expect_lb_protocol,
                      "port": expect_lb_port,
                      "algorithm": expect_lb_algorithm,
                      "status": input_lb_status,
                      "cluster": {"name": "test-cluster"},
                      "timeout": expect_lb_timeout,
                      "created": {"time": input_lb_time},
                      "virtualIps": [{"address": "127.0.0.1",
                                     "id": 1111, "type": "PUBLIC", "ipVersion": "IPV4"},
                                     {"address": "0000:0000:0000:0000:1111:111b:0000:0000",
                                      "id": 1111,
                                      "type": "PUBLIC",
                                      "ipVersion": "IPV6"}],
                      "sourceAddresses": {"ipv6Public": "0000:0001:0002::00/00",
                                          "ipv4Servicenet": "127.0.0.1",
                                          "ipv4Public": "127.0.0.1"},
                      "httpsRedirect": expect_lb_httpsRedirect,
                      "updated": {"time": input_lb_time},
                      "halfClosed": expect_lb_halfClosed,
                      "connectionLogging": expect_lb_connectionLogging,
                      "contentCaching": {"enabled": False}}

        self.assertEqual(actual, lb_example)


class LoadbalancerAPITests(SynchronousTestCase):
    """
    Tests for the Loadbalancer plugin API
    """

    def setUp(self):
        """
        Create a :obj:`MimicCore` with :obj:`LoadBalancerApi` as the only plugin
        """
        fixture = APIMockHelper(self, [LoadBalancerApi()])
        self.root = fixture.root
        self.uri = fixture.uri

    def _create_loadbalancer(self, name=None):
        """
        Helper method to create a load balancer and return the lb_id
        """
        create_lb = request(
            self, self.root, "POST", self.uri + '/loadbalancers',
            json.dumps({
                "loadBalancer": {
                    "name": name or "test_lb",
                    "protocol": "HTTP",
                    "virtualIps": [{"type": "PUBLIC"}]
                }
            })
        )
        create_lb_response = self.successResultOf(create_lb)
        create_lb_response_body = self.successResultOf(treq.json_content(create_lb_response))
        return create_lb_response_body['loadBalancer']['id']

    def test_add_load_balancer(self):
        """
        Test to verify :func:`add_load_balancer` on ``POST /v1.0/<tenant_id>/loadbalancers``
        """
        lb_name = 'mimic_lb'
        create_lb = request(
            self, self.root, "POST", self.uri + '/loadbalancers',
            json.dumps({
                "loadBalancer": {
                    "name": lb_name,
                    "protocol": "HTTP",
                    "virtualIps": [{"type": "PUBLIC"}]
                }
            })
        )
        create_lb_response = self.successResultOf(create_lb)
        create_lb_response_body = self.successResultOf(treq.json_content(create_lb_response))
        self.assertEqual(create_lb_response.code, 202)
        self.assertEqual(create_lb_response_body['loadBalancer']['name'], lb_name)

    def test_add_load_balancer_with_nodes(self):
        """
        Test to verify :func:`add_load_balancer` on ``POST /v1.0/<tenant_id>/loadbalancers``,
        with nodes
        """
        lb_name = 'mimic_lb'
        create_lb = request(
            self, self.root, "POST", self.uri + '/loadbalancers',
            json.dumps({
                "loadBalancer": {
                    "name": lb_name,
                    "protocol": "HTTP",
                    "virtualIps": [{"type": "PUBLIC"}],
                    "nodes": [{"address": "127.0.0.2",
                               "port": 80,
                               "condition": "ENABLED",
                               "type": "PRIMARY"},
                              {"address": "127.0.0.0",
                               "port": 80,
                               "condition": "ENABLED",
                               "type": "SECONDARY"}]
                }
            })
        )
        create_lb_response = self.successResultOf(create_lb)
        create_lb_response_body = self.successResultOf(treq.json_content(create_lb_response))
        self.assertEqual(create_lb_response.code, 202)
        self.assertEqual(len(create_lb_response_body['loadBalancer']['nodes']), 2)

    def test_list_loadbalancers(self):
        """
        Test to verify :func:`list_load_balancers` with on ``GET /v1.0/<tenant_id>/loadbalancers``
        Create two load balancers, then list them and verify the ids
        """
        test1_id = self._create_loadbalancer('test1')
        test2_id = self._create_loadbalancer('test2')
        list_lb = request(self, self.root, "GET", self.uri + '/loadbalancers')
        list_lb_response = self.successResultOf(list_lb)
        list_lb_response_body = self.successResultOf(treq.json_content(list_lb_response))
        self.assertEqual(list_lb_response.code, 200)
        self.assertEqual(len(list_lb_response_body['loadBalancers']), 2)
        self.assertTrue(list_lb_response_body['loadBalancers'][0]['id'] in [test1_id, test2_id])
        self.assertTrue(list_lb_response_body['loadBalancers'][1]['id'] in [test1_id, test2_id])
        self.assertTrue(list_lb_response_body['loadBalancers'][0]['id'] !=
                        list_lb_response_body['loadBalancers'][1]['id'])

    def test_delete_loadbalancer(self):
        """
        Test to verify :func:`delete_load_balancer` with on
        ``DELETE /v1.0/<tenant_id>/loadbalancers/<lb_id>``
        Create two load balancers, then list them and verify the ids
        """
        # These will fail if the servers weren't created
        test1_id = self._create_loadbalancer('test1')
        test2_id = self._create_loadbalancer('test2')
        delete_lb = request(self, self.root, 'DELETE', self.uri + '/loadbalancers/' + str(test1_id))
        del_lb_response = self.successResultOf(delete_lb)
        # This response code does not match the Rackspace documentation which specifies a 200 response
        # See comment: http://bit.ly/1AVHs3v
        self.assertEqual(del_lb_response.code, 202)
        # List lb to make sure the correct lb is gone and the other remains
        list_lb = request(self, self.root, "GET", self.uri + '/loadbalancers')
        list_lb_response = self.successResultOf(list_lb)
        list_lb_response_body = self.successResultOf(treq.json_content(list_lb_response))
        self.assertTrue(len(list_lb_response_body['loadBalancers']), 1)
        self.assertTrue(list_lb_response_body['loadBalancers'][0]['id'] == test2_id)

    def test_get_loadbalancer(self):
        """
        Test to verify :func:`get_load_balancers` with on
        ``GET /v1.0/<tenant_id>/loadbalancers\<loadbalancer_id``
        """
        lb_id = self._create_loadbalancer()
        get_lb = request(self, self.root, "GET", self.uri + '/loadbalancers/' + str(lb_id))
        get_lb_response = self.successResultOf(get_lb)
        get_lb_response_body = self.successResultOf(treq.json_content(get_lb_response))
        self.assertEqual(get_lb_response.code, 200)
        self.assertEqual(get_lb_response_body['loadBalancer']['id'], lb_id)

    def test_get_non_existant_loadbalancer(self):
        """
        Test to verify :func:`get_load_balancers` for a non existant load balancer id.
        """
        get_lb = request(self, self.root, "GET", self.uri + '/loadbalancers/123')
        get_lb_response = self.successResultOf(get_lb)
        self.assertEqual(get_lb_response.code, 404)

    def test_delete_non_existant_loadbalancer(self):
        """
        Test to verify :func:`delete_load_balancers` for a non existant load balancer.
        """
        delete_lb = request(self, self.root, 'DELETE', self.uri + '/loadbalancers/123')
        delete_lb_response = self.successResultOf(delete_lb)
        self.assertEqual(delete_lb_response.code, 404)

    def test_list_loadbalancers_when_none_exist(self):
        """
        Test to verify :func:`list_load_balancers` when no loadbalancers exist.
        """
        list_lb = request(self, self.root, 'GET', self.uri + '/loadbalancers')
        list_lb_response = self.successResultOf(list_lb)
        self.assertEqual(list_lb_response.code, 200)
        list_lb_response_body = self.successResultOf(treq.json_content(list_lb_response))
        self.assertEqual(list_lb_response_body, {"loadBalancers": []})


class LoadbalancerNodeAPITests(SynchronousTestCase):
    """
    Tests for the Loadbalancer plugin API for CRUD for nodes.
    """

    def setUp(self):
        """
        Create a :obj:`MimicCore` with :obj:`LoadBalancerApi` as the only plugin.
        And create a load balancer and add nodes to the load balancer.
        """
        fixture = APIMockHelper(self, [LoadBalancerApi()])
        self.root = fixture.root
        self.uri = fixture.uri
        create_lb = request(
            self, self.root, "POST", self.uri + '/loadbalancers',
            json.dumps({
                "loadBalancer": {
                    "name": "test_lb",
                    "protocol": "HTTP",
                    "virtualIps": [{"type": "PUBLIC"}]
                }
            })
        )
        create_lb_response = self.successResultOf(create_lb)
        self.create_lb_response_body = self.successResultOf(treq.json_content(
                                                            create_lb_response))
        create_node = request(
            self, self.root, "POST", self.uri + '/loadbalancers/' +
            str(self.create_lb_response_body["loadBalancer"]["id"]) + '/nodes',
            json.dumps({"nodes": [{"address": "127.0.0.1",
                                   "port": 80,
                                   "condition": "ENABLED",
                                   "type": "PRIMARY",
                                   "weight": 10}]})
        )
        self.create_node_response = self.successResultOf(create_node)
        self.create_node_response_body = self.successResultOf(treq.json_content(
                                                              self.create_node_response))
        self.node = self.create_node_response_body["nodes"]

    def test_add_node_to_loadbalancer(self):
        """
        Test to verify :func: `add_node` create a node successfully.
        """
        self.assertEqual(self.create_node_response.code, 200)
        self.assertEqual(len(self.create_node_response_body["nodes"]), 1)
        # verify that the node has all the attributes
        node1 = self.create_node_response_body["nodes"][0]
        self.assertEqual(node1["status"], "ONLINE")
        self.assertEqual(node1["port"], 80)
        self.assertEqual(node1["type"], "PRIMARY")
        self.assertTrue(node1["id"])
        self.assertEqual(node1["address"], "127.0.0.1")
        self.assertEqual(node1["condition"], "ENABLED")
        self.assertEqual(node1["weight"], 10)

    def test_add_multiple_nodes(self):
        """
        Test to verify :func: `add_node` creates multiple node successfully.
        """
        create_multiple_nodes = request(
            self, self.root, "POST", self.uri + '/loadbalancers/' +
            str(self.create_lb_response_body["loadBalancer"]["id"]) + '/nodes',
            json.dumps({"nodes": [{"address": "127.0.0.2",
                                   "port": 80,
                                   "condition": "ENABLED",
                                   "type": "PRIMARY"},
                                  {"address": "127.0.0.0",
                                   "port": 80,
                                   "condition": "ENABLED",
                                   "type": "SECONDARY"}]})
        )
        create_node_response = self.successResultOf(create_multiple_nodes)
        create_node_response_body = self.successResultOf(treq.json_content(
                                                         create_node_response))
        self.assertEqual(create_node_response.code, 200)
        self.assertEqual(len(create_node_response_body["nodes"]), 2)

    def test_add_duplicate_node(self):
        """
        Test to verify :func: `add_node` does not allow creation of duplicate nodes.
        """
        create_duplicate_nodes = request(
            self, self.root, "POST", self.uri + '/loadbalancers/' +
            str(self.create_lb_response_body["loadBalancer"]["id"]) + '/nodes',
            json.dumps({"nodes": [{"address": "127.0.0.1",
                                   "port": 80,
                                   "condition": "ENABLED",
                                   "type": "PRIMARY"}]})
        )
        create_node_response = self.successResultOf(create_duplicate_nodes)
        self.assertEqual(create_node_response.code, 413)

    def test_add_node_to_non_existant_loadbalancer(self):
        """
        Test to verify :func: `add_node` does not allow creation of nodes
        on non existant load balancers.
        """
        create_duplicate_nodes = request(
            self, self.root, "POST", self.uri + '/loadbalancers/123/nodes',
            json.dumps({"nodes": [{"address": "127.0.0.1",
                                   "port": 80,
                                   "condition": "ENABLED",
                                   "type": "PRIMARY"}]})
        )
        create_node_response = self.successResultOf(create_duplicate_nodes)
        self.assertEqual(create_node_response.code, 404)

    def test_list_nodes_on_loadbalancer(self):
        """
        Test to verify :func: `list_node` lists the nodes on the loadbalancer.
        """
        list_nodes = request(
            self, self.root, "GET", self.uri + '/loadbalancers/' +
            str(self.create_lb_response_body["loadBalancer"]["id"]) + '/nodes')
        list_nodes_response = self.successResultOf(list_nodes)
        list_nodes_response_body = self.successResultOf(treq.json_content(
                                                        list_nodes_response))
        self.assertEqual(list_nodes_response.code, 200)
        self.assertEqual(len(list_nodes_response_body["nodes"]), 1)

    def test_list_nodes_on_non_existant_loadbalancer(self):
        """
        Test to verify :func: `list_node` lists the nodes on the loadbalancer.
        """
        list_nodes = request(
            self, self.root, "GET", self.uri + '/loadbalancers/123/nodes')
        list_nodes_response = self.successResultOf(list_nodes)
        self.assertEqual(list_nodes_response.code, 404)

    def test_get_node_on_loadbalancer(self):
        """
        Test to verify :func: `get_node` gets the nodes on the loadbalancer.
        """
        get_nodes = request(
            self, self.root, "GET", self.uri + '/loadbalancers/' +
            str(self.create_lb_response_body["loadBalancer"]["id"]) + '/nodes/'
            + str(self.node[0]["id"]))
        get_node_response = self.successResultOf(get_nodes)
        get_node_response_body = self.successResultOf(treq.json_content(
                                                      get_node_response))
        self.assertEqual(get_node_response.code, 200)
        self.assertEqual(len(self.node), 1)
        self.assertEqual(get_node_response_body["node"]["id"],
                         self.node[0]["id"])

    def test_get_node_on_non_existant_loadbalancer(self):
        """
        Test to verify :func: `get_node` does get a nodes on a
        non existant loadbalancer.
        """
        get_nodes = request(
            self, self.root, "GET", self.uri + '/loadbalancers/123' +
            '/nodes/' + str(self.node[0]["id"]))
        get_node_response = self.successResultOf(get_nodes)
        self.assertEqual(get_node_response.code, 404)

    def test_get_non_existant_node_on_loadbalancer(self):
        """
        Test to verify :func: `get_node` does not get a non existant node.
        """
        get_nodes = request(
            self, self.root, "GET", self.uri + '/loadbalancers/' +
            str(self.create_lb_response_body["loadBalancer"]["id"]) + '/nodes/123')
        get_node_response = self.successResultOf(get_nodes)
        self.assertEqual(get_node_response.code, 404)

    def test_delete_node_on_loadbalancer(self):
        """
        Test to verify :func: `delete_node` deletes the node on the loadbalancer.
        """
        delete_nodes = request(
            self, self.root, "DELETE", self.uri + '/loadbalancers/' +
            str(self.create_lb_response_body["loadBalancer"]["id"]) + '/nodes/'
            + str(self.node[0]["id"]))
        delete_node_response = self.successResultOf(delete_nodes)
        self.assertEqual(delete_node_response.code, 202)

    def test_delete_node_on_non_existant_loadbalancer(self):
        """
        Test to verify :func: `delete_node` does delete a nodes on a
        non existant loadbalancer.
        """
        delete_nodes = request(
            self, self.root, "DELETE", self.uri + '/loadbalancers/123' +
            '/nodes/' + str(self.node[0]["id"]))
        delete_node_response = self.successResultOf(delete_nodes)
        self.assertEqual(delete_node_response.code, 404)

    def test_delete_non_existant_node_on_loadbalancer(self):
        """
        Test to verify :func: `delete_node` does not delete a non existant node.
        """
        delete_nodes = request(
            self, self.root, "DELETE", self.uri + '/loadbalancers/' +
            str(self.create_lb_response_body["loadBalancer"]["id"]) + '/nodes/123')
        delete_node_response = self.successResultOf(delete_nodes)
        self.assertEqual(delete_node_response.code, 404)
