# -*- test-case-name: mimic.test.test_dns -*-
"""
Defines get for reverse dns
"""

import json
from uuid import uuid4
from six import text_type
from zope.interface import implementer
from twisted.web.server import Request
from twisted.plugin import IPlugin
from mimic.rest.mimicapp import MimicApp
from mimic.catalog import Entry
from mimic.catalog import Endpoint
from mimic.imimic import IAPIMock

Request.defaultContentType = 'application/json'


@implementer(IAPIMock, IPlugin)
class DNSApi(object):

    """
    Rest endpoints for mocked DNS Api.
    """

    def __init__(self, regions=["ORD", "DFW", "IAD"]):
        """
        Create a DNSApi.
        """
        self._regions = regions

    def catalog_entries(self, tenant_id):
        """
        List catalog entries for the DNS API.
        """
        return [
            Entry(
                tenant_id, "rax:dns", "cloudDNS",
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
        return DNSMock(self, uri_prefix, session_store, region).app.resource()


class DNSMock(object):
    """
    DNS Mock
    """
    def __init__(self, api_mock, uri_prefix, session_store, name):
        """
        Create a DNS region with a given URI prefix
        """
        self.uri_prefix = uri_prefix
        self._api_mock = api_mock
        self._session_store = session_store
        self._name = name

    app = MimicApp()

    @app.route('/v2/<string:tenant_id>/rdns/cloudServersOpenStack', methods=['GET'])
    def get_dns(self, request, tenant_id):
        """
        Reverse DNS call. Response code and response body hardcoded so servers details page in
        cloud control panel will display the "Reverse DNS" field on the page.
        """
        request.setResponseCode(404)
        return json.dumps({})
