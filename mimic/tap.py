"""
Twisted Application plugin for Mimic
"""

from __future__ import absolute_import, division, unicode_literals

from twisted.application.strports import service
from twisted.application.service import MultiService
from twisted.python import usage
from mimic.core import MimicCore
from mimic.resource import MimicRoot, get_site
from twisted.internet.task import Clock
from twisted.application.service import Service


class Options(usage.Options):
    """
    Options for Mimic
    """
    optParameters = [['listen', 'l', '8900', 'The endpoint to listen on.'],
                     ['file_location', 'f', 'test_shelf.db',
                      'Location of the file which is used by shelve for saving.']]
    optFlags = [['realtime', 'r',
                 'Make mimic advance time as real time advances; '
                 'disable the "tick" endpoint.'],
                ['verbose', 'v',
                 'Log more verbosely: include full requests and responses.']]


class SavedSessionService(Service):

    def __init__(self, core):
        self.core = core

    def startService(self):
        self.core.sessions.load()

    def stopService(self):
        self.core.sessions.save()


def makeService(config):
    """
    Set up the otter-api service.
    """
    s = MultiService()
    if config['realtime']:
        from twisted.internet import reactor as clock
    else:
        clock = Clock()
    from mimic.session import ShelvedSessionStore
    if config['file_location']:
        sessions = ShelvedSessionStore(clock, config['file_location'])
    core = MimicCore.fromPlugins(clock, sessions)
    if config['file_location']:
        saved_session_service = SavedSessionService(core)
        saved_session_service.setServiceParent(s)
    root = MimicRoot(core, clock)
    site = get_site(root.app.resource(), logging=bool(config['verbose']))
    service(config['listen'], site).setServiceParent(s)
    return s
