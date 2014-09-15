

from twisted.trial.unittest import SynchronousTestCase
from mimic.canned_responses.loadbalancer import load_balancer_example


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
