"""
MAAS Mock API
"""

import json
from uuid import uuid4

from six import text_type

from zope.interface import implementer

from twisted.web.server import Request
from twisted.plugin import IPlugin

from mimic.catalog import Entry
from mimic.catalog import Endpoint
from mimic.rest.mimicapp import MimicApp
from mimic.imimic import IAPIMock


Request.defaultContentType = 'application/json'


@implementer(IAPIMock, IPlugin)
class MaasApi(object):
    """
    Rest endpoints for mocked MAAS Api.
    """

    def catalog_entries(self, tenant_id):
        """
        List catalog entries for the Nova API.
        """
        return [
            Entry(
                tenant_id, "rax:monitor", "cloudMonitoring",
                [
                    Endpoint(tenant_id, "ORD", text_type(uuid4()), "v1.0")
                ]
            )
        ]

    def resource_for_region(self, uri_prefix):
        """
        Get an :obj:`twisted.web.iweb.IResource` for the given URI prefix;
        implement :obj:`IAPIMock`.
        """
        return MaasMock(uri_prefix).app.resource()


class MaasMock(object):
    """
    Klein routes for the Monitoring API.
    """

    def __init__(self, uri_prefix):
        """
        Create a maas region with a given URI prefix (used for generating URIs
        to servers).
        """
        self.uri_prefix = uri_prefix

    app = MimicApp()

    @app.route('/v1.0/<string:tenant_id>/entities', methods=['GET'])
    def list_entities(self, request, tenant_id):
        """
        Returns a list of entities with Response code 200.
        """
        request.setResponseCode(200)
        return json.dumps({"entities": []})
