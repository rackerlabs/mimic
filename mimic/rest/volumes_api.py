"""
Defines list of volumes
"""

from uuid import uuid4
import json
from six import text_type
from zope.interface import implementer
from twisted.web.server import Request
from twisted.plugin import IPlugin
from mimic.canned_responses.volumes import get_volumes
from mimic.rest.mimicapp import MimicApp
from mimic.catalog import Entry
from mimic.catalog import Endpoint
from mimic.imimic import IAPIMock

Request.defaultContentType = 'application/json'


@implementer(IAPIMock, IPlugin)
class VolumesApi(object):
    """
    Rest endpoints for mocked Volumes Api.
    """
    def __init__(self, regions=["ORD", "DFW", "IAD"]):
        """
        Create a VolumesApi.
        """
        self._regions = regions

    def catalog_entries(self, tenant_id):
        """
        List catalog entries for the Volumes API.
        """
        return [
            Entry(
                tenant_id, "volume", "cloudBlockStorage",
                [
                    Endpoint(tenant_id, region, text_type(uuid4()),
                             prefix="v2")
                    for region in self._regions
                ]
            )
        ]

    def resource_for_region(self, region, uri_prefix, session_store):
        """
        Get an :obj:`twisted.web.iweb.IResource` for the given URI prefix;
        implement :obj:`IAPIMock`.
        """
        return VolumesMock(self, uri_prefix, session_store, region).app.resource()


class VolumesMock(object):
    """
    Volumes mock
    """
    def __init__(self, api_mock, uri_prefix, session_store, name):
        """
        Create a volumes region with a given URI prefix
        """
        self.uri_prefix = uri_prefix
        self._api_mock = api_mock
        self._session_store = session_store
        self._name = name

    app = MimicApp()

    @app.route('/v2/<string:tenant_id>/volumes', methods=['GET'])
    def get_volumes(self, request, tenant_id):
        """
        Returns a list of block storage volumes
        """
        request.setResponseCode(200)
        return json.dumps(get_volumes())