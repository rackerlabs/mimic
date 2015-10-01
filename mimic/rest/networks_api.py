# -*- test-case-name: mimic.test.test_glance -*-
"""
junk
"""

from uuid import uuid4
from json import dumps
from six import text_type
from zope.interface import implementer
from twisted.web.server import Request
from twisted.plugin import IPlugin
from mimic.model.glance_objects import GlanceImage
from mimic.rest.mimicapp import MimicApp
from mimic.catalog import Entry
from mimic.catalog import Endpoint
from mimic.imimic import IAPIMock


Request.defaultContentType = 'application/json'


@implementer(IAPIMock, IPlugin)
class NetworksApi(object):
    """
    Rest endpoints for mocked Glance Api.
    """
    def __init__(self, regions=["ORD", "DFW", "IAD"]):
        """
        Create a NetworksApi.
        """
        self._regions = regions

    def catalog_entries(self, tenant_id):
        """
        List catalog entries for the Networks API.
        """
        return [
            Entry(
                tenant_id, "network", "cloudNetworks",
                [
                    Endpoint(tenant_id, region, text_type(uuid4()), prefix="v2")
                    for region in self._regions
                ]
            )
        ]

    def resource_for_region(self, region, uri_prefix, session_store):
        """
        Get an :obj:`twisted.web.iweb.IResource` for the given URI prefix;
        implement :obj:`IAPIMock`.
        """
        return NetworksMock(self, uri_prefix, session_store, region).app.resource()


class NetworksMock(object):
    """
    Networks Mock
    """
    def __init__(self, api_mock, uri_prefix, session_store, region_name):
        """
        Create a glance region with a given URI prefix.
        """
        self.uri_prefix = uri_prefix
        self._api_mock = api_mock
        self._session_store = session_store
        self._region = region_name

    app = MimicApp()