"""
Setup file for mimic
"""

from setuptools import setup, find_packages


_NAME = "mimic"
_VERSION = "1.3.0"


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
            package_dir={"mimic": "mimic"},
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

    script="bundle/start-app.py"
    test_script="bundle/run-tests.py"
    plist = dict(
        CFBundleName                = name,
        CFBundleShortVersionString  = " ".join([name, version]),
        CFBundleGetInfoString       = name,
        CFBundleExecutable          = name,
        CFBundleIdentifier          = "com.%s.%s" % (name, version),
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
            This generates `dropin.cache` files for mimic"s plugins.
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
    **setup_options(_NAME, _VERSION)
)
