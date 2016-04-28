"""
Tests for neutron api
"""

from __future__ import absolute_import, division, unicode_literals
from twisted.trial.unittest import SynchronousTestCase
from mimic.test.helpers import json_request
from mimic.rest.neutron_api import NeutronApi
from mimic.test.fixtures import APIMockHelper


class NeutronTests(SynchronousTestCase):
    """
    Tests for networks using the Neutron Api plugin.
    """
    def setUp(self):
        """

        """
        neutron_api = NeutronApi(['DFW'])
        self.helper = APIMockHelper(self, [neutron_api])
        self.root = self.helper.root
        self.uri = self.helper.uri

    def test_get_networks(self):
        """
        Requesting a list of networks for a tenant that does not have any will return
        a 200 with an empty network list
        http://developer.openstack.org/api-ref-networking-v2.html#listNetworks
        """
        (response, content) = self.successResultOf(json_request(
            self, self.root, b"GET", self.uri + '/networks'))
        self.assertEqual(200, response.code)
        self.assertEqual(content, {'networks': []})
