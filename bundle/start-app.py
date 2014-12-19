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

_PORT="8800"

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
        self.statusItem = NSStatusBar.systemStatusBar().statusItemWithLength_(NSVariableStatusItemLength)
        self.statusItem.setTitle_(u"M")
        self.statusItem.setHighlightMode_(TRUE)
        self.statusItem.setEnabled_(TRUE)

        self.quit = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                                  "Quit", "terminate:", "")
        # ugly but... it provides the information.
        self.port = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Listening on localhost:{0}".format(_PORT), "", "")

        self.menubarMenu = NSMenu.alloc().init()
        self.menubarMenu.addItem_(self.port)
        self.menubarMenu.addItem_(self.quit)

        # XXX add a an item displaying the port

        #add menu to statusitem
        self.statusItem.setMenu_(self.menubarMenu)
        self.statusItem.setToolTip_(u"mimic - rackspace mock api")

        AppHelper.callLater(1, startMimic)
        # XXX I"m continuing to get an exception here
        # <type "exceptions.AttributeError">: "CFReactor"
        # object has no attribute "interleave"
        # it seems like using interleave is necessary
        # but, it could be I"m misunderstanding the API.
        #reactor.interleave(AppHelper.callAfter)

    def applicationShouldTerminate_(self, sender):
        """
        Kill the reactor to close cleanly.
        """
        log.msg("stopping mimic reactor")
        if reactor.running:
            reactor.addSystemEventTrigger(
                "after", "shutdown", AppHelper.stopEventLoop)
            reactor.stop()
            return False
        return True


def startMimic():
    """
    Start the actual mimic application.
    """
    clock = Clock()
    core = MimicCore.fromPlugins(clock)
    root = MimicRoot(core, clock)
    site = Site(root.app.resource())
    site.displayTracebacks = False

    endpoint = serverFromString(
        reactor,
        b"tcp:{0}:interface=127.0.0.1".format(_PORT)
    )
    endpoint.listen(site)


if __name__ == "__main__":
    log.startLogging(stdout)
    application = NSApplication.sharedApplication()
    delegate = MyAppDelegate.alloc().init()
    application.setDelegate_(delegate)

    AppHelper.runEventLoop()
