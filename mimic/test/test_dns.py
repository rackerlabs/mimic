"""
Tests for dns api
"""

from __future__ import absolute_import, division, unicode_literals

from twisted.trial.unittest import SynchronousTestCase

from mimic.test.helpers import json_request
from mimic.rest.dns_api import DNSApi
from mimic.test.fixtures import APIMockHelper


class DNSTests(SynchronousTestCase):
    """
    Tests for DNS using the DNS Api plugin.
    """
    def setUp(self):
        """
        Create a :obj:`MimicCore` with :obj:`DNSApi` as the only plugin.
        """
        dns_api = DNSApi(['DFW'])
        self.helper = APIMockHelper(self, [dns_api])
        self.root = self.helper.root
        self.uri = self.helper.uri

    def test_get_ptr_record_list(self):
        """
        Requesting PTR records for a service that does not have any returns a 404
        https://developer.rackspace.com/docs/cloud-dns/v1/developer-guide/#list-ptr-records
        """
        (response, content) = self.successResultOf(json_request(
            self, self.root, b"GET", self.uri + '/rdns/cloudServersOpenStack'))
        self.assertEqual(404, response.code)
        self.assertEqual(content, {'message': 'Not Found', 'code': 404,
                                   'details': 'No PTR records found'})
