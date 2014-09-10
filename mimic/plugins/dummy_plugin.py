"""
This module presents a dummy plugin for Mimic.  It doesn't do anything
interesting but it should illustrate how you would write a plugin yourself.
"""

from mimic.imimic import IAPIMock
from twisted.plugin import IPlugin
from twisted.web.static import Data
from mimic.catalog import Entry
from mimic.catalog import Endpoint
from zope.interface import implementer


@implementer(IAPIMock, IPlugin)
class DummyPlugin(object):
    """
    Sample plugin that implements a dummy service.
    """
    def catalog_entries(self, tenant_id):
        """
        Return an Entry object with a couple of sample Endpoints.
        """
        if tenant_id is not None:
            modified = "dummy_" + tenant_id
        else:
            modified = None
        return [Entry(modified, "dummy", "Not Real", [
            Endpoint(modified, "Luna", "4321", "v3k"),
            Endpoint(modified, "Mars", "5432", "v3k"),
        ])]

    def resource_for_region(self, region, uri_prefix):
        """
        Return an IResource provider that just serves static data at its root.
        """
        return Data("Hello, world!", "text/plain")

# Uncomment this line to activate the plugin above.
# dummy = DummyPlugin()
