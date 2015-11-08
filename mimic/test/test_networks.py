"""
Tests for networks api
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
        networks_api = NetworksApi(['DFW'])
        self.helper = APIMockHelper(self, [networks_api])
        self.root = self.helper.root
        self.uri = self.helper.uri

    def test_get_networks(self):
        """
        Requesting a list of networks for a tenant that does not have any will return
        a 200 with an empty network list
        https://developer.rackspace.com/docs/cloud-dns/v1/developer-guide/#list-ptr-records
        http://developer.openstack.org/api-ref-networking-v2.html
        """
        (response, content) = self.successResultOf(json_request(
            self, self.root, b"GET", self.uri + '/networks'))
        self.assertEqual(200, response.code)
        self.assertEqual(content, {"networks": []})
