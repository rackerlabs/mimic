
from mimic.imimic import IAPIMock
from twisted.plugin import IPlugin
from twisted.web.static import Data
from mimic.catalog import Entry
from mimic.catalog import Endpoint
from zope.interface import implementer

@implementer(IAPIMock, IPlugin)
class DummyPlugin(object):
    def catalog_entries(self, tenant_id):
        if tenant_id is not None:
            modified = "dummy_" + tenant_id
        else:
            modified = None
        return [Entry(modified, "dummy", "Not Real", [
            Endpoint(modified, "Luna", "4321", "v3k"),
            Endpoint(modified, "Mars", "5432", "v3k"),
        ])]

    def resource_for_region(self):
        return Data("Hello, world!", "text/plain")

# dummy = DummyPlugin()
