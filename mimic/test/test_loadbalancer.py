"""
Unit tests for the
"""

import json
import treq

from twisted.trial.unittest import SynchronousTestCase
from mimic.canned_responses.loadbalancer import load_balancer_example
from mimic.test.fixtures import MimicTestFixture
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
        fixture = MimicTestFixture(self, [LoadBalancerApi()])
        self.root = fixture.root
        self.uri = fixture.uri

    def _create_loadbalancer(self, name):
        """
        Helper methond to create a load balancer and return the lb_id
        """
        create_lb = request(
            self, self.root, "POST", self.uri + '/loadbalancers',
            json.dumps({
                "loadBalancer": {
                    "name": name,
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
        print test1_id
        delete_lb = request(self, self.root, 'DELETE', self.uri + '/loadbalancers' + str(test1_id))
        del_lb_response = self.successResultOf(delete_lb)
        self.assertEqual(del_lb_response.code, 200)
        # List lb to make sure the correct lb is gone and the other remains
        list_lb = request(self, self.root, "GET", self.uri + '/loadbalancers')
        list_lb_response = self.successResultOf(list_lb)
        list_lb_response_body = self.successResultOf(treq.json_content(list_lb_response))
        self.assertTrue(len(list_lb_response_body['loadBalancers']), 1)
        self.assertTrue(list_lb_response_body['loadBalancers'][0]['id'] == test2_id)
