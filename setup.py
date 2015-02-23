"""
Setup file for mimic
"""

from setuptools import setup, find_packages

try:
    from py2app.build_app import py2app
    py2app_available = True
except ImportError:
    py2app_available = False


_NAME = "mimic"
_VERSION = "1.3.0"


def setup_options(name, version):
    """
    If `py2app` is present in path, then enable to option to build the app.

    This also disables the options needed for normal `sdist` installs.

    :returns: a dictionary of setup options.
    """
    if not py2app_available:
        return dict(
            install_requires=[
                "characteristic==14.2.0",
                "klein==0.2.1",
                "twisted>=13.2.0",
                "jsonschema==2.0",
                "treq",
                "six"
            ],
            package_dir={"mimic": "mimic"},
            packages=find_packages(exclude=[]) + ["twisted.plugins"],
        )

    from twisted.plugin import getPlugins, IPlugin
    from mimic import plugins

    # py2app available, proceed.
    script="bundle/start-app.py"
    test_script="bundle/run-tests.py"
    plist = dict(
        CFBundleName                = _NAME,
        CFBundleShortVersionString  = " ".join([_NAME, _VERSION]),
        CFBundleGetInfoString       = _NAME,
        CFBundleExecutable          = _NAME,
        CFBundleIdentifier          = "com.%s.%s" % (_NAME, _VERSION),
        LSUIElement                 = "1",
        LSMultipleInstancesProhibited = "1",
    )
    app_data = dict(
        script=script,
        plist=plist,
        extra_scripts=[test_script]
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
        app=[app_data],
        cmdclass={
            "py2app": BuildWithCache
        },
        options={
            "py2app": {
                "includes": ["syslog", "mimic.test.*", "twisted.plugin"],
            }
        }
    )

setup(
    name=_NAME,
    version=_VERSION,
    description="An API-compatible mock service",
    license="Apache License, Version 2.0",
    include_package_data=True,
    **setup_options(_NAME, _VERSION)
)
