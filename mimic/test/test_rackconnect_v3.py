"""
Unit tests for the Rackspace RackConnect V3 API.
"""
import json
from random import randint
from uuid import uuid4

from six import text_type

from twisted.trial.unittest import SynchronousTestCase
from mimic.test.fixtures import APIMockHelper
from mimic.rest.rackconnect_v3_api import (
    LoadBalancerPool, LoadBalancerPoolNode, RackConnectV3)
from mimic.test.helpers import json_request, request_with_content


class _IsString(object):

    """
    Helper class to be used when checking equality when you don't what the ID
    is but you want to check that it's an ID
    """

    def __eq__(self, other):
        """
        Returns true if the other is a string
        """
        return isinstance(other, basestring)


class LoadBalancerObjectTests(SynchronousTestCase):

    """
    Tests for :class:`LoadBalancerPool` and :class:`LoadBalancerPoolNode`
    """

    def setUp(self):
        self.pool = LoadBalancerPool(id=text_type("pool_id"),
                                     virtual_ip=text_type("10.0.0.1"))
        for i in range(10):
            self.pool.nodes.append(
                LoadBalancerPoolNode(id=text_type("node_{0}".format(i)),
                                     created="2000-01-01T00:00:00Z",
                                     load_balancer_pool=self.pool,
                                     updated=None,
                                     cloud_server=text_type(
                                         "server_{0}".format(i))))

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

    def test_LBPoolNode_update(self):
        """
        Updating the status changes the 'now', 'status', and 'status_detail'
        attributes.
        """
        self.pool.nodes[0].update(now="2000-01-02T00:00:00Z",
                                  status="DISABLED",
                                  status_detail="Broken.")
        self.assertEqual(
            {
                "id": "node_0",
                "created": "2000-01-01T00:00:00Z",
                "updated": "2000-01-02T00:00:00Z",
                "load_balancer_pool": {
                    "id": "pool_id"
                },
                "cloud_server": {
                    "id": "server_0"
                },
                "status": "DISABLED",
                "status_detail": "Broken."
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


class RackConnectTestMixin(object):

    """
    Mixin object that provides some nice utilities
    """

    def setUp(self):
        """
        Create a :obj:`MimicCore` with :obj:`RackConnectV3` as the only plugin
        """
        super(RackConnectTestMixin, self).setUp()
        self.rcv3 = RackConnectV3()
        self.helper = APIMockHelper(self, [self.rcv3])
        self.pool_id = self.get_lb_ids()[0][0]

    def get_lb_ids(self):
        """
        Helper function to get the load balancer ids per region
        """
        _, resp_jsons = zip(*[
            self.successResultOf(json_request(
                self, self.helper.root, "GET",
                self.helper.get_service_endpoint("rackconnect", region)
                + "/load_balancer_pools"))
            for region in self.rcv3.regions])

        lb_ids = [[lb['id'] for lb in lbs] for lbs in resp_jsons]
        return lb_ids

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


class LoadbalancerPoolAPITests(RackConnectTestMixin, SynchronousTestCase):

    """
    Tests for the LoadBalancerPool API
    """

    def test_list_pools_default_one(self):
        """
        Verify the JSON response from listing all load balancer pools.
        By default, all tenants have one load balancer pool.
        """
        response, response_json = self.successResultOf(
            self.json_request("GET", "/load_balancer_pools"))
        self.assertEqual(200, response.code)
        self.assertEqual(['application/json'],
                         response.headers.getRawHeaders('content-type'))
        self.assertEqual(1, len(response_json))

        pool_json = response_json[0]
        # has the right JSON
        self.assertTrue(all(
            attr.name in pool_json
            for attr in LoadBalancerPool.characteristic_attributes
            if attr.name != "nodes"))
        # Generated values
        self.assertTrue(all(
            pool_json.get(attr.name)
            for attr in LoadBalancerPool.characteristic_attributes
            if attr.name not in ("nodes", "status_detail")))

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
        The same tenant has different pools in different regions, default of 1
        pool in each.
        """
        self.rcv3 = RackConnectV3(regions=["ORD", "DFW"])
        self.helper = APIMockHelper(self, [self.rcv3])
        lb_ids = self.get_lb_ids()
        self.assertEqual(1, len(lb_ids[0]))
        self.assertEqual(1, len(lb_ids[1]))
        self.assertNotEqual(set(lb_ids[0]), set(lb_ids[1]))

    def test_default_multiple_pools(self):
        """
        If ``default_pools`` is passed to :class:`RackConnectV3`, multiple
        load balancer pools will be created per tenant per region
        """
        self.rcv3 = RackConnectV3(regions=["ORD", "DFW"], default_pools=2)
        self.helper = APIMockHelper(self, [self.rcv3])
        lb_ids = self.get_lb_ids()
        self.assertEqual(2, len(lb_ids[0]))
        self.assertEqual(2, len(lb_ids[1]))
        self.assertNotEqual(set(lb_ids[0]), set(lb_ids[1]))

    def test_get_pool_on_success(self):
        """
        Validate the JSON response of getting a single pool on an existing
        pool.
        """
        _, pool_list_json = self.successResultOf(
            self.json_request("GET", "/load_balancer_pools"))
        pool = pool_list_json[0]

        pool_details_response, pool_details_json = self.successResultOf(
            self.json_request("GET",
                              "/load_balancer_pools/{0}".format(pool['id'])))

        self.assertEqual(200, pool_details_response.code)
        self.assertEqual(
            ['application/json'],
            pool_details_response.headers.getRawHeaders('content-type'))
        self.assertEqual(pool, pool_details_json)

    def test_get_pool_400_non_uuid_pool_id(self):
        """
        Getting pool on a non-uuid pool id returns a 400.
        """
        response, content = self.successResultOf(
            self.request_with_content("GET", "/load_balancer_pools/123"))

        self.assertEqual(400, response.code)

    def test_get_pool_404_non_existant_pool(self):
        """
        Getting pool on a non-existant pool returns a 404.
        """
        random_pool_id = text_type(uuid4())
        response, content = self.successResultOf(
            self.request_with_content("GET",
                                      "/load_balancer_pools/{0}".format(random_pool_id)))

        self.assertEqual(404, response.code)
        self.assertEqual("Load Balancer Pool {0} does not exist".format(random_pool_id), content)

    def _get_add_nodes_json(self):
        """
        Helper function to generate bulk add nodes JSON given the lbs on
        the tenant and region
        """
        return [
            {"cloud_server": {"id": "{0}".format(randint(0, 9))},
             "load_balancer_pool": {"id": pool_id}}
            for pool_id in self.get_lb_ids()[0]
        ]

    def _get_custom_add_nodes_json(self, node_and_pool_ids):
        """
        Helper function to generate bulk add nodes JSON given values for
        node and pool ids.
        node_and_pool_ids: list of tuples of corresponding node and
        pool ids.
        """
        return [
            {"cloud_server": {"id": "{0}".format(each[0])},
             "load_balancer_pool": {"id": each[1]}}
            for each in node_and_pool_ids
        ]

    def _check_added_nodes_result(self, seconds, add_json, results_json):
        """
        Helper function to add some servers to the pools, and check that the
        results reflect the added nodes
        """
        self.assertEqual(len(add_json), len(results_json))

        # sort function by server ID then load balancer pool ID
        def cmp_key_function(dictionary):
            "{0}_{1}".format(dictionary['cloud_server']['id'],
                             dictionary['load_balancer_pool']['id'])

        add_json = sorted(add_json, key=cmp_key_function)
        results_json = sorted(results_json, key=cmp_key_function)

        # Can't construct the whole thing, because the IDs are random, so
        # compare some parts
        for i, add_blob in enumerate(add_json):
            result = results_json[i]
            expected = {
                "id": _IsString(),
                "cloud_server": add_blob['cloud_server'],
                "load_balancer_pool": add_blob['load_balancer_pool'],
                "created": "1970-01-01T00:00:{0:02}Z".format(seconds),
                "status": "ACTIVE",
                "status_detail": None,
                "updated": None
            }
            self.assertEqual(expected, result)

    def test_add_bulk_pool_nodes_success_response(self):
        """
        Adding multiple pool nodes successfully results in a 200 with the
        correct node detail responses
        """
        self.helper.clock.advance(50)
        add_data = self._get_add_nodes_json()
        response, resp_json = self.successResultOf(self.json_request(
            "POST", "/load_balancer_pools/nodes", body=add_data))
        self.assertEqual(201, response.code)
        self._check_added_nodes_result(50, add_data, resp_json)

    def test_add_bulk_pool_nodes_when_pool_id_is_non_uuid(self):
        """
        Adding multiple pool nodes results in a 400 if one of the pool_ids
        is not a uuid4
        """
        self.helper.clock.advance(50)
        node_and_pool_ids = [(text_type(uuid4()), 122),
                             (text_type(uuid4()), text_type(uuid4()))]
        add_data = self._get_custom_add_nodes_json(node_and_pool_ids)
        response, resp_json = self.successResultOf(self.json_request(
            "POST", "/load_balancer_pools/nodes", body=add_data))
        self.assertEqual(400, response.code)

    def test_add_bulk_pool_nodes_to_single_non_existant_pool_id_1(self):
        """
        Adding a pool node to a non-existant pool_id using add bulk node
        api call results in a 409 with respective error message
        """
        self.helper.clock.advance(50)
        pool_id = text_type(uuid4())
        node_and_pool_ids = [(text_type(uuid4()), pool_id)]
        add_data = self._get_custom_add_nodes_json(node_and_pool_ids)
        response, resp_json = self.successResultOf(self.json_request(
            "POST", "/load_balancer_pools/nodes", body=add_data))
        self.assertEqual(409, response.code)
        self.assertEqual("Load Balancer Pool {0} does not exist".format(pool_id),
                         resp_json["errors"][0])

    def test_add_bulk_pool_nodes_to_single_non_existant_pool_id_2(self):
        """
        Adding multiple pool nodes to a non-existant pool_id results in a 409
        with respective error message
        """
        self.helper.clock.advance(50)
        pool_id = text_type(uuid4())
        node_and_pool_ids = [(text_type(uuid4()), pool_id),
                             (text_type(uuid4()), pool_id)]
        add_data = self._get_custom_add_nodes_json(node_and_pool_ids)
        response, resp_json = self.successResultOf(self.json_request(
            "POST", "/load_balancer_pools/nodes", body=add_data))
        self.assertEqual(409, response.code)
        self.assertEqual("Load Balancer Pool {0} does not exist".format(pool_id),
                         resp_json["errors"][0])
        self.assertEqual("Load Balancer Pool {0} does not exist".format(pool_id),
                         resp_json["errors"][1])

    def test_add_bulk_pool_nodes_to_multiple_non_existant_pool_ids(self):
        """
        Adding multiple pool nodes to multiple non-existant pool_id results in a 409
        with respective error messages
        """
        self.helper.clock.advance(50)
        node_and_pool_ids = [(text_type(uuid4()), text_type(uuid4())),
                             (text_type(uuid4()), text_type(uuid4()))]
        add_data = self._get_custom_add_nodes_json(node_and_pool_ids)
        response, resp_json = self.successResultOf(self.json_request(
            "POST", "/load_balancer_pools/nodes", body=add_data))
        self.assertEqual(409, response.code)
        self.assertEqual(len(resp_json['errors']), 2)

    def test_add_bulk_pool_nodes_for_an_existing_node(self):
        """
        Adding an existing node to a pool_id results in a 409
        with respective error messages
        """
        self.helper.clock.advance(50)
        server_id = text_type(uuid4())

        # add node to lb_pool
        node_and_pool_ids = [(server_id, self.get_lb_ids()[0][0])]
        add_data = self._get_custom_add_nodes_json(node_and_pool_ids)
        response, resp_json = self.successResultOf(self.json_request(
            "POST", "/load_balancer_pools/nodes", body=add_data))
        self.assertEqual(201, response.code)

        # re-adding the node
        response, resp_json = self.successResultOf(self.json_request(
            "POST", "/load_balancer_pools/nodes", body=add_data))
        self.assertEqual(409, response.code)
        self.assertEqual("Cloud Server {0} is already a member of "
                         "Load Balancer Pool {1}".format(server_id, self.get_lb_ids()[0][0]),
                         resp_json["errors"][0])

    def test_add_bulk_pool_nodes_multiple_errors(self):
        """
        Adding an existing node to a pool_id. Then adding the node to an exiting
        and non-existing pool id results in a 409 with respective error messages
        """
        self.helper.clock.advance(50)

        # add node to a valid lb pool
        server_id = text_type(uuid4())
        node_and_pool_ids = [(server_id, self.get_lb_ids()[0][0])]
        add_data = self._get_custom_add_nodes_json(node_and_pool_ids)
        response, resp_json = self.successResultOf(self.json_request(
            "POST", "/load_balancer_pools/nodes", body=add_data))
        self.assertEqual(201, response.code)

        # get the node count for the lb pool
        _, list_json = self.successResultOf(self.json_request(
            "GET", "/load_balancer_pools/{0}/nodes".format(self.pool_id)))

        # re-add the node to a valid lb pool id as well to a non-existant pool_id
        node_and_pool_ids.append((server_id, text_type(uuid4())))
        add_data = self._get_custom_add_nodes_json(node_and_pool_ids)
        response, resp_json = self.successResultOf(self.json_request(
            "POST", "/load_balancer_pools/nodes", body=add_data))
        self.assertEqual(409, response.code)
        self.assertEqual(len(resp_json["errors"]), 2)

        # ensure no new nodes were added to the pool
        _, list_json_again = self.successResultOf(self.json_request(
            "GET", "/load_balancer_pools/{0}/nodes".format(self.pool_id)))
        self.assertEqual(len(list_json_again), len(list_json))

    def test_add_bulk_pool_nodes_errors_with_no_node_added(self):
        """
        Add bulk pool nodes fails with a 409 if even one of the cloud servers
        or pool_ids in the request causes an error.
        """
        self.helper.clock.advance(50)
        # get the node count for the lb pool
        _, list_json = self.successResultOf(self.json_request(
            "GET", "/load_balancer_pools/{0}/nodes".format(self.pool_id)))
        server_id = text_type(uuid4())
        random_pool_id = text_type(uuid4())
        node_and_pool_ids = [(server_id, self.get_lb_ids()[0][0]),
                             (server_id, random_pool_id)]
        add_data = self._get_custom_add_nodes_json(node_and_pool_ids)
        response, resp_json = self.successResultOf(self.json_request(
            "POST", "/load_balancer_pools/nodes", body=add_data))
        self.assertEqual(409, response.code)
        self.assertEqual("Load Balancer Pool {0} does not exist".format(random_pool_id),
                         resp_json["errors"][0])
        # ensure no new nodes were added to the pool
        _, list_json_again = self.successResultOf(self.json_request(
            "GET", "/load_balancer_pools/{0}/nodes".format(self.pool_id)))
        self.assertEqual(len(list_json_again), len(list_json))

    def test_add_bulk_pool_nodes_then_list(self):
        """
        Adding multiple pool nodes successfully means that the next time nodes
        are listed those nodes are listed.
        """
        self.helper.clock.advance(50)
        add_data = self._get_add_nodes_json()
        add_response, _ = self.successResultOf(self.json_request(
            "POST", "/load_balancer_pools/nodes", body=add_data))
        self.assertEqual(201, add_response.code)

        _, list_json = self.successResultOf(self.json_request(
            "GET", "/load_balancer_pools/{0}/nodes".format(self.pool_id)))
        self._check_added_nodes_result(50, add_data, list_json)

    def test_remove_bulk_pool_nodes_success(self):
        """
        Removing multiple pool nodes successfully results in a 204 with the
        correct node detail responses
        """
        server_data = self._get_add_nodes_json()

        # add first
        resp, body = self.successResultOf(self.json_request(
            "POST", "/load_balancer_pools/nodes", body=server_data))

        # ensure the node has been added
        _, list_json = self.successResultOf(self.json_request(
            "GET", "/load_balancer_pools/{0}/nodes".format(self.pool_id)))
        self.assertEqual(1, len(list_json))

        # delete
        response, _ = self.successResultOf(self.request_with_content(
            "DELETE", "/load_balancer_pools/nodes",
            body=json.dumps(server_data)))
        self.assertEqual(204, response.code)

        # ensure there are 0
        _, list_json = self.successResultOf(self.json_request(
            "GET", "/load_balancer_pools/{0}/nodes".format(self.pool_id)))
        self.assertEqual(0, len(list_json))

    def test_remove_bulk_pool_nodes_when_pool_id_is_non_uuid(self):
        """
        Removing multiple pool nodes results in a 400 if one of the pool_ids
        is not a uuid4
        """
        node_and_pool_ids = [(text_type(uuid4()), 122)]
        add_data = self._get_custom_add_nodes_json(node_and_pool_ids)
        response, resp_json = self.successResultOf(self.json_request(
            "DELETE", "/load_balancer_pools/nodes", body=add_data))
        self.assertEqual(400, response.code)

    def test_remove_bulk_pool_nodes_to_single_non_existant_pool_id_1(self):
        """
        Removing a pool node from a non-existant pool_id results in a 409
        with respective error message
        """
        server_id = text_type(uuid4())
        node_and_pool_ids = [(server_id, self.get_lb_ids()[0][0])]
        add_data = self._get_custom_add_nodes_json(node_and_pool_ids)
        response, resp_json = self.successResultOf(self.json_request(
            "POST", "/load_balancer_pools/nodes", body=add_data))
        self.assertEqual(201, response.code)
        pool_id = text_type(uuid4())
        node_and_pool_ids = [(server_id, pool_id)]
        add_data = self._get_custom_add_nodes_json(node_and_pool_ids)
        response, resp_json = self.successResultOf(self.json_request(
            "DELETE", "/load_balancer_pools/nodes", body=add_data))
        self.assertEqual(409, response.code)
        self.assertEqual("Load Balancer Pool {0} does not exist".format(pool_id),
                         resp_json["errors"][0])

    def test_remove_bulk_pool_nodes_to_single_non_existant_pool_id_2(self):
        """
        Removing multiple pool nodes from a non-existant pool_id results in a 409
        with respective error message
        """
        pool_id = text_type(uuid4())
        node_and_pool_ids = [(text_type(uuid4()), pool_id),
                             (text_type(uuid4()), pool_id)]
        add_data = self._get_custom_add_nodes_json(node_and_pool_ids)
        response, resp_json = self.successResultOf(self.json_request(
            "DELETE", "/load_balancer_pools/nodes", body=add_data))
        self.assertEqual(409, response.code)
        self.assertEqual("Load Balancer Pool {0} does not exist".format(pool_id),
                         resp_json["errors"][0])

    def test_remove_bulk_pool_nodes_to_multiple_non_existant_pool_ids(self):
        """
        Removing multiple pool nodes from multiple non-existant pool_id results in a 409
        with respective error messages
        """
        node_and_pool_ids = [(text_type(uuid4()), text_type(uuid4())),
                             (text_type(uuid4()), text_type(uuid4()))]
        add_data = self._get_custom_add_nodes_json(node_and_pool_ids)
        response, resp_json = self.successResultOf(self.json_request(
            "POST", "/load_balancer_pools/nodes", body=add_data))
        self.assertEqual(409, response.code)
        self.assertEqual(len(resp_json['errors']), 2)

    def test_remove_bulk_pool_nodes_given_a_non_existing_node(self):
        """
        Removing an already deleted node from a pool_id results in a 409
        with respective error messages
        """
        server_id = text_type(uuid4())
        node_and_pool_ids = [(server_id, self.get_lb_ids()[0][0])]
        add_data = self._get_custom_add_nodes_json(node_and_pool_ids)
        response, resp_json = self.successResultOf(self.json_request(
            "POST", "/load_balancer_pools/nodes", body=add_data))
        self.assertEqual(201, response.code)
        response, _ = self.successResultOf(self.request_with_content(
            "DELETE", "/load_balancer_pools/nodes",
            body=json.dumps(add_data)))
        self.assertEqual(204, response.code)

        # get the node count for the lb pool
        _, list_json = self.successResultOf(self.json_request(
            "GET", "/load_balancer_pools/{0}/nodes".format(self.pool_id)))

        response, resp_json = self.successResultOf(self.request_with_content(
            "DELETE", "/load_balancer_pools/nodes",
            body=json.dumps(add_data)))
        self.assertEqual(409, response.code)
        resp = json.loads(resp_json)
        self.assertEqual("Cloud Server {0} is not a member of "
                         "Load Balancer Pool {1}".format(server_id, self.get_lb_ids()[0][0]),
                         resp["errors"][0])

        # ensure no other nodes were deleted from the pool
        _, list_json_again = self.successResultOf(self.json_request(
            "GET", "/load_balancer_pools/{0}/nodes".format(self.pool_id)))
        self.assertEqual(len(list_json_again), len(list_json))

    def test_remove_bulk_pool_nodes_multiple_errors(self):
        """
        Removing bulk pool nodes fails with a 409 if even one of the cloud servers
        or pool_ids in the request causes an error.
        """
        server_id = text_type(uuid4())
        random_pool_id = text_type(uuid4())

        # get the node count for the lb pool
        _, list_json = self.successResultOf(self.json_request(
            "GET", "/load_balancer_pools/{0}/nodes".format(self.pool_id)))

        node_and_pool_ids = [(server_id, self.get_lb_ids()[0][0]),
                             (server_id, random_pool_id)]
        add_data = self._get_custom_add_nodes_json(node_and_pool_ids)
        response, resp_json = self.successResultOf(self.json_request(
            "POST", "/load_balancer_pools/nodes", body=add_data))
        self.assertEqual(409, response.code)
        self.assertEqual("Load Balancer Pool {0} does not exist".format(random_pool_id),
                         resp_json["errors"][0])

        # ensure no nodes were deleted from the pool
        _, list_json_again = self.successResultOf(self.json_request(
            "GET", "/load_balancer_pools/{0}/nodes".format(self.pool_id)))
        self.assertEqual(len(list_json_again), len(list_json))


class LoadbalancerPoolNodesAPITests(RackConnectTestMixin,
                                    SynchronousTestCase):

    """
    Tests for the LoadBalancerPool API for getting and updating nodes
    """

    def test_get_pool_404_invalid_pool_nodes(self):
        """
        Getting nodes on a non-existant pool returns a 404.
        """
        random_pool_id = text_type(uuid4())
        response, content = self.successResultOf(self.request_with_content(
            "GET", "/load_balancer_pools/{0}/nodes".format(random_pool_id)))

        self.assertEqual(404, response.code)
        self.assertEqual("Load Balancer Pool {0} does not exist".format(random_pool_id),
                         content)

    def test_get_pool_nodes_empty(self):
        """
        Getting nodes for an empty existing load balancer returns a 200 with
        no nodes
        """
        response, json_content = self.successResultOf(self.json_request(
            "GET", "/load_balancer_pools/{0}/nodes".format(self.pool_id)))
        self.assertEqual(200, response.code)
        self.assertEqual(json_content, [])

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
        response, content = self.successResultOf(self.request_with_content(
            "POST", "/load_balancer_pools/{0}/nodes".format(self.pool_id),
            body=json.dumps({
                "cloud_server": {"id": "d95ae0c4-6ab8-4873-b82f-f8433840cff2"}
            })))
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
