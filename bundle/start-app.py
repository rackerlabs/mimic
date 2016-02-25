"""
start_app.py starts mimic for py2app.
"""

from twisted.internet.cfreactor import install
from PyObjCTools import AppHelper

reactor = install(runner=AppHelper.runEventLoop)

from AppKit import NSVariableStatusItemLength
from Foundation import (
    NSObject,
    NSApplication,
    NSStatusBar,
    NSMenu,
    NSMenuItem,
    TRUE
)

from mimic.core import MimicCore
from mimic.resource import MimicRoot

from twisted.internet.endpoints import serverFromString
from twisted.internet.task import Clock
from twisted.web.server import Site
from twisted.python import log

# The following are required by pkg_resources.resource_string, which is used by
# treq; so trick modulegraph into including it.
from pkg_resources._vendor.packaging import version, specifiers, requirements
version, specifiers, requirements # pacify pyflakes

from sys import stdout

# This is the port on which mimic will listen for requests. It has been
# declared here to make it usable in the status bar and by startMimic.
_PORT = "8900"


class MimicAppDelegate(NSObject):
    """
    Setup a small user interface that allows the user to shutdown the
    application and see which port mimic is listening on.
    """
    def applicationDidFinishLaunching_(self, aNotification):
        """
        Create a toolbar and menu for the mac application that can be used
        to close shut down the application.
        """
        self.statusItem = NSStatusBar\
            .systemStatusBar()\
            .statusItemWithLength_(NSVariableStatusItemLength)

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

        # add the menu to status bar item
        self.statusItem.setMenu_(self.menubarMenu)
        self.statusItem.setToolTip_(u"mimic - rackspace mock api")

        AppHelper.callLater(1, startMimic)
        # XXX I"m continuing to get an exception here
        # <type "exceptions.AttributeError">: "CFReactor"
        # object has no attribute "interleave"
        # it seems like using interleave is necessary
        # but, it could be I"m misunderstanding the API.
        # reactor.interleave(AppHelper.callAfter)

    def applicationShouldTerminate_(self, sender):
        """
        Stop twisted's reactor when the application is shutdown.
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
    Setup the mimic application using steps similar to
    :obj:`mimic.tap.makeService' and start listening for requests.
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
    delegate = MimicAppDelegate.alloc().init()
    application.setDelegate_(delegate)

    AppHelper.runEventLoop()
