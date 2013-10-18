from twisted.application.strports import service
from twisted.application.service import MultiService
from twisted.web.server import Site
from mimic.rest.views import Mimic
from twisted.python import usage


class Options(usage.Options):
    pass


def makeService(config):
    """
    Set up the otter-api service.
    """
    s = MultiService()
    m = Mimic()
    site = Site(m.app.resource())
    api_service = service(str(8909), site)
    api_service.setServiceParent(s)
    site.displayTracebacks = False
    return s
