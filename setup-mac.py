"""
Setup file for mimic
"""

from setuptools import setup, find_packages
from twisted.plugin import getPlugins, IPlugin
from py2app.build_app import py2app


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
    CFBundleIdentifier          = 'com.yourdn.%s' % ID,
    LSUIElement                 = '1',
    LSMultipleInstancesProhibited = '1',
)

APP_DATA = dict(
    script=SCRIPT,
    plist=PLIST,
    extra_scripts=[TEST_SCRIPT]
)

DATA_FILES = [
    ('', [
        'twisted/plugins/dropin.cache',
        #'mimic/canned_responses/dropin.cache',
        #'mimic/test/dropin.cache',
        # this file is needed for the tests to pass. But, regenerating it
        # is eluding me at the moment.
        'mimic/plugins/dropin.cache'
        #'mimic/rest/dropin.cache',
        #'mimic/util/dropin.cache'
    ]),
]

class BuildWithCache(py2app):
    """
    Before building the application rebuild the `dropin.cache` files.
    """
    def run(self):
        """
        This needs to generate dropin.cache files in several locations.
        """
        list(getPlugins(IPlugin))
        py2app.run(self)


setup(
    name='mimic',
    version='1.3.0',
    description='An API-compatible mock service',
    app=[APP_DATA],
    data_files=DATA_FILES,
    cmdclass={
        'py2app': BuildWithCache
    },
    options={
        'py2app': {
            'includes': ['syslog', 'mimic.test.*', 'twisted.plugin'],
        }
    }
)
