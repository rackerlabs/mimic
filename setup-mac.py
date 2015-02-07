"""
Setup file for mimic
"""

from setuptools import setup, find_packages
from twisted.plugin import getPlugins, IPlugin
from py2app.build_app import py2app
from mimic import plugins


NAME = 'mimic'
VERSION = '0.1'
ID = 'mimic'
SCRIPT='bundle/start-app.py'
TEST_SCRIPT='bundle/run-tests.py'
PLIST = dict(
    CFBundleName                = NAME,
    CFBundleShortVersionString  = ' '.join([NAME, VERSION]),
    CFBundleGetInfoString       = NAME,
    CFBundleExecutable          = NAME,
    CFBundleIdentifier          = 'com.%s.%s' % (NAME, ID),
    LSUIElement                 = '1',
    LSMultipleInstancesProhibited = '1',
)

APP_DATA = dict(
    script=SCRIPT,
    plist=PLIST,
    extra_scripts=[TEST_SCRIPT]
)


class BuildWithCache(py2app):
    """
    Before building the application rebuild the `dropin.cache` files.
    """

    def run(self):
        """
        This generates `dropin.cache` files for mimic's plugins.
        """
        list(getPlugins(IPlugin, package=plugins))
        py2app.run(self)


setup(
    app=[APP_DATA],
    cmdclass={
        'py2app': BuildWithCache
    },
    options={
        'py2app': {
            'includes': ['syslog', 'mimic.test.*', 'twisted.plugin'],
        }
    }
)
