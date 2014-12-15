"""
start_app.py starts mimic for py2app.
"""
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


class MyApp(NSApplication):

    def finishLaunching(self):

        # Make statusbar item
        statusbar = NSStatusBar.systemStatusBar()
        self.statusitem = statusbar.statusItemWithLength_(NSVariableStatusItemLength)
        self.icon = NSImage.alloc().initByReferencingFile_('icon.png')
        self.icon.setScalesWhenResized_(True)
        self.icon.setSize_((20, 20))
        self.statusitem.setImage_(self.icon)

        #make the menu
        self.menubarMenu = NSMenu.alloc().init()

        self.menuItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Click Me', 'clicked:', '')
        self.menubarMenu.addItem_(self.menuItem)

        self.quit = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Quit', 'terminate:', '')
        self.menubarMenu.addItem_(self.quit)

        #add menu to statusitem
        self.statusitem.setMenu_(self.menubarMenu)
        self.statusitem.setToolTip_('My App')

    def clicked_(self, notification):
        NSLog('clicked!')


# class MyAppDelegate(NSObject):
#     """
#     Things that need to happen at startup and shutdown for the application
#     to work.
#     """
#     def applicationDidFinishLaunching_(self, aNotification):
#         """
#         Invoked by NSApplication once the app is done launching and
#         immediately before the first pass through the main event
#         loop.
#         """
#         reactor.interleave(AppHelper.callAfter)

#     def applicationShouldTerminate_(self, sender):
#         """
#         Kill the reactor to close cleanly.
#         """
#         if reactor.running:
#             reactor.addSystemEventTrigger(
#                 'after', 'shutdown', AppHelper.stopEventLoop)
#             reactor.stop()
#             return False
#         return True


def startMimic(reactor):
    """

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


if __name__ == '__main__':
    #from twisted.internet.cfreactor import install
    #from PyObjCTools import AppHelper
    #install(runner=AppHelper.runEventLoop)
    from twisted.internet import reactor

    startMimic(reactor)
    reactor.run()
