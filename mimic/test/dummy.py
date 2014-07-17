"""
Dummy classes that can be shared across test cases
"""

from zope.interface import implementer

from twisted.plugin import IPlugin
from twisted.web.resource import NoResource

from mimic.catalog import Entry
from mimic.catalog import Endpoint
from mimic.imimic import IAPIMock


@implementer(IAPIMock, IPlugin)
class ExampleAPI(object):
    """
    Example API that returns NoResource
    """
    def __init__(self):
        """
        Has a dictionary to store information from calls, for testing
        purposes
        """
        self.store = {}

    def catalog_entries(self, tenant_id):
        """
        List catalog entries for the Nova API.
        """
        return [Entry(tenant_id, "serviceType", "serviceName",
                      [Endpoint(tenant_id, "ORD", 'uuid')])]

    def resource_for_region(self, uri_prefix):
        """
        Return no resource.
        """
        self.store['uri_prefix'] = uri_prefix
        return NoResource()
