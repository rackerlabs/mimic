"""
Dummy classes that can be shared across test cases
"""

from zope.interface import implementer

from twisted.plugin import IPlugin
from twisted.web.resource import Resource

from mimic.catalog import Entry
from mimic.catalog import Endpoint
from mimic.imimic import IAPIMock


class ExampleResource(Resource):
    """
    Simple resource that returns a string as the response
    """
    isLeaf = True

    def __init__(self, response_message):
        """
        Has a response message to return when rendered
        """
        self.response_message = response_message

    def render_GET(self, request):
        """
        Render whatever message was passed in
        """
        return self.response_message


@implementer(IAPIMock, IPlugin)
class ExampleAPI(object):
    """
    Example API that returns NoResource
    """
    def __init__(self, response_message="default message", regions_and_versions=[('ORD', 'v1')]):
        """
        Has a dictionary to store information from calls, for testing
        purposes
        """
        self.store = {}
        self.regions_and_versions = regions_and_versions
        self.response_message = response_message

    def catalog_entries(self, tenant_id):
        """
        List catalog entries for the Nova API.
        """
        endpoints = [Endpoint(tenant_id, each[0], 'uuid', each[1]) for each in self.regions_and_versions]
        return [Entry(tenant_id, "serviceType", "serviceName", endpoints)]

    def resource_for_region(self, region, uri_prefix, session_store):
        """
        Return no resource.
        """
        self.store['uri_prefix'] = uri_prefix
        return ExampleResource(self.response_message)
