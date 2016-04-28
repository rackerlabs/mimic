# -*- test-case-name: mimic.test.test_dns -*-
"""
Defines get for reverse dns
"""

import json
from uuid import uuid4
from six import text_type
from zope.interface import implementer
from twisted.plugin import IPlugin
from mimic.rest.mimicapp import MimicApp
from mimic.catalog import Entry
from mimic.catalog import Endpoint
from mimic.imimic import IAPIMock


@implementer(IAPIMock, IPlugin)
class DNSApi(object):
    """
    Rest endpoints for mocked DNS Api.
    """
    def __init__(self, regions=[""]):
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
                    Endpoint(tenant_id, region, text_type(uuid4()), prefix="v1.0")
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

    @app.route('/v1.0/<string:tenant_id>/rdns/cloudServersOpenStack', methods=['GET'])
    def get_PTR_records(self, request, tenant_id):
        """
        Lists all PTR records configured for a specified Cloud device
        """
        request.setResponseCode(404)
        return json.dumps({'message': 'Not Found',
                           'code': 404,
                           'details': 'No PTR records found'})
