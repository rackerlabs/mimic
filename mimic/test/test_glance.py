import treq

from twisted.trial.unittest import SynchronousTestCase
from mimic.test.fixtures import APIMockHelper
from mimic.test.helpers import request
from mimic.rest.glance_api import GlanceApi


class GlanceAPITests(SynchronousTestCase):
    """
    Tests for the Glance plugin api
    """
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


    def test_pending_images(self):
        """
        List any pending images
        """
        req = request(self, self.root, "GET",
                      self.uri + '/images?member_status=pending&&visibility=shared&&limit=1000', '')
        resp = self.successResultOf(req)
        data = self.successResultOf(treq.text_content(resp))
        self.assertEquals(data, b"")
        self.assertEquals(resp.code, 200)
