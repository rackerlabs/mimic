# -*- test-case-name: mimic.test.test_loadbalancer -*-
"""
Defines the control plane API endpoints for the Cloudfeeds Plugin.
"""
from uuid import uuid4
from six import text_type
from zope.interface import implementer
from twisted.plugin import IPlugin
from mimic.catalog import Endpoint, Entry
from mimic.imimic import IAPIMock
from mimic.rest.mimicapp import MimicApp


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
        lb_region = CloudFeedsRegion(self, uri_prefix, session_store, region)
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


class CloudFeedsRegion(object):
    """
    Klein routes for cloud feeds API methods within a particular region.
    """

    app = MimicApp()

    def __init__(self, api_mock, uri_prefix, session_store, region_name):
        """
        Fetches the cloud feeds id for a failure, invalid scenarios, etc.
        """
        self.uri_prefix = uri_prefix
        self.region_name = region_name
        self._api_mock = api_mock
        self._session_store = session_store
