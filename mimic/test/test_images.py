"""
Tests for :mod:`nova_api` and :mod:`nova_objects` for images.
"""

from twisted.trial.unittest import SynchronousTestCase

from mimic.test.helpers import json_request
from mimic.rest.nova_api import NovaApi
from mimic.test.fixtures import APIMockHelper


class NovaAPIImagesTests(SynchronousTestCase):
    """
    Tests for images using the Nova Api plugin.
    """

    def setUp(self):
        """
        Create a :obj:`MimicCore` with :obj:`NovaApi` as the only plugin.
        """
        nova_api = NovaApi(['DFW'])
        self.helper = APIMockHelper(self, [nova_api])
        self.root = self.helper.root
        self.uri = self.helper.uri

    def get_server_image(self, postfix):
        """
        Get flavors, assert response code is 200 and return response body.
        """
        (response, content) = self.successResultOf(json_request(
            self, self.root, "GET", self.uri + postfix))
        self.assertEqual(200, response.code)
        return content

    def test_get_image_list(self):
        """
        Test to verify :func:`get_image_list` on ``GET /v2.0/<tenant_id>/images``
        """
        get_flavor_list_response_body = self.get_server_image('/images')
        image_list = get_flavor_list_response_body['images']
        self.assertTrue(len(image_list) > 1)
        for each_image in image_list:
            self.assertEqual(sorted(each_image.keys()), sorted(['id', 'name', 'links']))

    def test_get_image_list_with_details(self):
        """
        Test to verify :func:`get_image_list` on ``GET /v2.0/<tenant_id>/images/detail``
        """
        get_flavor_list_response_body = self.get_server_image('/images/detail')
        image_list = get_flavor_list_response_body['images']
        self.assertTrue(len(image_list) > 1)
        for each_image in image_list:
            self.assertEqual(sorted(each_image.keys()), sorted(['OS-EXT-IMG-SIZE:size',
                                                                'com.rackspace__1__ui_default_show',
                                                                'id', 'links', 'metadata', 'minDisk',
                                                                'minRam', 'name']))
