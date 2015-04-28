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
        List the images
        """
        req = request(self, self.root, "GET", self.uri + '/images', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(True, 'images' in json.dumps(data))
