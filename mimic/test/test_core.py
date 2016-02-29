from __future__ import absolute_import, division, unicode_literals

import sys

from twisted.internet.task import Clock
from twisted.trial.unittest import SynchronousTestCase
from twisted.python.filepath import FilePath

from mimic.core import MimicCore
from mimic.plugins import (nova_plugin, loadbalancer_plugin, swift_plugin,
                           queue_plugin, maas_plugin, rackconnect_v3_plugin,
                           glance_plugin, cloudfeeds_plugin, heat_plugin,
                           neutron_plugin, dns_plugin, cinder_plugin)


class CoreBuildingTests(SynchronousTestCase):
    """
    Tests for creating a :class:`MimicCore` object with plugins
    """
    def test_no_uuids_if_no_plugins(self):
        """
        If there are no plugins provided to :class:`MimicCore`, there are no
        uri prefixes or entries for the tenant.
        """
        core = MimicCore(Clock(), [])
        self.assertEqual(0, len(core._uuid_to_api))
        self.assertEqual([], list(core.entries_for_tenant('any_tenant', {},
                                                          'http://mimic')))

    def test_from_plugin_includes_all_plugins(self):
        """
        Using the :func:`MimicRoot.fromPlugin` creator for a
        :class:`MimicCore`, the nova and loadbalancer plugins are included.
        """
        core = MimicCore.fromPlugins(Clock())
        plugin_apis = set((
            glance_plugin.glance,
            heat_plugin.heat,
            loadbalancer_plugin.loadbalancer,
            loadbalancer_plugin.loadbalancer_control,
            maas_plugin.maas,
            maas_plugin.maas_control,
            nova_plugin.nova,
            nova_plugin.nova_control_api,
            queue_plugin.queue,
            rackconnect_v3_plugin.rackconnect,
            swift_plugin.swift,
            cloudfeeds_plugin.cloudfeeds,
            cloudfeeds_plugin.cloudfeeds_control,
            neutron_plugin.neutron,
            dns_plugin.dns,
            cinder_plugin.cinder
        ))
        self.assertEqual(
            plugin_apis,
            set(core._uuid_to_api.values()))
        self.assertEqual(
            len(plugin_apis),
            len(list(core.entries_for_tenant('any_tenant', {},
                                             'http://mimic'))))

    def test_load_domain_plugin_includes_all_domain_plugins(self):
        """
        Using the :func:`MimicRoot.fromPlugin` creator for a
        :class:`MimicCore`, domain mocks implementing `class`:`IAPIDomainMock`
        are included.
        """
        # build a fake plugins package with a domain plugin
        self.root = FilePath(self.mktemp())
        self.root.createDirectory()
        self.package = self.root.child('fakeplugins')
        self.package.createDirectory()
        init = b"""from fakeplugins._domain import domain_plugin
__all__ = [domain_plugin]
"""
        self.package.child('__init__.py').setContent(init)
        plugin = b"""from mimic.test.dummy import ExampleDomainAPI
domain_plugin = ExampleDomainAPI()
__all__ = [domain_plugin]
"""
        self.package.child('_domain.py').setContent(plugin)
        sys.path.append(self.root.path)

        # monkey patch mimic.plugins package with fakeplugins
        import fakeplugins
        import mimic.plugins
        mimic.plugins = fakeplugins

        core = MimicCore.fromPlugins(Clock())
        self.assertIdentical(
            fakeplugins.domain_plugin,
            core.domains[0]
        )
        self.assertEqual(
            1,
            len(list(core.domains))
        )
