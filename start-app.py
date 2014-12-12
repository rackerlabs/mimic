"""
start_app.py starts the application for py2app.

This calls twistd with default arguments.
"""
from PyObjCTools import AppHelper

# import classes required to start application
import WSTApplicationDelegateClass
import WSTConnectionWindowControllerClass

from mimic.core import MimicCore
from mimic.resource import MimicRoot
from twisted.internet.endpoints import (
    serverFromString,
    TCP4ServerEndpoint
)
#from twisted.internet import reactor

from twisted.internet.task import Clock
from twisted.web.server import Site

from twisted.python import log

from sys import stdout


def startMimic():
    """
    Start the application, setup logging, and run the reactor.
    """
    from twisted.internet._threadedselect import install
    reactor = install()

    log.startLogging(stdout)

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

    # pass control to the AppKit
    AppHelper.runEventLoop()


if __name__ == '__main__':
    startMimic()
