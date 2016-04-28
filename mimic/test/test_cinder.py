"""
Tests for cinder api
"""

from __future__ import absolute_import, division, unicode_literals
from twisted.trial.unittest import SynchronousTestCase
from mimic.test.helpers import json_request
from mimic.rest.cinder_api import CinderApi
from mimic.test.fixtures import APIMockHelper


class CinderTests(SynchronousTestCase):
    """
    Tests for cinder using the Cinder Api plugin.
    """
    def setUp(self):
        """
        Initialize core and root
        """
        cinder_api = CinderApi(['DFW'])
        self.helper = APIMockHelper(self, [cinder_api])
        self.root = self.helper.root
        self.uri = self.helper.uri

    def test_get_blockstorage_volume_list(self):
        """
        Requesting block storage volumes for a tenant returns 200 and an empty list
        if no volumes are available for the given tenant
        http://developer.openstack.org/api-ref-blockstorage-v2.html#getVolumesSimple
        """
        (response, content) = self.successResultOf(json_request(
            self, self.root, b"GET", self.uri + '/volumes'))
        self.assertEqual(200, response.code)
        self.assertEqual(content, {'volumes': []})
