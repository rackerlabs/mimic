"""
Tests for dns api
"""

from __future__ import absolute_import, division, unicode_literals

from twisted.trial.unittest import SynchronousTestCase

from mimic.test.helpers import json_request
from mimic.rest.networks_api import NetworksApi
from mimic.test.fixtures import APIMockHelper


class NetworksTests(SynchronousTestCase):
    """
    Tests for networks using the Networks Api plugin.
    """
    def setUp(self):
        """
        Create a :obj:`MimicCore` with :obj: `NetworksApi` as the only plugin.
        """
        dns_api = NetworksApi(['DFW'])
        self.helper = APIMockHelper(self, [dns_api])
        self.root = self.helper.root
        self.uri = self.helper.uri

    def test_get_networks(self):
        """

        https://developer.rackspace.com/docs/cloud-dns/v1/developer-guide/#list-ptr-records
        """
        (response, content) = self.successResultOf(json_request(
            self, self.root, b"GET", self.uri + '/networks'))
        self.assertEqual(200, response.code)
        self.assertEqual(content, {"networks": [], "networks_links":
                                   [{"href": "http://localhost:9696/v2.0/networks?page_reverse=True",
                                    "rel": "previous"}]})
