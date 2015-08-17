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

    def list_images(self):
        """
        List images and return response
        """
        uri = "/glance/v2/images"
        (response, content) = self.successResultOf(json_request(
            self, self.root, "GET", uri))
        self.assertEqual(200, response.code)
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

    def test_list_images_for_admin_consistently(self):
        """
        List the images returned from the glance admin api
        """
        content1 = self.list_images()
        content2 = self.list_images()
        self.assertEqual(content2, content1)
