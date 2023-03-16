"""
Twisted Application plugin for Mimic
"""



from twisted.application.strports import service
from twisted.application.service import MultiService
from twisted.python import usage
from mimic.core import MimicCore
from mimic.resource import MimicRoot, get_site
from twisted.internet.task import Clock


class Options(usage.Options):
    """
    Options for Mimic
    """
    optParameters = [['listen', 'l', 'tcp:8900', 'The endpoint to listen on.']]
    optFlags = [['realtime', 'r',
                 'Make mimic advance time as real time advances; '
                 'disable the "tick" endpoint.'],
                ['verbose', 'v',
                 'Log more verbosely: include full requests and responses.']]


def makeService(config):
    """
    Set up the service.
    """
    s = MultiService()
    if config['realtime']:
        from twisted.internet import reactor as clock
    else:
        clock = Clock()
    core = MimicCore.fromPlugins(clock)
    root = MimicRoot(core, clock)
    site = get_site(root.app.resource(), logging=bool(config['verbose']))

    # The Twisted code currently (v16.6.0, 17.1.0) compares the type of
    # this argument to 'str' in order to determine how to handle it.
    description = str(config['listen'])
    service(description, site).setServiceParent(s)

    return s
