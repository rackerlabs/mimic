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
        self.assertEqual(2, len(core._uuid_to_api))
        self.assertEqual(0, len(core._uuid_to_api['internal']))
        self.assertEqual(0, len(core._uuid_to_api['external']))
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
        # all plugsin should be on the internal listing
        self.assertEqual(
            plugin_apis,
            set(core._uuid_to_api['internal'].values()))
        # the external listing should still be empty
        self.assertEqual(
            set([]),
            set(core._uuid_to_api['external'].values()))
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
        self.root = FilePath(self.mktemp())
        self.root.createDirectory()
        plugin = b"""from mimic.test.dummy import ExampleDomainAPI
dummy_domain_plugin = ExampleDomainAPI()
"""
        self.root.child('fake_plugin.py').setContent(plugin)

        import mimic.plugins
        mimic.plugins.__path__.append(self.root.path)
        from mimic.plugins import fake_plugin

        def cleanup():
            sys.modules.pop("mimic.plugins.fake_plugin")
            del mimic.plugins.fake_plugin
        self.addCleanup(cleanup)

        core = MimicCore.fromPlugins(Clock())
        self.assertIn(
            fake_plugin.dummy_domain_plugin,
            core.domains
        )
