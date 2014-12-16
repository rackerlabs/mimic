"""
start_app.py starts mimic for py2app.
"""
from twisted.internet.cfreactor import install
from PyObjCTools import AppHelper

reactor = install(runner=AppHelper.runEventLoop)

import objc

from Foundation import *
from AppKit import *

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


class MyAppDelegate(NSObject):
    """
    Things that need to happen at startup and shutdown for the application
    to work.
    """
    def applicationDidFinishLaunching_(self, aNotification):
        """
        Invoked by NSApplication once the app is done launching and
        immediately before the first pass through the main event
        loop.
        """
        AppHelper.callLater(1, startMimic, (reactor,))
        reactor.interleave(AppHelper.callAfter)

    def applicationShouldTerminate_(self, sender):
        """
        Kill the reactor to close cleanly.
        """
        if reactor.running:
            reactor.addSystemEventTrigger(
                'after', 'shutdown', AppHelper.stopEventLoop)
            reactor.stop()
            return False
        return True


def startMimic(reactor):
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


if __name__ == '__main__':
    log.startLogging(stdout)
    application = NSApplication.sharedApplication()

    delegate = MyAppDelegate.alloc().init()
    application.setDelegate_(delegate)

    AppHelper.runEventLoop()

# took requests at 7:03 but then started failing
# at this point it also complained of CFReactor object not being able
# to 'interleave'
