from twisted.application.strports import service
from twisted.application.service import MultiService
from twisted.web.server import Site
from mimic.rest import auth_api, nova_api, loadbalancer_api, mimic_api
from twisted.python import usage
from mimic.util.mimic_options import OPTION_VALUES


class Options(usage.Options):
    """
    Set the options
    """
    optParameters = [
        ["port", "p", "8900",
         "port for Mimic API connection. Note the mocked services use "
         " increments of the given port in the order: Identity, Nova, LB"],
        ["ip_address", "i", "localhost",
         "Ip address on which the service is running."]
    ]


def makeService(config):
    """
    Set up the mimic-api service.
    """
    s = MultiService()
    options = dict(config)
    port_offset = int(options['port'])
    OPTION_VALUES['port'] = int(options['port'])
    OPTION_VALUES['ip_address'] = options['ip_address']

    for klein_obj in (mimic_api.MimicPresetApi(), auth_api.AuthApi(),
                      nova_api.NovaApi(), loadbalancer_api.LoadBalancerApi()):
        site = Site(klein_obj.app.resource())
        api_service = service(str(port_offset), site)
        api_service.setServiceParent(s)
        site.displayTracebacks = False
        port_offset += 1
    return s
