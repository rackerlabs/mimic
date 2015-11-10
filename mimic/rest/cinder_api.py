# -*- test-case-name: mimic.test.test_cinder -*-
"""
Defines a mock for Cinder
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
class CinderApi(object):
    """
    Rest endpoints for mocked Cinder Api.
    """
    def __init__(self, regions=["DFW", "ORD", "IAD"]):
        """
        Create a CinderApi.
        """
        self._regions = regions

    def catalog_entries(self, tenant_id):
        """
        List catalog entries for the Cinder API.
        """
        return [
            Entry(
                tenant_id, "volume", "cloudBlockStorage",
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
        return CinderMock(self, uri_prefix, session_store, region).app.resource()


class CinderMock(object):
    """
    DNS Mock
    """
    def __init__(self, api_mock, uri_prefix, session_store, name):
        """
        Create a Cinder region with a given URI prefix
        """
        self.uri_prefix = uri_prefix
        self._api_mock = api_mock
        self._session_store = session_store
        self._name = name

    app = MimicApp()

    @app.route('/v2/<string:tenant_id>/volumes', methods=['GET'])
    def get_volumes(self, request, tenant_id):
        """
        Lists summary information for all Block Storage volumes that the tenant can access.
        http://developer.openstack.org/api-ref-blockstorage-v2.html#getVolumesSimple
        """
        request.setResponseCode(200)
        return json.dumps({'volumes': []})
