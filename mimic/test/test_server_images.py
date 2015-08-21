"""
Tests for :mod:`nova_api` and :mod:`nova_objects` for images.
"""

from twisted.trial.unittest import SynchronousTestCase

from mimic.test.helpers import json_request, request
from mimic.rest.nova_api import NovaApi, NovaControlApi
from mimic.test.fixtures import APIMockHelper


class NovaAPIImagesTests(SynchronousTestCase):

    """
    Tests for Images using the Nova Api plugin.
    """

    def setUp(self):
        """
        Create a :obj:`MimicCore` with :obj:`NovaApi` as the only plugin.
        """
        nova_api = NovaApi(["ORD", "MIMIC"])
        self.helper = self.helper = APIMockHelper(
            self, [nova_api, NovaControlApi(nova_api=nova_api)]
        )
        self.root = self.helper.root
        self.uri = self.helper.uri

    def get_server_image(self, postfix):
        """
        Get images, assert response code is 200 and return response body.
        """
        (response, content) = self.successResultOf(json_request(
            self, self.root, "GET", self.uri + postfix))
        self.assertEqual(200, response.code)
        return content

    def test_get_server_image_negative(self):
        """
        Test to verify :func:`get_image` when invalid image from the
        :obj: `mimic_presets` is provided.
        """
        get_server_image = request(self, self.root, "GET", self.uri +
                                   '/images/1111')
        get_server_image_response = self.successResultOf(get_server_image)
        self.assertEqual(get_server_image_response.code, 404)

    def test_get_server_image_negative2(self):
        """
        Test to verify :func:`get_image` when invalid image from the
        :obj: `mimic_presets` is provided.
        """
        get_server_image = request(self, self.root, "GET", self.uri +
                                   '/images/any-image-ending-with-Z')
        get_server_image_response = self.successResultOf(get_server_image)
        self.assertEqual(get_server_image_response.code, 404)

    def test_get_server_image(self):
        """
        Test to verify :func:`get_image` on ``GET /v2.0/<tenant_id>/images/<image_id>``
        """
        get_server_image_response_body = self.get_server_image(
            '/images/test-image-id')
        self.assertEqual(
            get_server_image_response_body['image']['id'], 'test-image-id')
        self.assertEqual(
            get_server_image_response_body['image']['status'], 'ACTIVE')

    def test_get_image_list(self):
        """
        Test to verify :func:`get_image_list` on ``GET /v2.0/<tenant_id>/images``
        """
        get_image_list_response_body = self.get_server_image('/images')
        image_list = get_image_list_response_body['images']
        self.assertTrue(len(image_list) > 1)
        for each_image in image_list:
            self.assertEqual(sorted(each_image.keys()), sorted(['id', 'name', 'links']))

    def test_get_image_list_with_details(self):
        """
        Test to verify :func:`test_get_image_list_with_details` on
        ``GET /v2.0/<tenant_id>/images/details``
        """
        get_image_list_response_body = self.get_server_image('/images/detail')
        image_list = get_image_list_response_body['images']
        self.assertTrue(len(image_list) > 1)
        for each_image in image_list:
            self.assertEqual(
                sorted(each_image.keys()),
                sorted(['id', 'name', 'links', 'status', 'progress', 'minRam',
                        'OS-DCF:diskConfig', 'OS-EXT-IMG-SIZE:size', 'metadata',
                        'minDisk', 'created', 'updated']))

    def test_get_image_list_with_details_is_consistent(self):
        """
        Test to verify ``GET /v2.0/<tenant_id>/images/details`` returns
        consistent data on mutiple list calls
        """
        get_image_list_response_body = self.get_server_image('/images/detail')
        get_image_list2_response_body = self.get_server_image('/images/detail')
        self.assertEqual(get_image_list_response_body, get_image_list2_response_body)

    def test_get_image_list_after_list_images(self):
        """
        Test to verify :func:`get_image_list` on ``GET /v2.0/<tenant_id>/images``
        """
        image_list = self.get_server_image('/images')['images']
        for each_image in image_list:
            get_server_image_response_body = self.get_server_image(
                '/images/' + each_image['id'])
            self.assertEqual(each_image['id'],
                             get_server_image_response_body['image']['id'])
            self.assertEqual(each_image['name'],
                             get_server_image_response_body['image']['name'])
