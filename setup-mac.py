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

app_data = dict(
    script=SCRIPT,
    plist=PLIST,
    extra_scripts=[TEST_SCRIPT]
)

data_files = [('', ['twisted/plugins/dropin.cache'])]

def makeDropInCache():
    """
    Creates a dropin.cache file for mimic's twisted plugins.

    :returns: None
    """
    list(getPlugins(IPlugin))


class BuildWithCache(py2app):
    """
    Run all of the normal py2app steps, but build the dropin.cache file
    first.
    """
    def run(self):
        makeDropInCache()
        py2app.run(self)


setup(
    name='mimic',
    version='1.3.0',
    description='An API-compatible mock service',
    cmdclass={
        'py2app': BuildWithCache
    },
    data_files=data_files,
    app=[app_data],
    options={
        'py2app': {
            'includes': ['syslog', 'mimic.test.*', 'twisted.plugin'],
            #'argv_emulation': True
        }
    }
)
