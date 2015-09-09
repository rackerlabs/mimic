import treq
import json

from twisted.trial.unittest import SynchronousTestCase
from twisted.internet.task import Clock

from mimic.test.fixtures import APIMockHelper
from mimic.test.helpers import request, json_request
from mimic.rest.glance_api import GlanceApi
from mimic.core import MimicCore
from mimic.resource import MimicRoot
from mimic.canned_responses.json.glance.glance_images_json import image_schema
from mimic.model.glance_objects import random_image_list


class GlanceAPITests(SynchronousTestCase):
    """
    Tests for the Glance plugin api
    """

    def get_responsebody(self, r):
        """
        util json response body
        """
        return self.successResultOf(treq.json_content(r))

    def setUp(self):
        """
        Setup for glance tests
        """
        helper = APIMockHelper(self, [GlanceApi()])
        self.root = helper.root
        self.uri = helper.uri

    def test_list_images(self):
        """
        List the images returned from glance
        """
        req = request(self, self.root, "GET", self.uri + '/images', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(True, 'images' in json.dumps(data))


class GlanceAdminAPITests(SynchronousTestCase):
    """
    Tests for the Glance Admin API
    """

    def setUp(self):
        """
        Initialize core and root
        """
        self.core = MimicCore(Clock(), [])
        self.root = MimicRoot(self.core).app.resource()
        self.uri = "/glance/v2/images"
        self.create_request = {"name": "OnMetal - MIMIC", "distro": "linux"}

    def create_image(self, request_json=None):
        """
        Create image and validate response code.
        Return newly created image.
        """
        request_json = request_json or self.create_request
        (response, content) = self.successResultOf(json_request(
            self, self.root, "POST", self.uri,
            body=request_json))
        self.assertEqual(response.code, 201)
        return content

    def list_images(self):
        """
        List images and return response
        """
        (response, content) = self.successResultOf(json_request(
            self, self.root, "GET", self.uri))
        self.assertEqual(200, response.code)
        for each in content['images']:
            self.assertEqual(each["status"], "active")
        return content

    def test_list_image_schema(self):
        """
        Get the image schema returned from glance admin API
        """
        uri = "/glance/v2/schemas/image"
        (response, content) = self.successResultOf(json_request(
            self, self.root, "GET", uri))
        self.assertEqual(200, response.code)
        self.assertEqual(sorted(image_schema.keys()),
                         sorted(content))

    def test_list_images_for_admin(self):
        """
        List the images returned from the glance admin api
        """
        content = self.list_images()
        self.assertEqual(len(random_image_list), len(content['images']))
        actual_image_names = [image['name'] for image in content['images']]
        expected_image_names = [each['name'] for each in random_image_list]
        self.assertEqual(sorted(actual_image_names), sorted(expected_image_names))

    def test_list_images_for_admin_consistently(self):
        """
        List the images returned from the glance admin api
        """
        content1 = self.list_images()
        content2 = self.list_images()
        self.assertEqual(content2, content1)

    def test_create_image(self):
        """
        Create Image and validate response
        """
        new_image = self.create_image()
        self.assertEqual(new_image['name'], self.create_request['name'])

    def test_create_image_fails_with_400(self):
        """
        Create Image and validate response
        """
        request_jsons = [{}, {"name": None}, {"hello": "world"}]
        for each in request_jsons:
            (response, content) = self.successResultOf(json_request(
                self, self.root, "POST", self.uri,
                body=json.dumps(each)))
            self.assertEqual(response.code, 400)

    def test_get_image(self):
        """
        Create then GET Image and validate response
        """
        new_image = self.create_image()

        (response, content) = self.successResultOf(json_request(
            self, self.root, "GET", self.uri + '/' + new_image['id']))
        self.assertEqual(200, response.code)
        self.assertEqual(new_image, content)

    def test_get_non_existant_image(self):
        """
        Return 404 when trying to GET a non existant image.
        """
        response = self.successResultOf(request(
            self, self.root, "GET", self.uri + '/' + '1111'))
        self.assertEqual(404, response.code)

    def test_delete_non_existant_image(self):
        """
        Return 404 when trying to DELETE a non existant image.
        """
        response = self.successResultOf(request(
            self, self.root, "DELETE", self.uri + '/' + '1111'))
        self.assertEqual(404, response.code)

    def test_delete_image(self):
        """
        Create and then delete Image and validate response
        """
        new_image = self.create_image()

        response = self.successResultOf(request(
            self, self.root, "DELETE", self.uri + '/' + new_image['id']))
        self.assertEqual(204, response.code)

        response = self.successResultOf(request(
            self, self.root, "GET", self.uri + '/' + new_image['id']))
        self.assertEqual(404, response.code)

    def test_get_then_delete_image(self):
        """
        Create and then delete Image and validate response
        """
        images = self.list_images()['images']

        for each in images[:2]:
            response = self.successResultOf(request(
                self, self.root, "DELETE", self.uri + '/' + each['id']))
            self.assertEqual(204, response.code)

            response = self.successResultOf(request(
                self, self.root, "GET", self.uri + '/' + each['id']))
            self.assertEqual(404, response.code)

        images_after_delete = self.list_images()['images']
        self.assertEqual(len(images),
                         len(images_after_delete) + 2)
