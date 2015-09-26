"""
Unit tests for the
"""

import json
import treq

from twisted.trial.unittest import SynchronousTestCase
from mimic.canned_responses.loadbalancer import load_balancer_example
from mimic.model.clb_errors import (
    considered_immutable_error,
    invalid_json_schema,
    loadbalancer_not_found,
    node_not_found,
    updating_node_validation_error
)
from mimic.test.fixtures import APIMockHelper, TenantAuthentication
from mimic.rest.loadbalancer_api import LoadBalancerApi, LoadBalancerControlApi
from mimic.test.helpers import json_request, request_with_content, request
from mimic.util.helper import EMPTY_RESPONSE
import attr


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
                                       input_lb_time)

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


@attr.s
class _CLBChangeResponseAndID(object):
    """
    A simple data structure intended to conveniently communicate the results
    of issuing a CLB control plane request.
    """
    resp = attr.ib()
    "The response returned from the .../attributes PATCH request."

    lb_id = attr.ib()
    "The CLB ID used for the purposes of performing the test."


class LoadbalancerAPITests(SynchronousTestCase):
    """
    Tests for the Loadbalancer plugin API
    """

    def setUp(self):
        """
        Create a :obj:`MimicCore` with :obj:`LoadBalancerApi` as the only plugin
        """
        lb = LoadBalancerApi()
        self.helper = APIMockHelper(self, [lb, LoadBalancerControlApi(lb_api=lb)])
        self.root = self.helper.root
        self.uri = self.helper.uri

    def _create_loadbalancer(self, name=None, api_helper=None, nodes=None):
        """
        Helper method to create a load balancer and return the lb_id.

        :param str name: The name fo the load balancer, defaults to 'test_lb'
        :param api_helper: An instance of :class:`APIMockHelper` - defaults to
            the one created by setup, but if different regions need to be
            created, for instance, your test may make a different helper, and
            so that helper can be passed here.
        :param list nodes: A list of nodes to create the load balancer with -
            defaults to creating a load balancer with no nodes.

        :return: Load balancer ID
        :rtype: int
        """
        api_helper = api_helper or self.helper
        lb_body = {
            "loadBalancer": {
                "name": name or "test_lb",
                "protocol": "HTTP",
                "virtualIps": [{"type": "PUBLIC"}]
            }
        }
        if nodes is not None:
            lb_body['loadBalancer']['nodes'] = nodes

        resp, body = self.successResultOf(json_request(
            self, api_helper.root, "POST", api_helper.uri + '/loadbalancers',
            lb_body
        ))
        return body['loadBalancer']['id']

    def _patch_attributes_request(
        self, lb_id_offset=0, status_key=None, status_val=None
    ):
        """
        Creates a CLB for the tenant, then attempts to patch its status using
        the CLB control plane endpoint.

        :param int lb_id_offset: Defaults to 0.  If provided, the CLB that is
            created for the tenant will be referenced in the patch request
            offset by this much.
        :param str status_key: Defaults to '"status"'.  If provided, the patch
            will be made against this member of the CLB's state.  Note that
            surrounding quotes are required for th key, thus giving the caller
            the ability to deliberately distort the JSON.
        :param str status_val: Defaults to 'PENDING_DELETE'.  If provided, the
            provided setting will be used for the status key provided.
        :return: An instance of _CLBChangeResponseAndID.  The `resp` attribute
            will refer to Mimic's response object; `code` will be set to the
            HTTP result code from the request.
        """
        ctl_uri = self.helper.auth.get_service_endpoint(
            "cloudLoadBalancerControl", "ORD"
        )
        lb_id = self._create_loadbalancer('test_lb') + lb_id_offset
        status_key = status_key or '"status"'
        status_val = status_val or 'PENDING_DELETE'
        payload = '{{{0}: "{1}"}}'.format(status_key, status_val)
        set_attributes_req = request(
            self, self.root, "PATCH", "{0}/loadbalancer/{1}/attributes".format(
                ctl_uri, lb_id
            ),
            payload
        )
        return _CLBChangeResponseAndID(
            resp=self.successResultOf(set_attributes_req), lb_id=lb_id
        )

    def test_lb_status_changes_as_requested(self):
        """
        Clients can ``PATCH`` to the ``.../loadbalancer/<lb-id>/attributes``
        :obj:`LoadBalancerControlApi` endpoint in order to change the
        ``status`` attribute on the load balancer identified by the given
        load-balancer ID for the same tenant in the :obj:`LoadBalancerApi`.

        This attribute controls the status code returned when the load balancer
        is retrieved by a ``GET`` request.
        """
        r = self._patch_attributes_request()
        self.assertEqual(r.resp.code, 204)

        get_lb = request(self, self.root, "GET", self.uri + '/loadbalancers/' + str(r.lb_id))
        get_lb_response = self.successResultOf(get_lb)
        get_lb_response_body = self.successResultOf(
            treq.json_content(get_lb_response)
        )["loadBalancer"]
        self.assertEqual(get_lb_response.code, 200)
        self.assertEqual(get_lb_response_body["status"], "PENDING_DELETE")

    def test_lb_status_change_with_illegal_json(self):
        """
        In the event the user sends a malformed request body to the
        .../attributes endpoint, we should get back a 400 Bad Request.
        """
        r = self._patch_attributes_request(status_key="\"status'")
        self.assertEqual(r.resp.code, 400)

    def test_lb_status_change_with_bad_keys(self):
        """
        In the event the user sends a request to alter a key which isn't
        supported, we should get back a 400 Bad Request as well.
        """
        r = self._patch_attributes_request(status_key="\"stats\"")
        self.assertEqual(r.resp.code, 400)

    def test_lb_status_change_to_illegal_status(self):
        """
        If we attempt to set a valid status on a valid CLB for a valid tenant
        to a value which is nonsensical, we should get back a 400.
        """
        r = self._patch_attributes_request(status_val="KJDHSFLKJDSH")
        self.assertEqual(r.resp.code, 400)

    def test_lb_status_change_against_undefined_clb(self):
        """
        In the event the user sends a request to alter a key on a load balancer
        which doesn't belong to the requestor, we should get back a 404 code.
        """
        r = self._patch_attributes_request(lb_id_offset=1000)
        self.assertEqual(r.resp.code, 404)

    def test_multiple_regions_multiple_endpoints(self):
        """
        API object created with multiple regions has multiple entries
        in the service catalog.
        """
        helper = APIMockHelper(self,
                               [LoadBalancerApi(regions=['ORD', 'DFW'])])
        entry = helper.service_catalog_json['access']['serviceCatalog'][0]
        self.assertEqual(2, len(entry['endpoints']))

    def test_add_load_balancer(self):
        """
        If created without nodes, no node information appears in the response
        when making a request to ``POST /v1.0/<tenant_id>/loadbalancers``.
        """
        lb_name = 'mimic_lb'
        resp, body = self.successResultOf(json_request(
            self, self.root, "POST", self.uri + '/loadbalancers',
            {
                "loadBalancer": {
                    "name": lb_name,
                    "protocol": "HTTP",
                    "virtualIps": [{"type": "PUBLIC"}]
                }
            }
        ))
        self.assertEqual(resp.code, 202)
        self.assertEqual(body['loadBalancer']['name'], lb_name)
        self.assertNotIn("nodeCount", body["loadBalancer"])
        self.assertNotIn("nodes", body["loadBalancer"])

    def test_add_load_balancer_request_with_no_body_causes_bad_request(self):
        """
        Test to verify :func:`add_load_balancer` on ``POST /v1.0/<tenant_id>/loadbalancers``
        """
        create_lb = request(self, self.root, "POST", self.uri + '/loadbalancers', "")
        create_lb_response = self.successResultOf(create_lb)
        self.assertEqual(create_lb_response.code, 400)

    def test_add_load_balancer_request_with_invalid_body_causes_bad_request(self):
        """
        Test to verify :func:`add_load_balancer` on ``POST /v1.0/<tenant_id>/loadbalancers``
        """
        create_lb = request(self, self.root, "POST", self.uri + '/loadbalancers', "{ bad request: }")
        create_lb_response = self.successResultOf(create_lb)
        self.assertEqual(create_lb_response.code, 400)

    def test_add_load_balancer_with_nodes(self):
        """
        Making a request to ``POST /v1.0/<tenant_id>/loadbalancers`` with
        nodes adds the nodes to the load balancer.
        """
        lb_name = 'mimic_lb'
        resp, body = self.successResultOf(json_request(
            self, self.root, "POST", self.uri + '/loadbalancers',
            {
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
            }
        ))
        self.assertEqual(resp.code, 202)
        self.assertNotIn("nodeCount", body['loadBalancer'])
        self.assertEqual(len(body['loadBalancer']['nodes']), 2)

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

    def test_list_loadbalancers_have_no_nodes(self):
        """
        When listing load balancers, nodes do not appear even if the load
        balanacer has nodes.  "nodeCount" is present for all the load
        balancers, whether or not there are nodes on the load balancer.
        """
        self._create_loadbalancer('no_nodes')
        self._create_loadbalancer(
            '3nodes', nodes=[{"address": "1.1.1.{0}".format(i),
                              "port": 80, "condition": "ENABLED"}
                             for i in range(1, 4)])
        list_resp, list_body = self.successResultOf(json_request(
            self, self.root, "GET", self.uri + '/loadbalancers'))
        self.assertEqual(list_resp.code, 200)
        self.assertEqual(len(list_body['loadBalancers']), 2)

        for lb in list_body['loadBalancers']:
            self.assertNotIn("nodes", lb)
            self.assertEqual(
                lb['nodeCount'],
                0 if lb['name'] == 'no_nodes' else 3)

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
        del_lb_response_body = self.successResultOf(treq.content(del_lb_response))
        self.assertEqual(del_lb_response_body, '')
        # List lb to make sure the correct lb is gone and the other remains
        list_lb = request(self, self.root, "GET", self.uri + '/loadbalancers')
        list_lb_response = self.successResultOf(list_lb)
        list_lb_response_body = self.successResultOf(treq.json_content(list_lb_response))
        self.assertTrue(len(list_lb_response_body['loadBalancers']), 1)
        self.assertTrue(list_lb_response_body['loadBalancers'][0]['id'] == test2_id)

    def test_get_loadbalancer_with_nodes(self):
        """
        If there are nodes on the load balancer, "nodes" (but not "nodeCount")
        appears in the response when making a request to
        ``GET /v1.0/<tenant_id>/loadbalancers/<loadbalancer_id>``.
        """
        lb_id = self._create_loadbalancer(
            nodes=[{"address": "1.2.3.4", "port": 80, "condition": "ENABLED"}])
        resp, body = self.successResultOf(json_request(
            self, self.root, "GET", self.uri + '/loadbalancers/' + str(lb_id)))
        self.assertEqual(resp.code, 200)
        self.assertEqual(body['loadBalancer']['id'], lb_id)
        self.assertNotIn('nodeCount', body['loadBalancer'])
        self.assertEqual(len(body['loadBalancer']['nodes']), 1)

    def test_get_loadbalancer_no_nodes(self):
        """
        If there are no nodes on the load balancer, then neither "nodeCount"
        nor "nodes" appear in the response when making a request to
        ``GET /v1.0/<tenant_id>/loadbalancers/<loadbalancer_id>``
        """
        lb_id = self._create_loadbalancer()
        resp, body = self.successResultOf(json_request(
            self, self.root, "GET", self.uri + '/loadbalancers/' + str(lb_id)))
        self.assertEqual(resp.code, 200)
        self.assertEqual(body['loadBalancer']['id'], lb_id)
        self.assertNotIn('nodeCount', body['loadBalancer'])
        self.assertNotIn('nodes', body['loadBalancer'])

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

    def test_different_tenants_same_region_different_lbs(self):
        """
        Creating a LB for one tenant in a particular region should not
        create it for other tenants in the same region.
        """
        self._create_loadbalancer()

        other_tenant = TenantAuthentication(self, self.root, "other", "other")

        list_lb_response, list_lb_response_body = self.successResultOf(
            request_with_content(
                self, self.root, "GET",
                other_tenant.get_service_endpoint("cloudLoadBalancers")
                + "/loadbalancers"))

        self.assertEqual(list_lb_response.code, 200)

        list_lb_response_body = json.loads(list_lb_response_body)
        self.assertEqual(list_lb_response_body, {"loadBalancers": []})

    def test_same_tenant_different_regions(self):
        """
        Creating an LB for a tenant in one different regions should create it
        in another region for that tenant.
        """
        helper = APIMockHelper(self,
                               [LoadBalancerApi(regions=["ORD", "DFW"])])
        self._create_loadbalancer(api_helper=helper)

        list_lb_response, list_lb_response_body = self.successResultOf(
            request_with_content(
                self, helper.root, "GET",
                helper.get_service_endpoint("cloudLoadBalancers", "DFW")
                + "/loadbalancers"))

        self.assertEqual(list_lb_response.code, 200)

        list_lb_response_body = json.loads(list_lb_response_body)
        self.assertEqual(list_lb_response_body, {"loadBalancers": []})


def _bulk_delete(test_case, root, uri, lb_id, node_ids):
    """Bulk delete multiple nodes."""
    query = '?' + '&'.join('id=' + str(node_id) for node_id in node_ids)
    endpoint = uri + '/loadbalancers/' + str(lb_id) + '/nodes' + query
    d = request(test_case, root, "DELETE", endpoint)
    response = test_case.successResultOf(d)
    body = test_case.successResultOf(treq.content(response))
    if body == '':
        body = EMPTY_RESPONSE
    else:
        body = json.loads(body)
    return response, body


def _update_clb_node(test_case, helper, lb_id, node_id, update_data,
                     request_func=json_request):
    """
    Return the response for updating a CLB node.
    """
    return test_case.successResultOf(request_func(
        test_case, helper.root, "PUT",
        "{0}/loadbalancers/{1}/nodes/{2}".format(
            helper.get_service_endpoint("cloudLoadBalancers"),
            lb_id, node_id),
        update_data
    ))


class LoadbalancerNodeAPITests(SynchronousTestCase):
    """
    Tests for the Loadbalancer plugin API for CRUD for nodes.
    """

    def setUp(self):
        """
        Create a :obj:`MimicCore` with :obj:`LoadBalancerApi` as the only plugin.
        And create a load balancer and add nodes to the load balancer.
        """
        self.helper = APIMockHelper(self, [LoadBalancerApi()])
        self.root = self.helper.root
        self.uri = self.helper.uri
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
        self.lb_id = self.create_lb_response_body["loadBalancer"]["id"]
        create_node = self._create_nodes(["127.0.0.1"])
        [(self.create_node_response, self.create_node_response_body)] = create_node
        self.node = self.create_node_response_body["nodes"]

    def _create_nodes(self, addresses):
        """
        Create nodes based on the addresses passed.

        :param list addresses: addresses to create nodes for.

        :return: a list of two-tuples of (response, response_body).
        """
        responses = [
            request(
                self, self.root, "POST", self.uri + '/loadbalancers/' +
                str(self.create_lb_response_body["loadBalancer"]["id"]) + '/nodes',
                json.dumps({"nodes": [{"address": address,
                                       "port": 80,
                                       "condition": "ENABLED",
                                       "type": "PRIMARY",
                                       "weight": 10}]}))
            for address in addresses]
        responses = map(self.successResultOf, responses)
        response_bodies = [self.successResultOf(treq.json_content(response))
                           for response in responses]
        return zip(responses, response_bodies)

    def _get_nodes(self, lb_id):
        """Get all the nodes in a LB."""
        list_nodes = request(
            self, self.root, "GET", self.uri + '/loadbalancers/' +
            str(lb_id) + '/nodes')
        response = self.successResultOf(list_nodes)
        body = self.successResultOf(treq.json_content(response))
        return body['nodes']

    def test_add_node_to_loadbalancer(self):
        """
        Test to verify :func: `add_node` create a node successfully.
        """
        self.assertEqual(self.create_node_response.code, 202)
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
            str(self.lb_id) + '/nodes',
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
        self.assertEqual(create_node_response.code, 202)
        self.assertEqual(len(create_node_response_body["nodes"]), 2)

    def test_add_duplicate_node(self):
        """
        Test to verify :func: `add_node` does not allow creation of duplicate nodes.
        """
        create_duplicate_nodes = request(
            self, self.root, "POST", self.uri + '/loadbalancers/' +
            str(self.lb_id) + '/nodes',
            json.dumps({"nodes": [{"address": "127.0.0.1",
                                   "port": 80,
                                   "condition": "ENABLED",
                                   "type": "PRIMARY"}]})
        )
        create_node_response = self.successResultOf(create_duplicate_nodes)
        self.assertEqual(create_node_response.code, 413)

    def test_add_single_over_node_limit(self):
        """
        Test to verify :func: `add_node` does not allow creation of a single
        node at a time to exceed the node limit.

        Note: This assumes the node limit is 25. If the limit is made
        configurable, this test will need to be updated.
        """

        for port in range(101, 126):
            request(
                self, self.root, "POST", self.uri + '/loadbalancers/' +
                str(self.lb_id) + '/nodes',
                json.dumps({"nodes": [{"address": "127.0.0.1",
                                       "port": port,
                                       "condition": "ENABLED"}]})
            )
        create_over_node = request(
            self, self.root, "POST", self.uri + '/loadbalancers/' +
            str(self.lb_id) + '/nodes',
            json.dumps({"nodes": [{"address": "127.0.0.2",
                                   "port": 130,
                                   "condition": "ENABLED",
                                   "type": "SECONDARY"}]})
        )

        create_node_response = self.successResultOf(create_over_node)
        self.assertEqual(create_node_response.code, 413)

    def test_add_bulk_nodes_over_limit(self):
        """
        Test to verify :func: `add_node` does not allow creation of a single
        node at a time to exceed the node limit.

        Note: This assumes the node limit is 25. If the limit is made
        configurable, this test will need to be updated.
        """

        add_node_list = []
        for a in range(26):
            node_addr = "127.0.0.{0}".format(a)
            add_node_list.append({"address": node_addr,
                                  "port": 88,
                                  "condition": "ENABLED",
                                  "type": "SECONDARY"})

        create_over_node = request(
            self, self.root, "POST", self.uri + '/loadbalancers/' +
            str(self.lb_id) + '/nodes',
            json.dumps({"nodes": add_node_list})
        )
        create_node_response = self.successResultOf(create_over_node)
        self.assertEqual(create_node_response.code, 413)

    def test_add_node_request_with_no_body_causes_bad_request(self):
        """
        Test to verify :func: `add_node` does not fail on bad request.
        """
        create_duplicate_nodes = request(
            self, self.root, "POST", self.uri + '/loadbalancers/' +
            str(self.lb_id) + '/nodes', "")

        create_node_response = self.successResultOf(create_duplicate_nodes)
        self.assertEqual(create_node_response.code, 400)

    def test_add_node_request_with_invalid_body_causes_bad_request(self):
        """
        Test to verify :func: `add_node` does not fail on bad request.
        """
        create_duplicate_nodes = request(
            self, self.root, "POST", self.uri + '/loadbalancers/' +
            str(self.lb_id) + '/nodes', "{ bad request: }")

        create_node_response = self.successResultOf(create_duplicate_nodes)
        self.assertEqual(create_node_response.code, 400)

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
            str(self.lb_id) + '/nodes')
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
            str(self.lb_id) + '/nodes/'
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
            str(self.lb_id) + '/nodes/123')
        get_node_response = self.successResultOf(get_nodes)
        self.assertEqual(get_node_response.code, 404)

    def test_delete_node_on_loadbalancer(self):
        """
        Test to verify :func: `delete_node` deletes the node on the loadbalancer.
        """
        delete_nodes = request(
            self, self.root, "DELETE", self.uri + '/loadbalancers/' +
            str(self.lb_id) + '/nodes/'
            + str(self.node[0]["id"]))
        delete_node_response = self.successResultOf(delete_nodes)
        self.assertEqual(delete_node_response.code, 202)

        # assert that it lists correctly after
        list_nodes_resp, list_nodes_body = self.successResultOf(json_request(
            self, self.root, "GET", self.uri + '/loadbalancers/' +
            str(self.lb_id) + '/nodes'))
        self.assertEqual(list_nodes_resp.code, 200)
        self.assertEqual(len(list_nodes_body["nodes"]), 0)

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
            str(self.lb_id) + '/nodes/123')
        delete_node_response = self.successResultOf(delete_nodes)
        self.assertEqual(delete_node_response.code, 404)

    def test_bulk_delete(self):
        """
        Test to verify :func: `delete_nodes` deletes the nodes on the loadbalancer.
        """
        node_results = self._create_nodes(['127.0.0.2', '127.0.0.3', '127.0.0.4'])
        node_ids = [
            node_result['id']
            for (response, body) in node_results
            for node_result in body['nodes']]
        node_ids_to_delete = node_ids[:-1]
        response, body = _bulk_delete(
            self, self.root, self.uri, self.lb_id, node_ids_to_delete)
        self.assertEqual(response.code, 202)
        self.assertEqual(body, EMPTY_RESPONSE)
        remaining_nodes = self._get_nodes(self.lb_id)
        # The one in setUp and the extra one we created are remaining
        self.assertEqual(
            [node['id'] for node in remaining_nodes],
            [self.node[0]['id'], node_ids[-1]])

    def test_bulk_delete_no_nodes(self):
        """
        When deleting multiple nodes but not giving any node IDs, a special
        error is returned.
        """
        response, body = _bulk_delete(
            self, self.root, self.uri, self.lb_id, [])
        self.assertEqual(response.code, 400)
        self.assertEqual(
            body,
            {'code': 400,
             'message': "Must supply one or more id's to process this request."})

    def test_bulk_delete_no_nodes_invalid_lb(self):
        """
        When trying to delete multiple nodes from a non-existent LB, the error
        for an empty node list takes precedence over the error for a
        non-existing LB.
        """
        lb_id = self.lb_id + 1
        response, body = _bulk_delete(self, self.root, self.uri, lb_id, [])
        self.assertEqual(response.code, 400)
        self.assertEqual(
            body,
            {'code': 400,
             'message': "Must supply one or more id's to process this request."})

    def test_bulk_delete_invalid_lb(self):
        """
        Bulk-deleting nodes from a non-existent LB returns a 404 and an appropriate
        message.
        """
        lb_id = self.lb_id + 1
        node_ids_to_delete = [self.node[0]['id']]
        response, body = _bulk_delete(self, self.root, self.uri, lb_id, node_ids_to_delete)
        self.assertEqual(response.code, 404)
        self.assertEqual(
            body,
            {'code': 404,
             'message': "Load balancer not found"})

    def test_bulk_delete_nonexistent_nodes(self):
        """
        When trying to delete multiple nodes, if any of the nodes don't exist, no
        nodes are deleted and a special error result is returned.
        """
        node_ids_to_delete = [self.node[0]['id'], 1000000, 1000001]
        response, body = _bulk_delete(
            self, self.root, self.uri, self.lb_id, node_ids_to_delete)
        self.assertEqual(response.code, 400)
        self.assertEqual(
            body,
            {
                "validationErrors": {
                    "messages": [
                        "Node ids 1000000,1000001 are not a part of your loadbalancer"
                    ]
                },
                "message": "Validation Failure",
                "code": 400,
                "details": "The object is not valid"
            }
        )
        # and the one valid node that we tried to delete is still there
        remaining = [node['id'] for node in self._get_nodes(self.lb_id)]
        self.assertEquals(remaining, [self.node[0]['id']])

    def test_updating_node_invalid_json(self):
        """
        When updating a node, if invalid JSON is provided (both actually not
        valid JSON and also not conforming to the schema), a 400 invalid
        JSON error will be returned.  This takes precedence over whether or not
        a load balancer or node actually exists, and precedence over
        validation errors.
        """
        real_lb_id = self.lb_id
        real_node_id = self.node[0]['id']
        fake_lb_id = real_lb_id + 1
        fake_node_id = real_node_id + 1

        combos = ((real_lb_id, real_node_id),
                  (real_lb_id, fake_node_id),
                  (fake_lb_id, fake_node_id))

        invalids = (
            {"node": {"weight": 1, "hockey": "stick"}},
            {"node": {"weight": 1, "status": "OFFLINE"}},
            {"node": {"weight": 1},
             "other": "garbage"},
            {"node": []},
            {"node": 1},
            {"nodes": {"weight": 1}},
            [],
            "not JSON",
            {"node": {"weight": "not a number", "address": "1.1.1.1"}},
            {"node": {"condition": "INVALID", "id": 1}},
            {"node": {"type": "INVALID", "weight": 1000}},
            {"node": {"weight": "not a number", "port": 80}}
        )

        expected = invalid_json_schema()

        for lb_id, node_id in combos:
            for invalid in invalids:
                resp, body = _update_clb_node(
                    self, self.helper, lb_id, node_id, invalid)
                self.assertEqual(
                    (body, resp.code), expected,
                    "{0} should have returned invalid JSON error".format(
                        invalid))

                self.assertEqual(
                    self._get_nodes(real_lb_id), self.node)

    def test_updating_node_validation_error(self):
        """
        When updating a node, if the address or port are provided,
        a 400 validation error will be returned because those are immutable.
        If the weight is <1 or >100, a 400 validation will also be returned.

        These takes precedence over whether or not a load balancer or node
        actually exists.  The error message also contains a list of all the
        validation failures.
        """
        real_lb_id = self.lb_id
        real_node_id = self.node[0]['id']
        fake_lb_id = real_lb_id + 1
        fake_node_id = real_node_id + 1

        combos = ((real_lb_id, real_node_id),
                  (real_lb_id, fake_node_id),
                  (fake_lb_id, fake_node_id))

        for lb_id, node_id in combos:
            data = {"node": {"weight": 1000, "address": "1.1.1.1",
                             "port": 80, "type": "PRIMARY", "id": 12345}}
            for popoff in (None, "address", "port", "weight"):
                if popoff:
                    del data["node"][popoff]

                resp, body = _update_clb_node(
                    self, self.helper, lb_id, node_id, data)
                actual = (body, resp.code)
                expected = updating_node_validation_error(
                    address="address" in data["node"],
                    port="port" in data["node"],
                    weight="weight" in data["node"],
                    id=True)  # id is always there
                self.assertEqual(
                    actual, expected,
                    "Input of {0}.\nGot: {1}\nExpected: {2}".format(
                        data,
                        json.dumps(actual, indent=2),
                        json.dumps(expected, indent=2)))

                self.assertEqual(
                    self._get_nodes(real_lb_id), self.node)

    def test_updating_node_checks_for_invalid_loadbalancer_id(self):
        """
        If the input is valid, but the load balancer ID does not exist,
        a 404 error is returned.
        """
        resp, body = _update_clb_node(
            self, self.helper, self.lb_id + 1, 1234, {"node": {"weight": 1}})

        self.assertEqual((body, resp.code), loadbalancer_not_found())
        self.assertEqual(self._get_nodes(self.lb_id), self.node)

    def test_updating_node_checks_for_invalid_node_id(self):
        """
        If the input is valid, but the node ID does not exist, a 404 error is
        returned.
        """
        resp, body = _update_clb_node(
            self, self.helper, self.lb_id, self.node[0]["id"] + 1,
            {"node": {"weight": 1}})

        self.assertEqual((body, resp.code), node_not_found())
        self.assertEqual(self._get_nodes(self.lb_id), self.node)

    def test_updating_node_success(self):
        """
        Updating a node successfully changes its values.  The response from a
        successful change is just the values that changed.  The body is an
        empty string. It also updates the atom feed of the node and returns
        that when GETing ../loadbalancers/lbid/nodes/nodeid.atom
        """
        original = self.node[0]
        expected = original.copy()
        change = {
            "condition": "DISABLED",
            "weight": 100,
            "type": "SECONDARY"
        }
        expected.update(change)
        # sanity check to make sure we're actually changing stuff
        self.assertTrue(all([change[k] != original[k] for k in change.keys()]))
        resp, body = _update_clb_node(
            self, self.helper, self.lb_id, self.node[0]["id"],
            json.dumps({"node": change}), request_func=request_with_content)
        self.assertEqual(resp.code, 202)
        self.assertEqual(body, "")

        self.assertEqual(self._get_nodes(self.lb_id)[0], expected)

        # check if feed is updated
        d = request(
            self, self.root, "GET",
            "{0}/loadbalancers/{1}/nodes/{2}.atom".format(self.uri, self.lb_id,
                                                          self.node[0]["id"]))
        feed_response = self.successResultOf(d)
        self.assertEqual(feed_response.code, 200)
        self.assertEqual(
            self.successResultOf(treq.content(feed_response)),
            ("<feed xmlns=\"http://www.w3.org/2005/Atom\"><entry>"
             "<summary>Node successfully updated with address: '127.0.0.1', "
             "port: '80', weight: '100', condition: 'DISABLED'</summary>"
             "<updated>1970-01-01T00:00:00.000000Z</updated></entry></feed>"))

    def test_get_feed_node_404(self):
        """
        Getting feed of non-existent node returns 404 with "Node not found"
        XML
        """
        d = request(
            self, self.root, "GET",
            "{0}/loadbalancers/{1}/nodes/{2}.atom".format(self.uri, self.lb_id, 0))
        feed_response = self.successResultOf(d)
        self.assertEqual(feed_response.code, 404)
        self.assertEqual(
            self.successResultOf(treq.content(feed_response)),
            ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
             '<itemNotFound xmlns="http://docs.openstack.org/loadbalancers/api/v1.0" code="404">'
             '<message>Node not found</message></itemNotFound>'))

    def test_get_feed_clb_404(self):
        """
        Getting feed of node of non-existent CLB returns 404 with
        "load balancer not found" XML
        """
        d = request(
            self, self.root, "GET",
            "{0}/loadbalancers/{1}/nodes/{2}.atom".format(self.uri, 0, 0))
        feed_response = self.successResultOf(d)
        self.assertEqual(feed_response.code, 404)
        self.assertEqual(
            self.successResultOf(treq.content(feed_response)),
            ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
             '<itemNotFound xmlns="http://docs.openstack.org/loadbalancers/api/v1.0" code="404">'
             '<message>Load balancer not found</message></itemNotFound>'))


class LoadbalancerAPINegativeTests(SynchronousTestCase):
    """
    Tests for the Loadbalancer plugin API for error injection
    """

    def setUp(self):
        """
        Create a :obj:`MimicCore` with :obj:`LoadBalancerApi` as the only plugin
        """
        helper = APIMockHelper(self, [LoadBalancerApi()])
        self.root = helper.root
        self.uri = helper.uri
        self.helper = helper

    def _create_loadbalancer_for_given_metadata(self, metadata=None):
        """
        Helper method to create a load balancer with the given metadata
        """
        create_lb = request(
            self, self.root, "POST", self.uri + '/loadbalancers',
            json.dumps({
                "loadBalancer": {
                    "name": "test_lb",
                    "protocol": "HTTP",
                    "virtualIps": [{"type": "PUBLIC"}],
                    "metadata": metadata or []
                }
            })
        )
        create_lb_response = self.successResultOf(create_lb)
        return create_lb_response

    def _add_node_to_lb(self, lb_id):
        """
        Adds a node to the load balancer and returns the response object
        """
        create_node = request(
            self, self.root, "POST", self.uri + '/loadbalancers/'
            + str(lb_id) + '/nodes',
            json.dumps({"nodes": [{"address": "127.0.0.1",
                                   "port": 80,
                                   "condition": "ENABLED",
                                   "type": "PRIMARY"}]})
        )
        create_node_response = self.successResultOf(create_node)
        return create_node_response

    def _get_loadbalancer(self, lb_id):
        """
        Makes the `GET` call for the given loadbalancer id and returns the
        load balancer object.
        """
        get_lb = request(self, self.root, "GET", self.uri + '/loadbalancers/' + str(lb_id))
        get_lb_response = self.successResultOf(get_lb)
        get_lb_response_body = self.successResultOf(treq.json_content(get_lb_response))
        return get_lb_response_body

    def _delete_loadbalancer(self, lb_id):
        """
        Deletes the given load balancer id and returns the response
        """
        delete_lb = request(self, self.root, "DELETE", self.uri + '/loadbalancers/' +
                            str(lb_id))
        return self.successResultOf(delete_lb)

    def _create_loadbalancer(self, metadata):
        """Create a load balancer and return the response body."""
        create_response = self._create_loadbalancer_for_given_metadata(metadata)
        self.assertEqual(create_response.code, 202)
        create_lb_response_body = self.successResultOf(treq.json_content(create_response))
        lb = create_lb_response_body["loadBalancer"]
        self.assertEqual(lb["status"], "ACTIVE")
        return lb

    def test_create_load_balancer_in_building_state(self):
        """
        Test to verify the created load balancer remains in building
        state for the time is seconds specified in the metadata.
        Adding a node to a lb in BUILD status results in 422.
        """
        metadata = [{"key": "lb_building", "value": 1}]
        create_response = self._create_loadbalancer_for_given_metadata(metadata)
        self.assertEqual(create_response.code, 202)
        create_lb_response_body = self.successResultOf(treq.json_content(create_response))
        lb = create_lb_response_body["loadBalancer"]
        self.assertEqual(lb["status"], "BUILD")
        create_node_response = self._add_node_to_lb(lb["id"])
        self.assertEqual(create_node_response.code, 422)

    def test_load_balancer_goes_into_error_state_when_adding_node(self):
        """
        Test to verify a load balancer goes into error state when adding a node.
        Adding a node to a loadbalancer in ERROR state results in 422.
        And such a load balancer can only be deleted.
        """
        metadata = [{"key": "lb_error_state", "value": "error"}]
        lb = self._create_loadbalancer(metadata)
        create_node_response = self._add_node_to_lb(lb["id"])
        self.assertEqual(create_node_response.code, 202)
        # get loadbalncer after adding node and verify its in error state
        errored_lb = self._get_loadbalancer(lb["id"])
        self.assertEqual(errored_lb["loadBalancer"]["status"], "ERROR")
        # adding another node to a lb in ERROR state, results in 422
        create_node_response = self._add_node_to_lb(lb["id"])
        self.assertEqual(create_node_response.code, 422)
        # An lb in ERROR state can be deleted
        delete_lb = request(self, self.root, "DELETE", self.uri + '/loadbalancers/' +
                            str(lb["id"]))
        delete_lb_response = self.successResultOf(delete_lb)
        self.assertEqual(delete_lb_response.code, 202)

    def test_load_balancer_goes_into_pending_update_state(self):
        """
        Test to verify a load balancer goes into PENDING-UPDATE state, for
        the given time in seconds when any action other than DELETE is performed
        on the lb.
        Adding a node to a loadbalancer in PENDING-UPDATE state results in 422.
        And such a load balancer can be deleted.
        """
        metadata = [{"key": "lb_pending_update", "value": 30}]
        lb = self._create_loadbalancer(metadata)
        create_node_response = self._add_node_to_lb(lb["id"])
        self.assertEqual(create_node_response.code, 202)
        # get loadbalncer after adding node and verify its in PENDING-UPDATE state
        errored_lb = self._get_loadbalancer(lb["id"])
        self.assertEqual(errored_lb["loadBalancer"]["status"], "PENDING-UPDATE")
        # Trying to add/list/delete node on a lb in PENDING-UPDATE state, results in 422
        create_node_response = self._add_node_to_lb(lb["id"])
        self.assertEqual(create_node_response.code, 422)
        delete_nodes = request(
            self, self.root, "DELETE", self.uri + '/loadbalancers/' +
            str(lb["id"]) + '/nodes/123')
        self.assertEqual(self.successResultOf(delete_nodes).code, 422)
        # An lb in PENDING-UPDATE state can be deleted
        delete_lb = request(self, self.root, "DELETE", self.uri + '/loadbalancers/' +
                            str(lb["id"]))
        delete_lb_response = self.successResultOf(delete_lb)
        self.assertEqual(delete_lb_response.code, 202)

    def test_load_balancer_reverts_from_pending_update_state(self):
        """
        Test to verify a load balancer goes into PENDING-UPDATE state, for
        the given time in seconds.
        """
        metadata = [{"key": "lb_pending_update", "value": 1}]
        lb = self._create_loadbalancer(metadata)
        create_node_response = self._add_node_to_lb(lb["id"])
        self.assertEqual(create_node_response.code, 202)
        # get loadbalncer after adding node and verify its in PENDING-UPDATE state
        errored_lb = self._get_loadbalancer(lb["id"])
        self.assertEqual(errored_lb["loadBalancer"]["status"], "PENDING-UPDATE")
        self.helper.clock.advance(1.0)
        # get loadbalncer after adding node and verify its in ACTIVE state
        errored_lb = self._get_loadbalancer(lb["id"])
        self.assertEqual(errored_lb["loadBalancer"]["status"], "ACTIVE")

    def test_delete_load_balancer_and_pending_delete_state(self):
        """
        Test to verify a load balancer goes into PENDING-DELETE state, for
        the given time in seconds and then goes into a DELETED status.
        Also, verify when a load balancer in PENDING-DELETE or DELETED status
        is deleted, response code 400 is returned.
        """
        metadata = [{"key": "lb_pending_delete", "value": 1}]
        lb = self._create_loadbalancer(metadata)

        # Verify the lb status goes into PENDING-DELETE
        del_lb_response = self._delete_loadbalancer(lb["id"])
        self.assertEqual(del_lb_response.code, 202)
        del_lb_content = self.successResultOf(treq.content(del_lb_response))
        self.assertEqual(del_lb_content, '')
        deleted_lb = self._get_loadbalancer(lb["id"])
        self.assertEqual(deleted_lb["loadBalancer"]["status"], "PENDING-DELETE")

        # Trying to delete a lb in PENDING-DELETE status results in 400
        self.assertEqual(self._delete_loadbalancer(lb["id"]).code, 400)
        self.helper.clock.advance(1.0000001)

        # Lb goes into DELETED status after time specified in metadata
        deleted_lb = self._get_loadbalancer(lb["id"])
        self.assertEqual(deleted_lb["loadBalancer"]["status"], "DELETED")

        # Trying to delete a lb in DELETED status results in 400
        self.assertEqual(self._delete_loadbalancer(lb["id"]).code, 400)

        # GET node on load balancer in DELETED status results in 410
        get_node = request(
            self, self.root, "GET", self.uri + '/loadbalancers/' +
            str(lb["id"]) + '/nodes/123')
        get_node_response = self.successResultOf(get_node)
        self.assertEqual(get_node_response.code, 410)

        # GET node feed on load balancer in DELETED status results in 410
        node_feed = request(
            self, self.root, "GET", self.uri + '/loadbalancers/' +
            str(lb["id"]) + '/nodes/123.atom')
        node_feed_response = self.successResultOf(node_feed)
        self.assertEqual(node_feed_response.code, 410)

        # List node on load balancer in DELETED status results in 410
        list_nodes = request(
            self, self.root, "GET", self.uri + '/loadbalancers/' + str(lb["id"])
            + '/nodes')
        self.assertEqual(self.successResultOf(list_nodes).code, 410)

        # Progress past "deleting now"
        self.helper.clock.advance(4000)
        list_nodes = request(
            self, self.root, "GET", self.uri + '/loadbalancers/' + str(lb["id"])
            + '/nodes')
        self.assertEqual(self.successResultOf(list_nodes).code, 404)

    def test_bulk_delete_empty_list_takes_precedence_over_immutable(self):
        """
        When bulk deleting no nodes, the error indicating nodes must be specified
        is returned even when the LB is not ACTIVE.
        """
        metadata = [{"key": "lb_pending_update", "value": 30}]
        lb = self._create_loadbalancer(metadata)

        # Add a node, which should put it into PENDING-UPDATE
        create_node_response = self._add_node_to_lb(lb["id"])
        self.assertEqual(create_node_response.code, 202)
        updated_lb = self._get_loadbalancer(lb["id"])
        self.assertEqual(updated_lb["loadBalancer"]["status"], "PENDING-UPDATE")

        # Now, trying to bulk-delete an empty list of nodes will still return
        # the empty-nodes error.
        response, body = _bulk_delete(self, self.root, self.uri, lb['id'], [])
        self.assertEqual(response.code, 400)
        self.assertEqual(
            body,
            {'code': 400,
             'message': "Must supply one or more id's to process this request."})

    def test_bulk_delete_not_active(self):
        """
        When bulk deleting nodes while the LB is not ACTIVE, a special error is
        returned, even when some of the nodes are invalid.
        """
        metadata = [{"key": "lb_pending_update", "value": 30}]
        lb = self._create_loadbalancer(metadata)

        # Add a node, which should put it into PENDING-UPDATE
        create_node_response = self._add_node_to_lb(lb["id"])
        self.assertEqual(create_node_response.code, 202)
        updated_lb = self._get_loadbalancer(lb["id"])
        self.assertEqual(updated_lb["loadBalancer"]["status"], "PENDING-UPDATE")

        # Now, trying to bulk-delete nodes (including invalid ones) will cause
        # it to return the special error
        response, body = _bulk_delete(
            self, self.root, self.uri, lb['id'], [100, 200])
        self.assertEqual(response.code, 422)
        self.assertEqual(
            body,
            {u'message': u'LoadBalancer is not ACTIVE', u'code': 422})

    def test_updating_node_loadbalancer_state(self):
        """
        If the load balancer is not active, when updating a node a 422 error
        is returned.
        """
        metadata = [{"key": "lb_pending_update", "value": 30}]
        lb_id = self._create_loadbalancer(metadata)["id"]

        # Add a node, which should put it into PENDING-UPDATE
        create_node_response = self._add_node_to_lb(lb_id)
        self.assertEqual(create_node_response.code, 202)
        updated_lb = self._get_loadbalancer(lb_id)
        self.assertEqual(updated_lb["loadBalancer"]["status"],
                         "PENDING-UPDATE")
        node = self.successResultOf(treq.json_content(create_node_response))
        node_id = node["nodes"][0]["id"]

        resp, body = _update_clb_node(self, self.helper, lb_id, node_id,
                                      {"node": {"weight": 1}})

        self.assertEqual((body, resp.code),
                         considered_immutable_error("PENDING-UPDATE", lb_id))
