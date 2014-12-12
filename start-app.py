"""
start_app.py starts the application for py2app.

This calls twistd with default arguments.
"""
from twisted.internet._threadedselect import install
reactor = install()

# import classes required to start application
from Cocoa import *
from Foundation import NSObject

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
    """
    Start the application, setup logging, and run the reactor.
    """
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

    # there is no real window to show, just the menu.
    app = NSApplication.sharedApplication()
    NSApp.activateIgnoringOtherApps_(True)

    from PyObjCTools import AppHelper
    AppHelper.runEventLoop()


if __name__ == '__main__':
    startMimic()
