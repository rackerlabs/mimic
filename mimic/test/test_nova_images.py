"""
Tests for :mod:`nova_api` and :mod:`nova_objects` for images.
"""

from twisted.trial.unittest import SynchronousTestCase

from mimic.test.helpers import json_request, request
from mimic.rest.nova_api import NovaApi, NovaControlApi
from mimic.test.fixtures import APIMockHelper
import random


class NovaAPIVirtualImageTests(SynchronousTestCase):

    """
    Tests for Virtual Images using the Nova Api plugin.
    """

    def setUp(self):
        """
        Create a :obj:`MimicCore` with :obj:`NovaApi` as the only plugin.
        """
        nova_api = NovaApi(["ORD"])
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
                                   '/images/invalid_image_id')
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

    def test_get_image_that_does_not_exist(self):
        """
        Test to verify :func:`get_image` on ``GET /v2.0/<tenant_id>/images/<image_id>``
        """
        response, body = self.successResultOf(json_request(
            self, self.root, "GET", self.uri + '/images/id_not_found'))

        self.assertEqual(response.code, 404)
        self.assertEqual(body, {
            "itemNotFound": {
                "message": "Image not found.",
                "code": 404
            }
        })

    def test_get_virtual_server_image(self):
        """
        Test to verify :func:`get_image` on ``GET /v2.0/<tenant_id>/images/<image_id>``
        """
        get_image_list_response_body = self.get_server_image('/images')
        image_list = get_image_list_response_body['images']
        choice = random.randint(0, len(image_list) - 1)
        image_id = image_list[choice]['id']
        get_image_response_body = self.get_server_image('/images/' + image_id)
        self.assertEqual(
            get_image_response_body['image']['id'], image_id)
        self.assertEqual(
            get_image_response_body['image']['status'], 'ACTIVE')

    def test_get_virtual_server_image_list(self):
        """
        Test to verify :func:`get_image_list` on ``GET /v2.0/<tenant_id>/images``
        """
        get_image_list_response_body = self.get_server_image('/images')
        image_list = get_image_list_response_body['images']
        self.assertEqual(len(image_list), 38)
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
                sorted(['id', 'name', 'links', 'minRam', 'status',
                        'OS-EXT-IMG-SIZE:size', 'metadata', 'progress', 'created', 'updated',
                        'minDisk', 'com.rackspace__1__ui_default_show']))

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

    def test_no_OnMetal_images_in_ORD(self):
        """
        Test to verify OnMetal images are not in ORD region
        """
        get_image_list_response_body = self.get_server_image('/images/detail')
        image_list = get_image_list_response_body['images']
        for image in image_list:
            self.assertTrue('!onmetal' in image['metadata']['flavor_classes'])


class NovaAPIOnMetalImageTests(SynchronousTestCase):

    """
    Tests for Virtual Images using the Nova Api plugin.
    """

    def setUp(self):
        """
        Create a :obj:`MimicCore` with :obj:`NovaApi` as the only plugin.
        """
        nova_api = NovaApi(["IAD"])
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

    def test_get_OnMetal_server_image(self):
        """
        Test to verify :func:`get_image` on ``GET /v2.0/<tenant_id>/images/<image_id>``
        """
        get_image_list_response_body = self.get_server_image('/images/detail')
        image_list = get_image_list_response_body['images']
        for image in image_list:
            if image['metadata']['flavor_classes'] == 'onmetal':
                onmetal_id = image['id']
                break
        response, body = self.successResultOf(json_request(
            self, self.root, "GET", self.uri + '/images/' + onmetal_id))
        self.assertEqual(200, response.code)
        self.assertEqual(body['image']['id'], onmetal_id)
        self.assertEqual(body['image']['metadata']['flavor_classes'], 'onmetal')

    def test_OnMetal_image_list(self):
        """
        Test to verify :func:`images` on ``GET /v2.0/<tenant_id>/images``
        """
        get_image_list_response_body = self.get_server_image('/images')
        image_list = get_image_list_response_body['images']
        self.assertTrue(len(image_list), 52)
        for each_image in image_list:
            self.assertEqual(sorted(each_image.keys()), sorted(['id', 'links', 'name']))

    def test_OnMetal_image_list_details(self):
        """
        Test to verify :func:`get_image_list` on ``GET /v2.0/<tenant_id>/images``
        includes OnMetal images in IAD
        """
        get_image_list_response_body = self.get_server_image('/images/detail')
        image_list = get_image_list_response_body['images']
        self.assertTrue(len(image_list), 52)
        for each_image in image_list:
            self.assertEqual(sorted(each_image.keys()), sorted(['id', 'name', 'links', 'minRam',
                                                                'status', 'OS-EXT-IMG-SIZE:size',
                                                                'metadata', 'progress', 'created',
                                                                'updated', 'minDisk',
                                                                'com.rackspace__1__ui_default_show']))
