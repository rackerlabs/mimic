import treq
from mimic.rest.cloudfeeds import (CloudFeedsApi, CloudFeedsControlApi)
from mimic.test.fixtures import APIMockHelper
from mimic.test.helpers import request
from twisted.trial.unittest import SynchronousTestCase
from testtools.matchers import (MatchesDict, MatchesSetwise, MatchesRegex, Equals)


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

    def test_data_plane_access_should_return_200(self):
        """
        Hit the data plane, and expect a 200 response code and valid,
        parseable JSON.  It must contain at least one pre-registered
        service.
        """
        listing = MatchesDict({
            "service": MatchesDict({
                "workspace": MatchesSetwise(
                    MatchesDict({
                        "collection": MatchesDict({
                            "href": MatchesRegex(r"^http:\/\/.*\/autoscale\/.*"),
                            "title": Equals("autoscale_events"),
                        }),
                        "title": Equals("autoscale_events"),
                    }),
                ),
            })
        })
        r = request(
            self, self.root, "GET", self.uri,
        )
        resp = self.successResultOf(r)
        body = self.successResultOf(treq.json_content(resp))
        print(body)
        self.assertEquals(resp.code, 200)
        self.assertEquals(listing.match(body), None)

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
