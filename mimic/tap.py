from twisted.application.strports import service
from twisted.application.service import MultiService
from twisted.web.server import Site
from mimic.rest import auth_api, nova_api, loadbalancer_api, mimic_api
from twisted.python import usage


class Options(usage.Options):
    pass


def makeService(config):
    """
    Set up the otter-api service.
    """
    s = MultiService()
    # Mimic preset service
    mimic_preset_service = mimic_api.MimicPresetApi()
    site = Site(mimic_preset_service.app.resource())
    api_service = service(str(8900), site)
    api_service.setServiceParent(s)
    site.displayTracebacks = False
    # Mimic Auth service
    auth_service = auth_api.AuthApi()
    site = Site(auth_service.app.resource())
    api_service = service(str(8901), site)
    api_service.setServiceParent(s)
    site.displayTracebacks = False
    # Mimic Nova service
    nova_service = nova_api.NovaApi()
    site = Site(nova_service.app.resource())
    api_service = service(str(8902), site)
    api_service.setServiceParent(s)
    site.displayTracebacks = False
    # Mimic Load balancer service
    loadbalancer_service = loadbalancer_api.LoadBalancerApi()
    site = Site(loadbalancer_service.app.resource())
    api_service = service(str(8903), site)
    api_service.setServiceParent(s)
    site.displayTracebacks = False
    return s
