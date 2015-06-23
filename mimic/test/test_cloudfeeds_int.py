from mimic.rest.cloudfeeds import (CloudFeedsApi, CloudFeedsControlApi)
from mimic.test.fixtures import APIMockHelper
from mimic.test.helpers import request
from twisted.trial.unittest import SynchronousTestCase


class TestCloudFeedsAPI(SynchronousTestCase):
    def setUp(self):
        """
        Create a MimicCore with CloudFeeds support as the only plugin.
        """
        cf_api = CloudFeedsApi()
        self.helper = APIMockHelper(self, [cf_api, CloudFeedsControlApi(cf_api=cf_api)])
        self.root = self.helper.root
        self.uri = self.helper.uri
        self.ctrl_uri = self.helper.auth.get_service_endpoint(
            "cloudFeedsControl", "ORD"
        )

    def test_data_plane_access_should_404(self):
        """
        Attempts to hit the data plane, as it's currently written, should 404.
        This is because the boilerplate is written but no endpoints.
        """
        r = request(
            self, self.root, "GET", self.uri,
        )
        resp = self.successResultOf(r)
        self.assertEquals(resp.code, 404)

    def test_control_plane_access_should_404(self):
        """
        Attempts to hit the controldata plane, as it's currently written,
        should 404.  This is because the boilerplate is written but no
        endpoints.
        """
        r = request(
            self, self.root, "GET", self.ctrl_uri,
        )
        resp = self.successResultOf(r)
        self.assertEquals(resp.code, 404)
