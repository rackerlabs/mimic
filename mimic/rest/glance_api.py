# -*- test-case-name: mimic.test.test_glance -*-
"""
Defines a list of images from glance
"""

import json
from uuid import uuid4
from six import text_type
from zope.interface import implementer
from twisted.plugin import IPlugin
from mimic.canned_responses.glance import get_images, get_image_schema
from mimic.rest.mimicapp import MimicApp
from mimic.catalog import Entry
from mimic.catalog import Endpoint
from mimic.imimic import IAPIMock


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
        Returns a list of glance images. Currently there is no provision
        for shared versus unshared images in the response
        """
        request.setResponseCode(200)
        return json.dumps(get_images())


class GlanceAdminApi(object):
    """
    Rest endpoints for mocked Glance Admin API.
    """

    app = MimicApp()

    def __init__(self, core):
        """
        :param MimicCore core: The core to which this Glance Admin API will be
        communicating.
        """
        self.core = core

    @app.route('/v2/images', methods=['POST'])
    def create_image(self, request):
        """
        Creates a new image and returns response code 201.
        """
        return json.dumps(self.core.glance_admin_image_store.create_image(request))

    @app.route('/v2/images', methods=['GET'])
    def get_images_for_admin(self, request):
        """
        Returns a list of glance images.
        """
        return json.dumps(self.core.glance_admin_image_store.list_images())

    @app.route('/v2/images/<string:image_id>', methods=['GET'])
    def get_image_for_admin(self, request, image_id):
        """
        Returns image with given `image_id`.
        """
        return json.dumps(self.core.glance_admin_image_store.get_image(
            request,
            image_id))

    @app.route('/v2/images/<string:image_id>', methods=['DELETE'])
    def delete_image(self, request, image_id):
        """
        Deletes the image and returns response code 204.
        """
        return self.core.glance_admin_image_store.delete_image(
            request,
            image_id)

    @app.route('/v2/schemas/image', methods=['GET'])
    def get_image_schema_for_admin(self, request):
        """
        Returns the glance image schema.
        """
        return json.dumps(get_image_schema())
