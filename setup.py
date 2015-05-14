"""
Setup file for mimic
"""
from __future__ import print_function

from setuptools import setup, find_packages


def modify_import_hook():
    """
    Monkey-patch modulegraph to work around
    https://bitbucket.org/ronaldoussoren/modulegraph/issue/25/
    """
    from modulegraph import modulegraph
    original = modulegraph.ModuleGraph.__dict__["import_hook"]
    def modified_import_hook(self, name, *args, **kw):
        """
        This is the modified version of ModuleGraph.import_hook.
        """
        if 'idnadata' in kw.get("fromlist", []):
            import idna, inspect
            return [self._find_module(name, inspect.getsourcefile(idna.idnadata))]
        return original(self, name, *args, **kw)
    modulegraph.ModuleGraph.import_hook = modified_import_hook

try:
    from py2app.build_app import py2app
    modify_import_hook()
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
    info = dict(
        install_requires=[
            "characteristic>=14.2.0",
            "klein>=0.2.1",
            "twisted>=14.0.2",
            "jsonschema>=2.0",
            "treq>=0.2.1",
            "six>=1.6.0",
            "xmltodict>=0.9.1",
            "attrs>=15.0.0",
            "testtools>=1.7.1,<1.8.0"
        ],
        package_dir={"mimic": "mimic"},
        packages=find_packages(exclude=[]) + ["twisted.plugins"],
    )
    if not py2app_available:
        return info

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

    class BuildWithCache(py2app, object):
        """
        Before building the application rebuild the `dropin.cache` files.
        """

        def collect_recipedict(self):
            """
            Implement a special Twisted plugins recipe so that dropin.cache
            files are generated and included in site-packages.zip.
            """
            result = super(BuildWithCache, self).collect_recipedict()
            def check(cmd, mg):
                from twisted.plugin import getPlugins, IPlugin
                from twisted import plugins as twisted_plugins
                from mimic import plugins as mimic_plugins

                for plugin_package in [twisted_plugins, mimic_plugins]:
                    import time
                    list(getPlugins(IPlugin, package=plugin_package))

                import os
                def plugpath(what):
                    path_in_zip = what + "/plugins"
                    path_on_fs = (
                        os.path.abspath(
                            os.path.join(
                                os.path.dirname(
                                    __import__(what + ".plugins",
                                               fromlist=["nonempty"])
                                    .__file__),
                                "dropin.cache")
                        ))
                    os.utime(path_on_fs, (time.time() + 86400,) * 2)
                    return (path_in_zip, [path_on_fs])
                data_files = [plugpath("mimic"), plugpath("twisted")]

                return dict(loader_files=data_files)
            result["bonus"] = check
            return result

    return dict(
        info,
        app=[app_data],
        cmdclass={
            "py2app": BuildWithCache
        },
        options={
            "py2app": {
                "includes": [
                    "syslog",
                    "mimic.test.*",
                    "mimic.plugins.*",
                    "twisted.plugins.*",
                    "twisted.plugin",
                ],
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
