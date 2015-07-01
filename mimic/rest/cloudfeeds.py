# -*- test-case-name: mimic.test.test_loadbalancer -*-
"""
Defines the control plane API endpoints for the Cloudfeeds Plugin.
"""
import json
from uuid import uuid4
from six import text_type
from zope.interface import implementer
from twisted.plugin import IPlugin
from mimic.catalog import Endpoint, Entry
from mimic.imimic import IAPIMock
from mimic.rest.mimicapp import MimicApp
from mimic.model import cloudfeeds


from characteristic import attributes


@implementer(IAPIMock, IPlugin)
class CloudFeedsApi(object):
    """
    This class registers the cloud feeds API in the service catalog.
    """
    def __init__(self, regions=["ORD"]):
        """
        Configures the API with a list of regions.

        :param list regions: If provided, a list of strings, each providing a
            name for a region (e.g., "ORD").  If not specified, defaults to
            ["ORD"].
        """
        self._regions = regions

    def catalog_entries(self, tenant_id):
        """
        Returns a list of cloud feeds entries.  Note that these are not
        cloud feeds product endpoints; this is one step removed from those.
        You'll need to GET from one of these URLs to see the catalog of
        product endpoints.
        """
        return [
            Entry(tenant_id, "rax:feeds", "cloudFeeds",
                  [
                      Endpoint(tenant_id, region, text_type(uuid4()))
                      for region in self._regions
                  ])
        ]

    def resource_for_region(self, region, uri_prefix, session_store):
        """
        Get an :obj:`twisted.web.iweb.IResource` for the given URI prefix;
        implement :obj:`IAPIMock`.
        """
        lb_region = CloudFeedsRegion(
            api_mock=self,
            uri_prefix=uri_prefix,
            session_store=session_store,
            region=region
        )
        return lb_region.app.resource()


@implementer(IAPIMock, IPlugin)
@attributes(["cf_api"])
class CloudFeedsControlApi(object):
    """
    This class registers the load balancer controller API in the service
    catalog.
    """
    def catalog_entries(self, tenant_id):
        """
        Cloud feeds controller endpoints.
        """
        return [
            Entry(
                tenant_id, "rax:feeds", "cloudFeedsControl",
                [
                    Endpoint(tenant_id, region, text_type(uuid4()))
                    for region in self.cf_api._regions
                ]
            )
        ]

    def resource_for_region(self, region, uri_prefix, session_store):
        """
        Get an :obj:`twisted.web.iweb.IResource` for the given URI prefix;
        implement :obj:`IAPIMock`.
        """
        cfc_region = CloudFeedsControlRegion(
            api_mock=self, uri_prefix=uri_prefix,
            session_store=session_store, region=region
        )
        return cfc_region.app.resource()


@attributes(["api_mock", "uri_prefix", "session_store", "region"])
class CloudFeedsControlRegion(object):
    """
    Klein routes for cloud feed's control API within a particular region.
    """

    app = MimicApp()


@attributes(["api_mock", "uri_prefix", "session_store", "region"])
class CloudFeedsRegion(object):
    """
    Klein routes for cloud feeds API methods within a particular region.
    """

    app = MimicApp()

    def session(self, tenant_id):
        """
        Gets a session for a particular tenant, creating one if there isn't
        one.
        """
        tenant_session = self.session_store.session_for_tenant_id(tenant_id)
        feeds = tenant_session.data_for_api(
            self.api_mock,
            lambda: cloudfeeds.CloudFeeds(
                tenant_id=tenant_id, clock=self.session_store.clock)
            )
        return feeds

    @app.route('/<string:tenant_id>', methods=['GET'])
    def get_feeds_catalog(self, request, tenant_id):
        """Produce list of cloud feed product endpoints."""
        feeds = self.session(tenant_id)
        request.setResponseCode(200)
        return json.dumps(cloudfeeds.render_product_endpoints_dict(
            feeds.get_product_endpoints()
        ))
