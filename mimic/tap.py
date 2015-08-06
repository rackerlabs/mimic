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
    optParameters = [['listen', 'l', '8900', 'The endpoint to listen on.']]
    optFlags = [['realtime', 'r',
                 'Make mimic advance time as real time advances; '
                 'disable the "tick" endpoint.'],
                ['verbose', 'v',
                 'Log more verbosely: include full requests and responses.']]


def makeService(config):
    """
    Set up the otter-api service.
    """
    s = MultiService()
    if config['realtime']:
        from twisted.internet import reactor as clock
    else:
        clock = Clock()
    core = MimicCore.fromPlugins(clock)
    root = MimicRoot(core, clock)
    site = get_site(root.app.resource(), logging=bool(config['verbose']))
    service(config['listen'], site).setServiceParent(s)
    return s
