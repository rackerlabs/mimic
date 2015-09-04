import treq
import json
from twisted.trial.unittest import SynchronousTestCase
from mimic.test.fixtures import APIMockHelper
from mimic.test.helpers import request
from mimic.rest.glance_api import GlanceApi


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
        List the images returned from glance with no request args
        """
        req = request(self, self.root, "GET", self.uri + '/images')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(True, 'images' in json.dumps(data))

    def test_list_images_with_public_visibility(self):
        """
        List images with public visibility in region IAD
        """
        # All regions other than IAD have 38 images
        req = request(self, self.root, "GET", self.uri + '/images?visibility=public')
        resp = self.successResultOf(req)
        data = self.get_responsebody(resp)
        self.assertEquals(resp.code, 200)
        self.assertEqual(38, len(data['images']))
        self.assertEquals(True, 'images' in json.dumps(data))

        # The IAD region has 52 images which include OnMetal images
        helper = APIMockHelper(self, [GlanceApi(['IAD'])])
        root = helper.root
        uri = helper.uri
        req = request(self, root, "GET", uri + '/images?visibility=public')
        resp = self.successResultOf(req)
        data = self.get_responsebody(resp)
        self.assertEquals(resp.code, 200)
        self.assertEqual(52, len(data['images']))
        self.assertEquals(True, 'onmetal' in json.dumps(data['images']))

    def test_pending_images(self):
        """
        Test pending images
        """
        req = request(self, self.root, "GET", self.uri + '/images?member_status=pending&'
                                                         'visibility=shared&limit=1000')
        resp = self.successResultOf(req)
        data = self.get_responsebody(resp)
        self.assertEqual(len(data['images']), 0)
        self.assertEquals(resp.code, 200)

    def test_list_images_with_private_visibility(self):
        """
        List images with private visibility
        """
        req = request(self, self.root, "GET", self.uri + '/images?visibility=private')
        resp = self.successResultOf(req)
        data = self.get_responsebody(resp)
        self.assertEqual(len(data['images']), 0)
        self.assertEquals(resp.code, 200)

    def test_list_images_with_no_request_args(self):
        """
        List images with no request args. IAD has 14 more images than other images due to OnMetal in
            IAD only
        """
        # All regions other than IAD have 38 images
        req = request(self, self.root, "GET", self.uri + '/images')
        resp = self.successResultOf(req)
        data = self.get_responsebody(resp)
        self.assertEquals(resp.code, 200)
        self.assertEqual(38, len(data['images']))
        self.assertEquals(True, 'images' in json.dumps(data))

        # The IAD region has 52 images which include OnMetal images
        helper = APIMockHelper(self, [GlanceApi(['IAD'])])
        root = helper.root
        uri = helper.uri
        req = request(self, root, "GET", uri + '/images?visibility')
        resp = self.successResultOf(req)
        data = self.get_responsebody(resp)
        self.assertEquals(resp.code, 200)
        self.assertEqual(52, len(data['images']))
        self.assertEquals(True, 'onmetal' in json.dumps(data['images']))
