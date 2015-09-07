# -*- test-case-name: mimic.test.test_glance -*-
"""
Defines a list of images from glance
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
    def __init__(self, api_mock, uri_prefix, session_store, region_name):
        """
        Create a glance region with a given URI prefix.
        """
        self.uri_prefix = uri_prefix
        self._api_mock = api_mock
        self._session_store = session_store
        self._region = region_name

    app = MimicApp()

    @app.route('/v2/<string:tenant_id>/images', methods=['GET'])
    def get_images(self, request, tenant_id):
        """
        Returns a list of glance images.  Reach makes three calls:
        The call with member_status query param is for pending images, for now we just return
            an empty array
        The call with visibility is private, for now we just return and empty array
        """
        if 'member_status' in request.args:
            status = request.args.get('member_status')[0]
            visible = request.args.get('visibility')[0]
            limit = request.args.get('limit')[0]

            if visible == 'shared' and status == 'pending' and limit == '1000':
                return dumps({"images": [], "schema": "/v2/schemas/images",
                              "first": "/v2/images?limit=1000&visibility=shared&member_status=pending"})
            else:
                request.setResponseCode(400)
                return dumps({
                    "badRequest": {
                        "message": "Bad Request.",
                        "code": 400
                    }
                })
        elif 'visibility' in request.args:
            visible = request.args.get('visibility')[0]
            if visible == 'public':
                image = GlanceImage()
                return image.list_images(self._region, include_details=True)
            else:
                return dumps({"images": [], "schema": "/v2/schemas/images",
                              "first": "/v2/images?limit=1000&visibility=private"})
        else:
            image = GlanceImage()
            return image.list_images(self._region, include_details=True)
