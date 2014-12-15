"""
Setup file for mimic
"""

from setuptools import setup, find_packages

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

setup(
    name='mimic',
    version='1.3.0',
    description='An API-compatible mock service',
    app=[app_data],
    options={
        'py2app': {
            'includes': ['syslog', 'mimic.test.*'],
            'argv_emulation': True
        }
    }
)
