"""
start_app.py starts the application for py2app.

This calls twistd with default arguments.
"""


from mimic.core import MimicCore
from mimic.resource import MimicRoot
from twisted.internet.endpoints import (
    serverFromString,
    TCP4ServerEndpoint
)
from twisted.internet.task import Clock
from twisted.web.server import Site

from twisted.python import log

from sys import stdout


def startMimic():
    # this will need an explicit logger
    log.startLogging(stdout)

    from twisted.internet import reactor
    # this runs in realtime. I'd think that the mimic user
    # would likely want to run with the internally defined
    # clock.
    clock = Clock()
    core = MimicCore.fromPlugins(clock)
    root = MimicRoot(core, clock)
    site = Site(root.app.resource())
    site.displayTracebacks = False

    endpoint = serverFromString(
        reactor,
        b"tcp:8800:interface=127.0.0.1"
    )
    endpoint.listen(site)
    reactor.run()


if __name__ == '__main__':
    startMimic()
