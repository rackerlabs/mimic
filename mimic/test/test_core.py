
from __future__ import unicode_literals

from twisted.internet.task import Clock
from twisted.trial.unittest import SynchronousTestCase

from mimic.core import MimicCore
from mimic.plugins import nova_plugin, loadbalancer_plugin, swift_plugin


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
        plugin_apis = set((nova_plugin.nova, loadbalancer_plugin.loadbalancer,
                           swift_plugin.swift))
        self.assertEqual(
            plugin_apis,
            set(core._uuid_to_api.values()))
        self.assertEqual(
            len(plugin_apis),
            len(list(core.entries_for_tenant('any_tenant', {},
                                             'http://mimic'))))
