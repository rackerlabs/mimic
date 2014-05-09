"""
Twisted Application plugin for Mimic
"""
from twisted.application.strports import service
from twisted.application.service import MultiService
from twisted.web.server import Site
from mimic.rest import auth_api, nova_api, loadbalancer_api, mimic_api
from twisted.python import usage


class Options(usage.Options):
    """
    Options for Mimic
    """
    pass


def makeService(config):
    """
    Set up the otter-api service.
    """
    s = MultiService()
    port_offset = 8900
    for klein_obj in (mimic_api.MimicPresetApi(), auth_api.AuthApi(),
                      nova_api.NovaApi(), loadbalancer_api.LoadBalancerApi()):
        site = Site(klein_obj.app.resource())
        api_service = service(str(port_offset), site)
        api_service.setServiceParent(s)
        site.displayTracebacks = False
        port_offset += 1
    return s
