# -*- test-case-name: mimic.test.test_nova -*-
"""
Defines list of images from glance
"""

from uuid import uuid4
import json

from six import text_type

from zope.interface import implementer

from twisted.web.server import Request

from twisted.python.urlpath import URLPath

from twisted.plugin import IPlugin

from mimic.canned_responses.support import get_support_info
from mimic.rest.mimicapp import MimicApp
from mimic.catalog import Entry
from mimic.catalog import Endpoint
from mimic.imimic import IAPIMock

Request.defaultContentType = 'application/json'


@implementer(IAPIMock, IPlugin)
class SupportApi(object):
    """
    Rest endpoints for mocked Glance Api.
    """

    def __init__(self, regions=[""]):
        """
        Create a GlanceApi.
        """
        self._regions = regions

    def catalog_entries(self, tenant_id):
        """
        List catalog entries for the Customer API.
        """
        return [
            Entry(
                tenant_id, "rax:support", "support",
                [
                    Endpoint(tenant_id, region, text_type(uuid4()),
                             prefix=None)
                    for region in self._regions
                ]
            )
        ]

    def resource_for_region(self, region, uri_prefix, session_store):
        """
        Get an :obj:`twisted.web.iweb.IResource` for the given URI prefix;
        implement :obj:`IAPIMock`.
        """
        return SupportMock(self, uri_prefix, session_store, region).app.resource()


class SupportMock(object):

    """

    """

    def __init__(self, api_mock, uri_prefix, session_store, name):
        """
        Create a nova region with a given URI prefix (used for generating URIs
        to images).
        """
        self.uri_prefix = uri_prefix
        self._api_mock = api_mock
        self._session_store = session_store
        self._name = name

    def url(self, suffix):
        """
        Generate a URL to an object within the Nova URL hierarchy, given the
        part of the URL that comes after.
        """
        return str(URLPath.fromString(self.uri_prefix).child(suffix))

    app = MimicApp()

    @app.route('/support-accounts/<string:tenant_id>', methods=['GET'])
    def get_customer_data(self, request, tenant_id):
        """
        support info
        """
        return json.dumps(get_support_info(tenant_id))


