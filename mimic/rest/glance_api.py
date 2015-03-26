# -*- test-case-name: mimic.test.test_glance -*-
"""
Defines a list of images from glance
"""

import json
from uuid import uuid4
from six import text_type
from zope.interface import implementer
from twisted.web.server import Request
from twisted.plugin import IPlugin
from mimic.canned_responses.glance import get_images
from mimic.rest.mimicapp import MimicApp
from mimic.catalog import Entry
from mimic.catalog import Endpoint
from mimic.imimic import IAPIMock

Request.defaultContentType = 'application/json'


@implementer(IAPIMock, IPlugin)
class GlanceApi(object):
    """
    Rest endpoints for mocked Glance Api.
    """
    def __init__(self, regions=["ORD", "DFW", "IAD"]):
        """
        Create a GlanceApi.
        """
        self._regions = regions

    def catalog_entries(self, tenant_id):
        """
        List catalog entries for the Glance API.
        """
        return [
            Entry(
                tenant_id, "image", "cloudImages",
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
        return GlanceMock(self, uri_prefix, session_store, region).app.resource()


class GlanceMock(object):
    """
    Glance Mock
    """
    def __init__(self, api_mock, uri_prefix, session_store, name):
        """
        Create a glance region with a given URI prefix.
        """
        self.uri_prefix = uri_prefix
        self._api_mock = api_mock
        self._session_store = session_store
        self._name = name

    app = MimicApp()

    @app.route('/v2/<string:tenant_id>/images', methods=['GET'])
    def get_images(self, request, tenant_id):
        """
        Returns a list of glance images.  Reach makes two calls, the route with query strings returns
        images that have been shared and but not accepted. For now return empty array.
        """
        if 'member_status' in request.args:
            status = request.args.get('member_status')[0]
            visible = request.args.get('visibility')[0]
            limit = request.args.get('limit')[0]

            if visible == 'shared' and status == 'pending' and limit == '1000':
                request.setResponseCode(200)
                return []
        else:
            request.setResponseCode(200)
            return json.dumps(get_images())
