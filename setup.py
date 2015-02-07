"""
Setup file for mimic
"""

from setuptools import setup, find_packages


_NAME = 'mimic'
_VERSION = '1.3.0'


def setup_options(name, version):
    """
    If py2app is present, then make the application buildable.
    """
    py2app_available = None
    try:
        from py2app.build_app import py2app
        py2app_available = True
    except ImportError:
        py2app_available = False

    if not py2app_available:
        return dict(
            packages=find_packages(exclude=[]) + ["twisted.plugins"],
            package_dir={'mimic': 'mimic'},
            install_requires=[
                "characteristic==14.2.0",
                "klein==0.2.1",
                "twisted>=13.2.0",
                "jsonschema==2.0",
                "treq",
                "six"
            ],
            include_package_data=True
        )

    # proceed with py2app
    from twisted.plugin import getPlugins, IPlugin
    from mimic import plugins

    SCRIPT='bundle/start-app.py'
    TEST_SCRIPT='bundle/run-tests.py'
    PLIST = dict(
        CFBundleName                = name,
        CFBundleShortVersionString  = ' '.join([name, version]),
        CFBundleGetInfoString       = name,
        CFBundleExecutable          = name,
        CFBundleIdentifier          = 'com.%s.%s' % (name, version),
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


    return dict(
        app=[APP_DATA],
        setup_requires=[
            "py2app==0.7.3",
            "pyobjc-core==2.5.1",
            "pyobjc-framework-Cocoa==2.5.1",
            "pyobjc-framework-CFNetwork==2.5.1"
            # what about mock, unittest2 ...
        ],
        cmdclass={
            'py2app': BuildWithCache
        },
        options={
            'py2app': {
                'includes': ['syslog', 'mimic.test.*', 'twisted.plugin'],
            }
        }
    )


setup(
    name=_NAME,
    version=_VERSION,
    description='An API-compatible mock service',
    license="Apache License, Version 2.0",
    **setup_options(_NAME, _VERSION)
)
